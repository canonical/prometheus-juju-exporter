#!/usr/bin/python3
"""Test exporter daemon."""
import unittest.mock as mock

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
        await statsd.trigger(once=True)

        statsd.collector.get_stats.assert_called_once()
        assert "example_gauge" in statsd.metrics.keys()

    @pytest.mark.asyncio
    async def test_trigger_exception(self, exporter_daemon):
        """Test exception handling of trigger function."""
        statsd = exporter_daemon()

        with mock.patch(
            "prometheus_juju_exporter.collector.Collector.get_stats",
            side_effect=Exception("mocked error"),
        ):
            with mock.patch("prometheus_juju_exporter.exporter.exit") as exit_call:
                await statsd.trigger(once=True)
                exit_call.assert_called_once()

    def test_run(self, exporter_daemon):
        """Test run function."""
        statsd = exporter_daemon()
        statsd.run(once=True)
        statsd.collector.get_stats.assert_called_once()
