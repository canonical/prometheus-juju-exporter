import argparse
import asyncio
import json
import logging

from prometheus_juju_exporter import logger as project_logger
from prometheus_juju_exporter.collector import Collector
from prometheus_juju_exporter.exporter import ExporterDaemon


def config_logger(debug=False):
    """Configure global logger's logging level.

    :param bool debug: Whether to set logging level to debug
    """
    if debug:
        project_logger.setLevel(logging.DEBUG)
    else:
        project_logger.setLevel(logging.INFO)
        # prevent logs from imported libraries from bubbling up. Specially libjuju
        # can be very verbose
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.ERROR)


def collect(pretty: bool = False) -> None:
    """Run 'collect' subcommand.

    This subcommand collects data from controller and outputs them to the STDOUT in
    the form of a json.

    :param pretty: If True, the output in STDOUT will be indented for easier reading.
    """
    collector = Collector()
    indent = 2 if pretty else None

    result = asyncio.run(collector.get_stats())

    print(json.dumps(result, indent=indent))


def export() -> None:
    """Run 'export' subcommand.

    This subcommand runs the Prometheus exporter and continuously updates its data.
    """
    ExporterDaemon().run()


def parse_cli_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    cli = argparse.ArgumentParser(
        prog="prometheus-juju-exporter",
        description="PrometheusJujuExporter CLI",
    )

    cli.add_argument(
        "-d", "--debug", dest="debug", action="store_true", help="Print debug log"
    )

    subcommands = cli.add_subparsers(
        dest="cmd", title="commands", help="available commands", required=True
    )

    collect_cli = subcommands.add_parser(
        "collect", help="Collect and print metrics from controller."
    )
    collect_cli.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        default=False,
        help="Indent output for easier reading",
        dest="pretty",
    )

    subcommands.add_parser("export", help="Run Prometheus exporter")

    return cli.parse_args()


def main():
    """Program entry point.

    Parse cli arguments and execute selected subcommand.
    """
    args = parse_cli_args()
    config_logger(debug=args.debug)

    if args.cmd == "collect":
        collect(args.pretty)
    elif args.cmd == "export":
        export()
    else:
        print(f"Subcommand '{args.cmd}' not implemented")
        exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
