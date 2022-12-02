#!/usr/bin/python3
"""Pytest fixture definitions."""

import os
import unittest.mock as mock

import pytest

os.environ["PROMETHEUSJUJUEXPORTERDIR"] = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def config_instance(monkeypatch):
    """Mock config."""
    from prometheus_juju_exporter.config import Config

    def _config(args=""):
        # Clear global
        monkeypatch.setattr("prometheus_juju_exporter.config.config", None)

        mock_set_args = mock.MagicMock()
        monkeypatch.setattr(
            "prometheus_juju_exporter.config.confuse.Configuration.set_args",
            mock_set_args,
        )

        return Config(args)

    return _config


@pytest.fixture
def exporter_daemon(monkeypatch):
    """Mock exporter daemon."""
    from prometheus_juju_exporter.exporter import ExporterDaemon

    def _daemon(*args, **kwargs):
        # Clear global
        mock_connection = mock.MagicMock()
        mock_collector = mock.AsyncMock()
        mock_async_sleep = mock.AsyncMock()
        mock_logger = mock.MagicMock()
        mock_logger.return_value = mock_logger
        mock_logger.handlers = None

        monkeypatch.setattr("prometheus_juju_exporter.config.config", None)
        monkeypatch.setattr(
            "prometheus_juju_exporter.exporter.start_http_server", mock_connection
        )
        monkeypatch.setattr(
            "prometheus_juju_exporter.collector.CollectorDaemon.get_stats",
            mock_collector,
        )
        monkeypatch.setattr(
            "prometheus_juju_exporter.logging.logging.getLogger", mock_logger
        )
        monkeypatch.setattr("asyncio.sleep", mock_async_sleep)
        return ExporterDaemon(*args, **kwargs)

    return _daemon


@pytest.fixture
def collector_daemon(monkeypatch, stats_gauge):
    """Mock collector daemon."""
    from prometheus_juju_exporter.collector import CollectorDaemon

    def _daemon(args=""):
        # Clear global
        monkeypatch.setattr("prometheus_juju_exporter.config.config", None)
        mock_logger = mock.MagicMock()
        mock_logger.return_value = mock_logger
        mock_logger.handlers = None
        monkeypatch.setattr(
            "prometheus_juju_exporter.logging.logging.getLogger", mock_logger
        )
        return CollectorDaemon(args)

    return _daemon


@pytest.fixture
def mock_gauge():
    """Provide mechanism to test args passed in calls to prometheus_client.Gauge."""

    class TestArgs(object):
        def __init__(self):
            self.args = []
            self.kwargs = []
            self.values = []
            self.call_labels = []

        def __call__(self, *args, **kwargs):
            self.args.append(list(args))
            if "registry" in kwargs:
                kwargs.pop("registry")
            self.kwargs.append(dict(kwargs))
            return self

        def labels(self, *args, **kwargs):
            self.call_labels.append(kwargs)
            return self

        def set(self, value):
            self.values.append(value)

    return TestArgs()


@pytest.fixture
def stats_gauge(monkeypatch, mock_gauge):
    """Mock Gauge calls for the collector module path."""
    monkeypatch.setattr("prometheus_juju_exporter.collector.Gauge", mock_gauge)
    gauge = mock_gauge

    return gauge
