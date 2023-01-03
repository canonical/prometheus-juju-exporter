"""Configuration loader."""
from collections import OrderedDict
from logging import getLogger

import confuse

config = None


class Config:
    """Configuration for PrometheusJujuExporter."""

    def __init__(self, args=None):
        """Initialize the config class."""
        self.logger = getLogger(__name__)

        if args:
            self.config.set_args(args, dots=True)

        self.validate_config_options()

    @property
    def config(self):
        """Return the configuration parsed from the config file."""
        global config

        if config is None:
            config = confuse.Configuration("PrometheusJujuExporter", __name__)

        return config

    def validate_config_options(self):
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
            self.logger.debug("Configuration parsed successfully")
        except (
            KeyError,
            confuse.ConfigTypeError,
            confuse.ConfigValueError,
            confuse.NotFoundError,
        ) as e:
            self.logger.error("Error parsing configuration values: %s", e)
            exit(1)

    def get_config(self, section=None):
        """Return the config."""
        if section:
            return self.config[section]

        return self.config
