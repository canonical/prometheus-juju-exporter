import argparse

from prometheus_juju_exporter import logger as project_logger
from prometheus_juju_exporter.exporter import ExporterDaemon


def config_logger(debug=False):
    """Configure global logger's logging level.

    :param bool debug: Whether to set logging level to debug
    """
    project_logger.setLevel("DEBUG" if debug else "INFO")


def main(args=None):
    """Program entry point.

    Parse cli arguments and start exporter daemon.
    """
    cli = argparse.ArgumentParser(
        prog="prometheus-juju-exporter",
        description="PrometheusJujuExporter CLI",
    )

    cli.add_argument(
        "-d", "--debug", dest="debug", action="store_true", help="Print debug log"
    )

    parser, unknown = cli.parse_known_args(args)
    config_logger(debug=parser.debug)

    obj = ExporterDaemon()
    obj.run()


if __name__ == "__main__":  # pragma: no cover
    main()
