"""Configuration loader."""
import sys
from collections import OrderedDict
from logging import getLogger
from typing import Dict, Union

import confuse

CONFIG = None


class Config:
    """Configuration for PrometheusJujuExporter."""

    def __init__(self, args: Union[Dict, None] = None) -> None:
        """Initialize the config class."""
        self.logger = getLogger(__name__)

        if args:
            self.config.set_args(args, dots=True)

        self.validate_config_options()

    @property
    def config(self) -> confuse.Configuration:
        """Return the configuration parsed from the config file."""
        global CONFIG  # pylint: disable=W0603

        if CONFIG is None:
            CONFIG = confuse.Configuration("PrometheusJujuExporter", __name__)

        return CONFIG

    def validate_config_options(self) -> None:
        """Validate the configuration values against a template."""
        template = {
            "exporter": OrderedDict(
                [
                    ("port", confuse.Choice(range(0, 65536), default=5000)),
                    ("collect_interval", int),
                ]
            ),
            "juju": OrderedDict(
                [
                    ("controller_endpoint", str),
                    ("controller_cacert", str),
                    ("username", str),
                    ("password", str),
                ]
            ),
            "customer": OrderedDict([("name", str), ("cloud_name", str)]),
        }

        try:
            self.config.get(template)
            self.logger.info("Configuration parsed successfully")
        except (
            KeyError,
            confuse.ConfigTypeError,
            confuse.ConfigValueError,
            confuse.NotFoundError,
        ) as err:
            self.logger.error("Error parsing configuration values: %s", err)
            sys.exit(1)

    def get_config(self, section: Union[Dict, None] = None) -> confuse.Configuration:
        """Return the config."""
        if section:
            return self.config[section]

        return self.config
