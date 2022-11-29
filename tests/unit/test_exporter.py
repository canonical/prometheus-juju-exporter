#!/usr/bin/python3
"""Test exporter daemon."""
import asyncio
import unittest.mock as mock

import pytest


class TestExporterDaemon:
    """Exporter daemon test class."""

    def test_fixture(self, exporter_daemon):
        """See if the helper fixture works to load charm configs."""
        stats_exporter_daemon = exporter_daemon()
        assert stats_exporter_daemon is not None

    def test_setup_logging(self, exporter_daemon):
        """Test setup logger."""
        statsd = exporter_daemon(True)
        statsd.logger.setLevel.assert_called_with("DEBUG")

    def test_parse_config(self, exporter_daemon):
        """Test config parsing."""
        statsd = exporter_daemon()
        assert statsd.config["exporter"]["port"].get() == 9748
        assert statsd.config["exporter"]["collect_interval"].get() == 15

    @pytest.mark.asyncio
    async def test_trigger(self, exporter_daemon):
        """Test trigger function."""
        statsd = exporter_daemon()
        await statsd.trigger(test=True)

        statsd.logger.info.assert_called_with(
            "Gauges collected and ready for exporting."
        )
        asyncio.sleep.assert_called_once_with(
            statsd.config["exporter"]["collect_interval"].get() * 60
        )

    @pytest.mark.asyncio
    async def test_trigger_exception(self, exporter_daemon):
        """Test exception handling of trigger function."""
        statsd = exporter_daemon()

        with mock.patch(
            "prometheus_juju_exporter.collector.CollectorDaemon.get_stats",
            side_effect=Exception("mocked error"),
        ):
            with pytest.raises(SystemExit) as e:
                await statsd.trigger(test=True)

            assert e.type == SystemExit
            assert e.value.code == 1
            statsd.logger.info.assert_called_with(
                "Collection job resulted in error: mocked error"
            )

    def test_run(self, exporter_daemon):
        """Test run function."""
        statsd = exporter_daemon()
        statsd.run(test=True)
