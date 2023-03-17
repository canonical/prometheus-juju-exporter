#!/usr/bin/python3
"""Test Cli."""
from unittest import mock

import pytest

from prometheus_juju_exporter.cli import Cli, main


class TestCli:
    """Cli test class."""

    def test_main(self):
        """Test main function in cli."""
        with mock.patch(
            "prometheus_juju_exporter.cli.ExporterDaemon"
        ) as mock_exporter, mock.patch(
            "prometheus_juju_exporter.cli.project_logger.setLevel"
        ) as set_level:
            main()
            set_level.assert_called_once()
            mock_exporter.assert_called_once()

    @pytest.mark.parametrize(
        "config_option, level_option", [(True, "DEBUG"), (False, "INFO")]
    )
    def test_config_logger(self, config_option, level_option):
        """Test main function in cli."""
        cli = Cli()
        with mock.patch(
            "prometheus_juju_exporter.cli.project_logger.setLevel"
        ) as set_level:
            cli.config["debug"] = config_option
            cli.config_logger()
            set_level.assert_called_once_with(level_option)
