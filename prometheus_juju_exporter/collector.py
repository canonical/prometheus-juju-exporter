"""Collector module."""
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
        self.logger.debug("Collector initialized")
        self.prefixes = [
            "52:54:00",
            "fa:16:3e",
            "06:f1:3a",
            "00:0d:3a",
            "00:50:56",
            "fa:16:3e",
        ]

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

    async def _get_models(self) -> Dict[str, str]:
        """Get a list of all models under a controller.

        :return: str model_uuids: the uuids of all models under the controller
        """
        model_uuids = await self.controller.model_uuids()

        return model_uuids

    async def _get_machines_in_model(self, uuid: str) -> Dict[Any, Any]:
        """Get a list of all machines in the model with their stats.

        :return: status information for all machines in the model
        """
        model = await self.controller.get_model(uuid)
        status = await model.get_status()

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

    async def _get_machine_stats(
        self, machines: Dict, model_name: str, gauge_name: str
    ) -> None:
        """Get baremetal or vm machines' stats.

        :param dict machines: status information for all machines in the model
        :param str model_name: the name of the model the machines are in
        :param str gauge_name: the name of the gauge
        """
        for machine in machines.values():
            # check machine type with the prefix of its mac address
            interfaces = machine["network-interfaces"].values()
            machine_type = MachineType.METAL

            for i in interfaces:
                mac_addresses = i["mac-address"]
                if mac_addresses.startswith(tuple(self.prefixes)):
                    machine_type = MachineType.KVM
                    break

            value = self._get_gauge_value(status=machine["agent-status"]["status"])

            labels = self._create_gauge_label(
                hostname=machine["hostname"],
                model_name=model_name,
                machine_type=machine_type.value,
            )

            if labels["hostname"] and labels["hostname"] != "None":
                self.currently_cached_labels[machine["hostname"]] = (
                    labels.copy(),
                    value,
                )

                self.data[gauge_name]["labelvalues_update"].append((labels, value))

            self._get_container_status(
                containers=machine["containers"],
                model_name=model_name,
                gauge_name=gauge_name,
            )

    def _get_container_status(
        self, containers: Dict, model_name: str, gauge_name: str
    ) -> None:
        """Get lxd containers stats.

        :param dict containers: status information for all containers on a machine
        :param str model_name: the name of the model the machines are in
        :param str gauge_name: the name of the gauge
        """
        for container in containers.values():
            value = self._get_gauge_value(container["agent-status"]["status"])

            labels = self._create_gauge_label(
                hostname=container["hostname"],
                model_name=model_name,
                machine_type=MachineType.LXD.value,
            )

            if labels["hostname"] and labels["hostname"] != "None":
                self.currently_cached_labels[container["hostname"]] = (
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
            model_uuids = await self._get_models()
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
