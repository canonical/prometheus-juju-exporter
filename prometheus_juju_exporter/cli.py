"""CLI module."""
from prometheus_juju_exporter import logger as project_logger
from prometheus_juju_exporter.config import Config
from prometheus_juju_exporter.exporter import ExporterDaemon


class Cli:
    """Core class of the PrometheusJujuExporter cli."""

    def __init__(self) -> None:
        """Initialize cli instance."""
        self.config = Config().get_config()

    def config_logger(self) -> None:
        """Configure global logger's logging level.

        :param bool debug: Whether to set logging level to debug
        """
        debug = self.config["debug"].get(bool)
        project_logger.setLevel("DEBUG" if debug else "INFO")

    def run_exporter(self) -> None:
        """Start exporter daemon."""
        obj = ExporterDaemon()
        obj.run()


def main() -> None:
    """Program entry point."""
    cli = Cli()
    cli.config_logger()
    cli.run_exporter()


if __name__ == "__main__":  # pragma: no cover
    main()
