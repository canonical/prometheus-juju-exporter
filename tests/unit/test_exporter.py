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
    async def test_update_registry(self, monkeypatch, exporter_daemon):
        """Test update_registry function."""
        statsd = exporter_daemon()
        collector = statsd.collector
        stats = await collector.get_stats()
        sample_labels = [
            {
                "job": "prometheus-juju-exporter",
                "hostname": "hostname0",
                "customer": "customer0",
                "cloud_name": "cloud name",
                "juju_model": "juju model",
                "type": "machine type",
            },
            {
                "job": "prometheus-juju-exporter",
                "hostname": "hostname1",
                "customer": "customer1",
                "cloud_name": "cloud name",
                "juju_model": "juju model",
                "type": "machine type",
            },
        ]
        expected_labels = [
            {
                "job": "prometheus-juju-exporter",
                "hostname": "hostname1",
                "customer": "customer1",
                "cloud_name": "cloud name",
                "juju_model": "juju model",
                "type": "machine type",
            },
            {
                "job": "prometheus-juju-exporter",
                "hostname": "hostname2",
                "customer": "customer2",
                "cloud_name": "cloud name",
                "juju_model": "juju model",
                "type": "machine type",
            },
        ]
        metric1, metric2 = mock.MagicMock(), mock.MagicMock()
        metrics = [metric1, metric2]
        sample1, sample2 = mock.MagicMock(), mock.MagicMock()
        sample1.labels, sample2.labels = sample_labels
        samples = [sample1, sample2]
        for sample in samples:
            sample.name = "example_gauge"
        for metric in metrics:
            metric.samples = samples
        monkeypatch.setattr(
            "prometheus_juju_exporter.exporter.CollectorRegistry.collect",
            lambda r: metrics,
        )
        statsd.update_registry(stats)
        assert statsd.metrics["example_gauge"].call_labels == expected_labels

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
