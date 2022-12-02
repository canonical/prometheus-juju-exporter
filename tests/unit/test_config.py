#!/usr/bin/python3
"""Test Config class."""
import unittest.mock as mock

import pytest


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

    def test_validate_config_options_success(self, config_instance):
        """Test validate_config_values function."""
        config_ins = config_instance()

        # Test valid config values in config.yaml file
        with mock.patch("prometheus_juju_exporter.config.exit") as exit_call:
            config_ins.validate_config_options()
            exit_call.assert_not_called()

    @pytest.mark.parametrize("port_value", ("foo", 65536, None))
    def test_validate_config_options_fail(self, config_instance, port_value):
        """Test validate_config_values function."""
        config_ins = config_instance()

        # Test bad config values
        config_ins.config["exporter"]["port"].set(port_value)
        with mock.patch("prometheus_juju_exporter.config.exit") as exit_call:
            config_ins.validate_config_options()
            assert config_ins.config["exporter"]["port"].get() == port_value
            exit_call.assert_called_once()
