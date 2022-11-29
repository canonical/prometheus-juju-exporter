#!/usr/bin/python3
"""Test Cli."""
import mock
import pytest

from prometheus_juju_exporter.cli import main


class TestCli:
    """Cli test class."""

    @pytest.mark.parametrize("option", ("-d", "--debug"))
    def test_cli_main(self, monkeypatch, option):
        """Test main function in cli."""
        exporter = mock.MagicMock()
        exporter.run = mock.MagicMock()
        monkeypatch.setattr("prometheus_juju_exporter.cli.ExporterDaemon", exporter)

        main([option])
        exporter.assert_called_once_with(debug=True)
