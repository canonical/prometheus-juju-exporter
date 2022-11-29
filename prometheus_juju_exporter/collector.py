from prometheus_client import CollectorRegistry, Gauge

from prometheus_juju_exporter.config import Config
from prometheus_juju_exporter.logging import get_logger


class CollectorDaemon:
    """Core class of the cloudstats exporter daemon."""

    def __init__(self, registry=None, debug=False):
        """Create new collector daemon and configure runtime environment."""
        self.config = Config().get_config()
        self.logger = self.setup_logging(debug=debug)
        self._registry = registry or CollectorRegistry()
        self.metrics = {}

    def setup_logging(self, debug):
        """Return the correct Logging instance based on debug option."""
        return get_logger(debug=debug)

    def _create_metrics_dict(self, gauge_name, gauge_desc, labels=[], value=0.0):
        """Create a dict of gauge instances."""
        if gauge_name not in self.metrics:
            self.logger.debug("Creating Gauge {}".format(gauge_name))
            self.metrics[gauge_name] = Gauge(
                gauge_name, gauge_desc, labelnames=labels, registry=self._registry
            )

    async def get_stats(self):
        """Get stats from all machines."""
        gauge_name = "juju_machine_state"
        gauge_desc = "Running status of juju machines"

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
