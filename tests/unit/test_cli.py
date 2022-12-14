#!/usr/bin/python3
"""Test Cli."""
import unittest.mock as mock

import pytest

from prometheus_juju_exporter.cli import config_logger, main


class TestCli:
    """Cli test class."""

    @pytest.mark.parametrize("option", ("-d", "--debug"))
    def test_cli_main(self, monkeypatch, option):
        """Test main function in cli."""
        mock_exporter = mock.MagicMock()
        monkeypatch.setattr(
            "prometheus_juju_exporter.cli.ExporterDaemon", mock_exporter
        )

        with mock.patch("prometheus_juju_exporter.cli.config_logger") as config_logger:
            main([option])
            config_logger.assert_called_once_with(debug=True)
            mock_exporter.assert_called_once()

    @pytest.mark.parametrize(
        "arg_option, level_option", [(True, "DEBUG"), (False, "INFO")]
    )
    def test_config_logger(self, arg_option, level_option):
        """Test main function in cli."""
        with mock.patch(
            "prometheus_juju_exporter.cli.project_logger.setLevel"
        ) as set_level:
            config_logger(debug=arg_option)
            set_level.assert_called_once_with(level_option)
