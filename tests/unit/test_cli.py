#!/usr/bin/python3
"""Test Cli."""
from unittest import mock

import pytest

from prometheus_juju_exporter.cli import config_logger, main


class TestCli:
    """Cli test class."""

    def test_main(self):
        """Test main function in cli."""
        with mock.patch(
            "prometheus_juju_exporter.cli.ExporterDaemon"
        ) as mock_exporter, mock.patch(
            "prometheus_juju_exporter.cli.project_logger.setLevel"
        ) as mock_set_level, mock.patch(
            "prometheus_juju_exporter.config.Config.get_config"
        ) as mock_get_config:
            main()
            mock_get_config.assert_called_once()
            mock_set_level.assert_called_once()
            mock_exporter.assert_called_once()

    @pytest.mark.parametrize("config_option, level_option", [(True, "DEBUG"), (False, "INFO")])
    def test_config_logger(self, config_option, level_option):
        """Test main function in cli."""
        with mock.patch("prometheus_juju_exporter.cli.project_logger.setLevel") as set_level:
            config_logger(config_option)
            set_level.assert_called_once_with(level_option)
