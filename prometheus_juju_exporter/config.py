"""Configuration loader."""
import sys
from collections import OrderedDict
from logging import getLogger
from typing import Any, Dict, Union

import confuse


class ConfigMeta(type):
    """Singleton metaclass for the Config."""

    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any) -> type:
        if not cls._instance:
            cls._instance = super(ConfigMeta, cls).__new__(cls, *args, **kwargs)
            cls._instance.config = confuse.Configuration(
                "PrometheusJujuExporter", __name__
            )
        return cls._instance


class Config(metaclass=ConfigMeta):
    """Configuration class for PrometheusJujuExporter."""

    config: confuse.Configuration = None

    def __init__(self, args: Union[Dict, None] = None) -> None:
        """Initialize the config class."""
        if not self.config:
            self.config = confuse.Configuration("PrometheusJujuExporter", __name__)

        self.logger = getLogger(__name__)

        if args:
            self.config.set_args(args, dots=True)

        self.validate_config_options()

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
            "detection": OrderedDict(
                [
                    ("virt_macs", confuse.StrSeq()),
                    ("skip_interfaces", confuse.StrSeq()),
                ]
            ),
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
