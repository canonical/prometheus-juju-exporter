import asyncio

from prometheus_client import CollectorRegistry, start_http_server

from prometheus_juju_exporter.collector import CollectorDaemon
from prometheus_juju_exporter.config import Config
from prometheus_juju_exporter.logging import get_logger


class ExporterDaemon:
    """Core class of the exporter daemon."""

    def __init__(self, debug=False):
        """Create new daemon and configure runtime environment."""
        self.config = Config().get_config()
        self.logger = self.setup_logging(debug=debug)
        self.logger.info("Parsed config: {}".format(self.config.config_dir()))
        self._registry = CollectorRegistry()
        self.collector = CollectorDaemon(self._registry, debug=debug)
        self.logger.debug("Exporter initialized")

    def setup_logging(self, debug):
        """Return the correct Logging instance based on debug option."""
        return get_logger(debug=debug)

    async def trigger(self, **kwargs):
        """Configure prometheus_client gauges from generated stats."""
        run_collector = True

        while run_collector:
            try:
                self.logger.info("Collecting gauges...")
                await self.collector.get_stats()
                self.logger.info("Gauges collected and ready for exporting.")
                await asyncio.sleep(
                    self.config["exporter"]["collect_interval"].get(int) * 60
                )
            except Exception as e:
                self.logger.info(f"Collection job resulted in error: {e}")
                exit(1)

            # run collector only once if in test mode
            if "test" in kwargs and kwargs["test"] is True:
                run_collector = False

    def run(self, **kwargs):
        """Run exporter."""
        self.logger.debug("Running prometheus client http server.")
        start_http_server(
            self.config["exporter"]["port"].get(), registry=self._registry
        )

        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(self.trigger(**kwargs))
        loop.run_until_complete(asyncio.wait([task]))
