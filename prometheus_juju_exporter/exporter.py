"""Exporter module."""
import asyncio
import sys
from logging import getLogger
from typing import Any, Dict, List

from prometheus_client import CollectorRegistry, Gauge, start_http_server

from prometheus_juju_exporter.collector import Collector
from prometheus_juju_exporter.config import Config


class ExporterDaemon:
    """Core class of the exporter daemon."""

    def __init__(self) -> None:
        """Create new daemon and configure runtime environment."""
        self.config = Config().get_config()
        self.logger = getLogger(__name__)
        self.logger.info("Parsed config: %s", self.config.config_dir())
        self._registry = CollectorRegistry()
        self.metrics: Dict[str, Gauge] = {}
        self.collector = Collector()
        self.logger.debug("Exporter initialized")

    def _create_metrics_dict(
        self, gauge_name: str, gauge_desc: str, labels: List[str]
    ) -> None:
        """Create a dict of gauge instances.

        :param str gauge_name: the name of the gauge
        :param str gauge_desc: the description of the gauge
        :param List[str] labels: the label set of the gauge
        """
        if gauge_name not in self.metrics:
            self.logger.debug("Creating Gauge %s", gauge_name)
            self.metrics[gauge_name] = Gauge(
                gauge_name, gauge_desc, labelnames=labels, registry=self._registry
            )

    def update_registry(self, data: Dict[str, Any]) -> None:
        """Update the registry with newly collected values.

        :param dict data: the machine data collected by the Collector method
        """
        for gauge_name, values in data.items():
            self._create_metrics_dict(
                gauge_name=gauge_name,
                gauge_desc=values["gauge_desc"],
                labels=values["labels"],
            )
            for labels, value in values["labelvalues_update"]:
                self.logger.debug(
                    "Updating Gauge %s, %s: %s", gauge_name, labels, value
                )
                self.metrics[gauge_name].labels(**labels).set(value)

            for labels in values["labelvalues_remove"]:
                self.logger.debug(
                    "Deleting labelvalues %s from %s...", labels, gauge_name
                )
                self.metrics[gauge_name].remove(*labels)

    async def trigger(self, **kwargs: Any) -> None:
        """Call Collector and configure prometheus_client gauges from generated stats.

        Available parameters are:

        :param bool once: Whether to continuously collect data. If set
            to true, trigger function will only run once.
        """
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
            except Exception as err:  # pylint: disable=W0703
                self.logger.error("Collection job resulted in error: %s", err)
                sys.exit(1)

            # run collector only once if in test mode
            if kwargs.get("once"):
                run_collector = False

    def run(self, **kwargs: Any) -> None:
        """Run exporter.

        Available parameters are:

        :param bool once: Whether to run exporter daemon continuously. If set
            to true, trigger function will only run once.
        """
        self.logger.debug("Running prometheus client http server.")
        start_http_server(
            self.config["exporter"]["port"].get(int),
            registry=self._registry,
        )

        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(self.trigger(**kwargs))
        loop.run_until_complete(asyncio.wait([task]))
