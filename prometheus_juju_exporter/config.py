"""Configuration loader."""
import confuse

config = None


class Config:
    """Configuration for cloudstats."""

    def __init__(self, args=None):
        """Initialize the config class."""
        global config

        if config:
            self.config = config
        else:
            self.config = confuse.Configuration("PrometheusJujuExporter", __name__)
            config = self.config

        if args:
            self.config.set_args(args, dots=True)

    def get_config(self, section=None):
        """Return the config."""
        if section:
            return self.config[section]

        return self.config
