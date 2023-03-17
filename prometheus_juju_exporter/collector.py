"""Collector module."""
import re
from enum import Enum
from logging import getLogger
from typing import Any, Dict, List

from juju.controller import Controller

from prometheus_juju_exporter.config import Config


class MachineType(Enum):
    """String type enum for selecting available machine types."""

    METAL = "metal"
    KVM = "kvm"
    LXD = "lxd"


class Collector:
    """Core class of the PrometheusJujuExporter collector."""

    def __init__(self) -> None:
        """Create new collector and configure runtime environment."""
        self.config = Config().get_config()
        self.logger = getLogger(__name__)
        self.controller = Controller(max_frame_size=6**24)
        self.data: Dict[str, Any] = {}
        self.currently_cached_labels: Dict[str, Any] = {}
        self.previously_cached_labels: Dict[str, Any] = {}
        self.virt_mac_prefixes = self.config["detection"]["virt_macs"].as_str_seq()
        self.logger.debug("Collector initialized")

    def refresh_cache(
        self, gauge_name: str, gauge_desc: str, labels: List[str]
    ) -> None:
        """Refresh instances for each collection job.

        :param str gauge_name: the name of the gauge
        :param str gauge_desc: the description of the gauge
        :param List[str] labels: the label set of the gauge
        """
        self.data = {
            gauge_name: {
                "gauge_desc": gauge_desc,
                "labels": labels,
                "labelvalues_update": [],
                "labelvalues_remove": [],
            }
        }

        self.previously_cached_labels = self.currently_cached_labels.copy()
        self.currently_cached_labels = {}

        self.controller = Controller(max_frame_size=6**24)

    async def _connect_controller(
        self, endpoint: str, username: str, password: str, cacert: str
    ) -> None:
        """Connect to a controller via its endpoint.

        :param str endpoint: the hostname:port endpoint of the controller
            to connect to.
        :param str username: the username for controller-local users
        :param str password: the password for controller-local users
        :param str cacert: the CA certificate of the controller
            (PEM formatted)
        """
        if not self.controller.is_connected():
            await self.controller.connect(
                endpoint=endpoint, username=username, password=password, cacert=cacert
            )

    async def _get_machines_in_model(self, uuid: str) -> Dict[Any, Any]:
        """Get a list of all machines in the model with their stats.

        :return: status information for all machines in the model
        """
        try:
            model = await self.controller.get_model(uuid)
            status = await model.get_status()
            await model.disconnect()
        except Exception as err:  # pylint: disable=W0703
            self.logger.error("Failed connecting to model '%s': %s ", uuid, err)
            return {}

        return status["machines"]

    def _create_gauge_label(
        self, hostname: str, model_name: str, machine_type: str
    ) -> Dict[str, str]:
        """Create label dict for gauge.

        :param str hostname: the hostnameof the machine
        :param str model_name: the name of the model the machine is in
        :param str machine_type: the hardware type of the machine
        :return dict labelvalues: the label values in dict format
        """
        return {
            "job": "prometheus-juju-exporter",
            "hostname": hostname,
            "customer": self.config["customer"]["name"].get(str),
            "cloud_name": self.config["customer"]["cloud_name"].get(str),
            "juju_model": model_name,
            "type": machine_type,
        }

    @staticmethod
    def _get_gauge_value(status: str) -> int:
        """Get numerical value for the running status.

        :param str status: the running status of the machine
        :return int status: the integer representation of the running status.
            0 for inactive, 1 for active.
        """
        return int(status == "started")

    def _get_labels_to_remove(self, gauge_name: str) -> None:
        """Get a list of labelvalues for removed machines."""
        stale_labels = {
            k: self.previously_cached_labels[k]
            for k in set(self.previously_cached_labels)
            - set(self.currently_cached_labels)
        }

        for label in stale_labels.values():
            self.data[gauge_name]["labelvalues_remove"].append(list(label[0].values()))

    def _get_machine_type(self, machine: Dict, machine_id: str) -> MachineType:
        """Detect machine type based on its MAC address.

        :param dict machine: status information for a machine
        :return MachineType: MachineType class object indicating the machine type
        """
        self.logger.debug("Determining type of machine: %s", machine_id)
        machine_type = MachineType.METAL
        skip_interfaces = self.config["detection"]["skip_interfaces"].as_str_seq()
        interface_filter = re.compile(r"(?=(" + "|".join(skip_interfaces) + r"))")

        for interface, properties in machine["network-interfaces"].items():
            if skip_interfaces and interface_filter.search(interface) is not None:
                self.logger.debug(
                    "Disregarding interface %s. Matching filter: %s",
                    interface,
                    skip_interfaces,
                )
                continue

            mac_address = properties["mac-address"]
            self.logger.debug(
                "Considering interface %s with MAC: %s", interface, mac_address
            )
            if mac_address.startswith(tuple(self.virt_mac_prefixes)):
                machine_type = MachineType.KVM
                break

        self.logger.debug("Machine %s is of type: %s", machine_id, machine_type)
        return machine_type

    def _get_host_identifier(self, host: Dict) -> str:
        """Try to find a valid identifier for the host.

        The hostname field is only supported for juju controller versions
        2.8.10 and upwards. For the remaining lower versions, this field
        exists however is None or "None". This method tries to get it from
        hostname if it can, else it will try to get it from the "instance-id"
        field, which seems to exist almost always.

        The instance-id with the value "pending" is also treated specially.
        This value is observed when model status data was gathered
        during machine/container creation phase. In this case, an info is
        issued for the operator and this host will be treated as there is no
        valid identifier.

        :param dict machine: status dictionary for a machine or container
        :return str: a valid identifier string for the host if
            applicable, else the string literal "None".
        """
        self.logger.debug("Trying to find an identifier for host: %s", str(host))
        host_id = "None"
        for field in ["hostname", "instance-id"]:
            candidate = host.get(field, None)
            if candidate not in [None, "None"]:
                host_id = candidate
                self.logger.debug(
                    "Candidate host id:[%s] in field:[%s]",
                    host_id,
                    field,
                )
                break

        if host_id == "pending":
            self.logger.info("Found host with pending identifier. Skipping.")
            return "None"

        if host_id == "None":
            self.logger.error("Failed to find identifier for host: %s", str(host))
        else:
            self.logger.debug("Found identifier for host: %s", host_id)
        return host_id

    async def _get_machine_stats(
        self, machines: Dict, model_name: str, gauge_name: str
    ) -> None:
        """Get baremetal or vm machines' stats.

        :param dict machines: status information for all machines in the model
        :param str model_name: the name of the model the machines are in
        :param str gauge_name: the name of the gauge
        """
        for machine in machines.values():
            value = self._get_gauge_value(status=machine["agent-status"]["status"])
            machine_id = self._get_host_identifier(machine)

            if machine_id != "None":
                machine_type = self._get_machine_type(machine, machine_id)
                labels = self._create_gauge_label(
                    hostname=machine_id,
                    model_name=model_name,
                    machine_type=machine_type.value,
                )
                self.currently_cached_labels[machine_id] = (
                    labels.copy(),
                    value,
                )
                self.data[gauge_name]["labelvalues_update"].append((labels, value))

            self._get_container_stats(
                containers=machine["containers"],
                model_name=model_name,
                gauge_name=gauge_name,
            )

    def _get_container_stats(
        self, containers: Dict, model_name: str, gauge_name: str
    ) -> None:
        """Get lxd containers stats.

        :param dict containers: status information for all containers on a machine
        :param str model_name: the name of the model the machines are in
        :param str gauge_name: the name of the gauge
        """
        for container in containers.values():
            value = self._get_gauge_value(container["agent-status"]["status"])
            container_id = self._get_host_identifier(container)

            if container_id != "None":
                labels = self._create_gauge_label(
                    hostname=container_id,
                    model_name=model_name,
                    machine_type=MachineType.LXD.value,
                )
                self.currently_cached_labels[container_id] = (
                    labels.copy(),
                    value,
                )
                self.data[gauge_name]["labelvalues_update"].append((labels, value))

    async def get_stats(self) -> Dict[str, Any]:
        """Get stats from all machines."""
        gauge_name = "juju_machine_state"
        gauge_desc = "Running status of juju machines"
        labels = [
            "job",
            "hostname",
            "customer",
            "cloud_name",
            "juju_model",
            "type",
        ]
        self.refresh_cache(gauge_name=gauge_name, gauge_desc=gauge_desc, labels=labels)

        endpoint = self.config["juju"]["controller_endpoint"].get(str)
        username = self.config["juju"]["username"].get(str)
        password = self.config["juju"]["password"].get(str)
        cacert = self.config["juju"]["controller_cacert"].get(str)

        try:
            await self._connect_controller(
                endpoint=endpoint, username=username, password=password, cacert=cacert
            )
            model_uuids = await self.controller.model_uuids()
            self.logger.debug("List of models in controller: %s", model_uuids)

            for name, uuid_ in model_uuids.items():
                self.logger.debug("Checking model '%s'...", name)
                machines = await self._get_machines_in_model(uuid=uuid_)

                await self._get_machine_stats(
                    machines=machines, model_name=name, gauge_name=gauge_name
                )

            self._get_labels_to_remove(gauge_name=gauge_name)
        finally:
            await self.controller.disconnect()

        return self.data
