#!/usr/bin/python3
"""Test Config class."""


class TestConfig:
    """Config test class."""

    def test_fixture(self, config_instance):
        """See if the helper fixture works to load charm configs."""
        config_ins = config_instance()
        assert config_ins is not None

    def test_arg(self, config_instance):
        """Check if set_args() is successfully called when arg is not None."""
        config_ins = config_instance({"foo.bar": "car"})
        config_ins.config.set_args.assert_called_once_with(
            {"foo.bar": "car"}, dots=True
        )

    def test_get_config(self, config_instance):
        """Check if getting section config behaves correctly."""
        config_ins = config_instance()
        config_data = config_ins.get_config("juju")
        assert config_data["controller_endpoint"].get() == "192.168.1.100:17070"
        assert (
            config_data["controller_cacert"].get()
            == "-----BEGIN CERTIFICATE-----\n-----END CERTIFICATE-----\n"
        )
        assert config_data["username"].get() == "example_user"
        assert config_data["password"].get() == "example_password"
