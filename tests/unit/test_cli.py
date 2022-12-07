#!/usr/bin/python3
"""Test Cli."""
import unittest.mock as mock

import pytest

from prometheus_juju_exporter.cli import main


class TestCli:
    """Cli test class."""

    @pytest.mark.parametrize("option", ("-d", "--debug"))
    def test_cli_main(self, option):
        """Test main function in cli."""
        with mock.patch("prometheus_juju_exporter.cli.ExporterDaemon") as exporter:
            main([option])
            exporter.assert_called_once_with(debug=True)
