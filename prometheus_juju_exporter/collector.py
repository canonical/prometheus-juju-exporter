from juju.controller import Controller
from juju.model import Model
from prometheus_client import CollectorRegistry, Gauge

from prometheus_juju_exporter.config import Config
from prometheus_juju_exporter.logging import get_logger


class CollectorDaemon:
    """Core class of the PrometheusJujuExporter collector daemon."""

    def __init__(self, registry=None, debug=False):
        """Create new collector daemon and configure runtime environment."""
        self.config = Config().get_config()
        self.logger = get_logger(debug=debug)
        self.controller = Controller()
        self.model = Model()
        self._registry = registry or CollectorRegistry()
        self.metrics = {}
        self.currently_cached_labels = {}
        self.previously_cached_labels = {}
        self.logger.debug("Collector initialized")
        self.prefixes = [
            "52:54:00",
            "fa:16:3e",
            "06:f1:3a",
            "00:0d:3a",
            "00:50:56",
            "fa:16:3e",
        ]

    def create_new_juju_instances(self):
        """Create new model and controller object to avoid timeout issue."""
        self.controller = Controller()
        self.model = Model()

    def _create_metrics_dict(self, gauge_name, gauge_desc, labels=[], value=0.0):
        """Create a dict of gauge instances."""
        if gauge_name not in self.metrics:
            self.logger.debug("Creating Gauge %s", gauge_name)
            self.metrics[gauge_name] = Gauge(
                gauge_name, gauge_desc, labelnames=labels, registry=self._registry
            )

    async def _connect_controller(self, endpoint, username, password, cacert):
        """Connect to a controller via its endpoint."""
        if not self.controller.is_connected():
            await self.controller.connect(
                endpoint=endpoint, username=username, password=password, cacert=cacert
            )

    async def _get_models(self, endpoint, username, password, cacert):
        """Get a list of all models under a controller."""
        await self._connect_controller(
            endpoint=endpoint, username=username, password=password, cacert=cacert
        )
        model_uuids = await self.controller.model_uuids()
        await self.controller.disconnect()

        return model_uuids

    async def _connect_model(self, uuid, endpoint, username, password, cacert):
        """Connect to a model via its controller's endpoint."""
        if not self.model.is_connected():
            await self.model.connect(
                uuid=uuid,
                endpoint=endpoint,
                username=username,
                password=password,
                cacert=cacert,
            )

    async def _get_machines_in_model(self):
        """Get a list of all machines in the model with their stats."""
        status = await self.model.get_status()

        return status["machines"]

    def _create_gauge_label(self, hostname, model_name, machine_type):
        """Create label dict for gauge."""
        return {
            "job": "prometheus-juju-exporter",
            "hostname": hostname,
            "customer": self.config["customer"]["name"].get(str),
            "cloud_name": self.config["customer"]["cloud_name"].get(str),
            "juju_model": model_name,
            "type": machine_type,
        }

    def _get_gauge_value(self, status):
        """Get numerical value for the running status."""
        if status == "started":
            return 1
        return 0

    def _remove_stale_lables(self, gauge_name):
        stale_labels = {
            k: self.previously_cached_labels[k]
            for k in set(self.previously_cached_labels)
            - set(self.currently_cached_labels)
        }

        for host in stale_labels.keys():
            self.logger.debug(
                f"Deleting timeseries {stale_labels[host]} for removed machine {host}..."
            )
            self.metrics[gauge_name].remove(*list(stale_labels[host].values()))

    async def _get_machine_stats(self, machines, model_name, gauge_name):
        """Get baremetal or vm machines' stats."""
        if machines != {} and len(machines.keys()) > 0:
            for machine_num in machines.keys():
                # check machine type with the prefix of its main mac_address
                interfaces = machines[machine_num]["network-interfaces"].values()
                mac_addresses = [i["mac-address"] for i in interfaces]
                virt_address = list(
                    filter(lambda s: s.startswith(tuple(self.prefixes)), mac_addresses)
                )
                machine_type = "kvm" if len(virt_address) > 0 else "metal"
                labels = self._create_gauge_label(
                    hostname=machines[machine_num]["hostname"],
                    model_name=model_name,
                    machine_type=machine_type,
                )
                value = self._get_gauge_value(
                    status=machines[machine_num]["agent-status"]["status"]
                )
                if labels["hostname"] and labels["hostname"] != "None":
                    self.currently_cached_labels[
                        machines[machine_num]["hostname"]
                    ] = labels.copy()
                    self.logger.debug(
                        "Updating Gauge {}, {}: {}".format(gauge_name, labels, value)
                    )
                    self.metrics[gauge_name].labels(**labels).set(value)

                self._get_container_status(
                    containers=machines[machine_num]["containers"],
                    model_name=model_name,
                    gauge_name=gauge_name,
                )
        else:
            self.logger.debug(f"No machines in model '{model_name}'")

    def _get_container_status(self, containers, model_name, gauge_name):
        """Get lxd containers stats."""
        if containers != {} and len(containers.keys()) > 0:
            for container_num in containers.keys():
                labels = self._create_gauge_label(
                    hostname=containers[container_num]["hostname"],
                    model_name=model_name,
                    machine_type="lxd",
                )
                value = self._get_gauge_value(
                    containers[container_num]["agent-status"]["status"]
                )
                if labels["hostname"] and labels["hostname"] != "None":
                    self.currently_cached_labels[
                        containers[container_num]["hostname"]
                    ] = labels.copy()
                    self.logger.debug(
                        "Updating Gauge {}, {}: {}".format(gauge_name, labels, value)
                    )
                    self.metrics[gauge_name].labels(**labels).set(value)

    async def get_stats(self):
        """Get stats from all machines."""
        gauge_name = "juju_machine_state"
        gauge_desc = "Running status of juju machines"

        self.previously_cached_labels = self.currently_cached_labels.copy()
        self.currently_cached_labels = dict()

        self._create_metrics_dict(
            gauge_name,
            gauge_desc,
            labels=[
                "job",
                "hostname",
                "customer",
                "cloud_name",
                "juju_model",
                "type",
            ],
        )

        self.create_new_juju_instances()

        endpoint = self.config["juju"]["controller_endpoint"].get(str)
        username = self.config["juju"]["username"].get(str)
        password = self.config["juju"]["password"].get(str)
        cacert = self.config["juju"]["controller_cacert"].get(str)
        model_uuids = await self._get_models(
            endpoint=endpoint, username=username, password=password, cacert=cacert
        )
        self.logger.debug(f"List of models in controller: {model_uuids}")

        for model_name in model_uuids.keys():
            self.logger.debug(f"Checking model '{model_name}'...")
            await self._connect_model(
                uuid=model_uuids[model_name],
                endpoint=endpoint,
                username=username,
                password=password,
                cacert=cacert,
            )
            machines = await self._get_machines_in_model()
            await self._get_machine_stats(
                machines=machines, model_name=model_name, gauge_name=gauge_name
            )
            await self.model.disconnect()

        self._remove_stale_lables(gauge_name=gauge_name)
