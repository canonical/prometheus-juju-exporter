import asyncio

from prometheus_client import CollectorRegistry, Gauge, start_http_server

from prometheus_juju_exporter.collector import CollectorDaemon
from prometheus_juju_exporter.config import Config
from prometheus_juju_exporter.logging import get_logger


class ExporterDaemon:
    """Core class of the exporter daemon."""

    def __init__(self, debug=False):
        """Create new daemon and configure runtime environment."""
        self.config = Config().get_config()
        self.logger = get_logger(debug=debug)
        self.logger.info("Parsed config: %s", self.config.config_dir())
        self._registry = CollectorRegistry()
        self.metrics = {}
        self.collector = CollectorDaemon(debug=debug)
        self.logger.debug("Exporter initialized")

    def _create_metrics_dict(self, gauge_name, gauge_desc, labels=[]):
        """Create a dict of gauge instances."""
        if gauge_name not in self.metrics:
            self.logger.debug("Creating Gauge %s", gauge_name)
            self.metrics[gauge_name] = Gauge(
                gauge_name, gauge_desc, labelnames=labels, registry=self._registry
            )

    def update_registry(self, data):
        for gauge_name in data.keys():
            self._create_metrics_dict(
                gauge_name=gauge_name,
                gauge_desc=data[gauge_name]["gauge_desc"],
                labels=data[gauge_name]["labels"],
            )
            for labels in data[gauge_name]["labelvalues_update"]:
                value = labels.pop("value")
                self.logger.debug(
                    "Updating Gauge %s, %s: %s", gauge_name, labels, value
                )
                self.metrics[gauge_name].labels(**labels).set(value)

            for labels in data[gauge_name]["labelvalues_remove"]:
                labels.pop()
                self.logger.debug(
                    "Deleting labelvalues %s from %s...", labels, gauge_name
                )
                self.metrics[gauge_name].remove(*labels)

    async def trigger(self, **kwargs):
        """Configure prometheus_client gauges from generated stats."""
        run_collector = True

        while run_collector:
            try:
                self.logger.info("Collecting gauges...")
                data = await self.collector.get_stats()
                self.update_registry(data)
                self.logger.info("Gauges collected and ready for exporting.")
                await asyncio.sleep(
                    self.config["exporter"]["collect_interval"].get(int) * 60
                )
            except Exception as e:
                self.logger.error("Collection job resulted in error: %s", e)
                exit(1)

            # run collector only once if in test mode
            if kwargs.get("once"):
                run_collector = False

    def run(self, **kwargs):
        """Run exporter."""
        self.logger.debug("Running prometheus client http server.")
        start_http_server(
            self.config["exporter"]["port"].get(int),
            registry=self._registry,
        )

        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(self.trigger(**kwargs))
        loop.run_until_complete(asyncio.wait([task]))
