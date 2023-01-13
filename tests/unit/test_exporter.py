#!/usr/bin/python3
"""Test exporter daemon."""
from unittest import mock

import pytest


class TestExporterDaemon:
    """Exporter daemon test class."""

    def test_fixture(self, exporter_daemon):
        """See if the helper fixture works to load charm configs."""
        stats_exporter_daemon = exporter_daemon()
        assert stats_exporter_daemon is not None

    def test_parse_config(self, exporter_daemon):
        """Test config parsing."""
        statsd = exporter_daemon()

        assert isinstance(statsd.config["exporter"]["port"].get(), int)
        assert isinstance(statsd.config["exporter"]["collect_interval"].get(), int)

        assert statsd.config["exporter"]["port"].get() == 9748
        assert statsd.config["exporter"]["collect_interval"].get() == 15

    @pytest.mark.asyncio
    async def test_trigger(self, exporter_daemon):
        """Test trigger function."""
        statsd = exporter_daemon()

        with mock.patch(
            "prometheus_juju_exporter.exporter.asyncio.sleep",
            side_effect=Exception,
        ), pytest.raises(SystemExit) as exit_call:
            await statsd.trigger()

        statsd.collector.get_stats.assert_called_once()
        assert "example_gauge" in statsd.metrics.keys()

        assert exit_call.type == SystemExit
        assert exit_call.value.code == 1

    def test_run(self, exporter_daemon):
        """Test run function."""
        statsd = exporter_daemon()

        with mock.patch(
            "prometheus_juju_exporter.exporter.ExporterDaemon.trigger",
            side_effect=KeyboardInterrupt,
        ), pytest.raises(SystemExit) as exit_call:
            statsd.run()

        assert exit_call.type == SystemExit
        assert exit_call.value.code == 0
