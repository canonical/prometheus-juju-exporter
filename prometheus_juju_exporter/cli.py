"""CLI module."""
from prometheus_juju_exporter import logger as project_logger
from prometheus_juju_exporter.config import Config
from prometheus_juju_exporter.exporter import ExporterDaemon


def config_logger(debug: bool = False) -> None:
    """Configure global logger's logging level.

    :param bool debug: Whether to set logging level to debug
    """
    project_logger.setLevel("DEBUG" if debug else "INFO")


def main() -> None:
    """Program entry point."""
    config = Config().get_config()
    config_logger(config["debug"].get(bool))
    obj = ExporterDaemon()
    obj.run()


if __name__ == "__main__":  # pragma: no cover
    main()
