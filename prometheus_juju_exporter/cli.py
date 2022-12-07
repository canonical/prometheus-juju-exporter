import argparse

from prometheus_juju_exporter.exporter import ExporterDaemon


def main(args=None):
    """Program entry point."""
    cli = argparse.ArgumentParser(
        prog="prometheus-juju-exporter",
        description="PrometheusJujuExporter CLI",
    )

    cli.add_argument(
        "-d", "--debug", dest="debug", action="store_true", help="Print debug log"
    )

    parser, unknown = cli.parse_known_args(args)
    obj = ExporterDaemon(debug=parser.debug)
    obj.run()


if __name__ == "__main__":  # pragma: no cover
    main()
