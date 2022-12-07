#!/usr/bin/python3
"""Pytest fixture definitions."""

import os
import unittest.mock as mock

import pytest
from juju.controller import Controller
from juju.model import Model

os.environ["PROMETHEUSJUJUEXPORTERDIR"] = os.path.dirname(os.path.abspath(__file__))


def get_model_list_data():
    """Mock controller.model_uuids."""
    mock_model_list = mock.AsyncMock()

    # uuids are randomly generated for testing purposes
    mock_model_list.return_value = {
        "controller": "65f76aed-789f-4dbf-a75a-a32e5d90ab7e",
        "default": "77643b91-a6f8-4cf6-8755-83c6becd09bb",
        "test": "68c4cc81-9b3d-44a2-a419-d25dfb9d5588",
    }

    return mock_model_list


def get_stats_data():
    """Mock model.get_status."""
    mock_stats = mock.AsyncMock()

    mock_stats.return_value = {
        "model": {
            "name": "test",
            "type": "iaas",
            "controller": "test-cloud-local",
            "cloud": "test-cloud",
            "region": "local",
            "version": "2.9.29",
            "model-status": {"current": "available", "since": "24 Nov 2022 13:19:09Z"},
            "sla": "unsupported",
        },
        "machines": {
            "0": {
                "agent-status": {
                    "status": "started",
                    "since": "24 Nov 2022 13:21:25Z",
                    "version": "2.9.29",
                },
                "hostname": "juju-000ddd-test-0",
                "dns-name": "10.5.0.18",
                "ip-addresses": ["10.5.0.01", "252.0.0.1"],
                "instance-id": "149e81c8-a05b-4852-9201-434670598c30",
                "instance-status": {
                    "status": "running",
                    "message": "ACTIVE",
                    "since": "24 Nov 2022 13:20:33Z",
                },
                "modification-status": {
                    "current": "idle",
                    "since": "24 Nov 2022 13:19:43Z",
                },
                "series": "focal",
                "network-interfaces": {
                    "ens3": {
                        "ip-addresses": ["10.5.0.01"],
                        "mac-address": "fa:16:3e:d4:00:00",
                        "gateway": "10.5.0.1",
                        "space": "alpha",
                        "is-up": "true",
                    },
                    "fan-252": {
                        "ip-addresses": ["252.0.0.1"],
                        "mac-address": "9e:fc:ca:87:00:00",
                        "space": "alpha",
                        "is-up": "true",
                    },
                    "lxdbr0": {
                        "ip-addresses": ["10.100.00.1"],
                        "mac-address": "00:16:3e:e1:00:00",
                        "is-up": "true",
                    },
                },
                "containers": {
                    "0/lxd/0": {
                        "agent-status": {
                            "status": "started",
                            "since": "24 Nov 2022 13:23:50Z",
                            "version": "2.9.29",
                        },
                        "hostname": "juju-000ddd-0-lxd-0",
                        "dns-name": "252.0.0.190",
                        "ip-addresses": ["252.0.0.190"],
                        "instance-id": "juju-000ddd-0-lxd-0",
                        "instance-status": {
                            "status": "running",
                            "message": "Container started",
                            "since": "24 Nov 2022 13:22:46Z",
                        },
                        "modification-status": {
                            "current": "applied",
                            "since": "24 Nov 2022 13:22:46Z",
                        },
                        "series": "focal",
                        "network-interfaces": {
                            "eth0": {
                                "ip-addresses": ["252.0.0.190"],
                                "mac-address": "00:16:3e:7f:00:00",
                                "gateway": "252.0.0.1",
                                "space": "alpha",
                                "is-up": "true",
                            }
                        },
                        "constraints": "arch=amd64 spaces=",
                        "hardware": "availability-zone=nova",
                    }
                },
                "hardware": "arch=amd64 cores=1 mem=2048M root-disk=20480M availability-zone=nova",
            }
        },
        "applications": {
            "ubuntu": {
                "charm": "ubuntu",
                "series": "focal",
                "os": "ubuntu",
                "charm-origin": "charmhub",
                "charm-name": "ubuntu",
                "charm-rev": 21,
                "charm-channel": "stable",
                "exposed": "false",
                "application-status": {
                    "current": "active",
                    "since": "24 Nov 2022 13:23:52Z",
                },
                "units": {
                    "ubuntu/0": {
                        "workload-status": {
                            "current": "active",
                            "since": "24 Nov 2022 13:23:52Z",
                        },
                        "juju-status": {
                            "current": "idle",
                            "since": "24 Nov 2022 13:23:56Z",
                            "version": "2.9.29",
                        },
                        "leader": "true",
                        "machine": "0/lxd/0",
                        "public-address": "252.0.18.190",
                    }
                },
                "version": "20.04",
            }
        },
        "storage": {},
        "controller": {"timestamp": "13:38:17Z"},
    }

    return mock_stats


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
def mock_controller_connection(monkeypatch):
    """Mock juju controller for the collector module path."""
    mock_controller = Controller
    mock_connection = mock.AsyncMock()
    mock_connection.return_value = mock_connection
    mock_controller.connect = mock_connection
    mock_controller.disconnect = mock_connection
    mock_controller.is_connected.return_value = False
    mock_controller.model_uuids = get_model_list_data()
    monkeypatch.setattr(
        "prometheus_juju_exporter.collector.Controller",
        mock_controller,
    )

    return mock_controller


@pytest.fixture
def mock_model_connection(monkeypatch):
    """Mock juju model for the collector module path."""
    mock_model = Model
    mock_connection = mock.AsyncMock()
    mock_connection.return_value = mock_connection
    mock_model.connect = mock_connection
    mock_model.disconnect = mock_connection
    mock_model.is_connected.return_value = False
    mock_model.get_status = get_stats_data()
    monkeypatch.setattr(
        "prometheus_juju_exporter.collector.Model",
        mock_model,
    )

    return mock_model


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
def collector_daemon(
    monkeypatch, mock_model_connection, mock_controller_connection, stats_gauge
):
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

        def remove(self, *labelvalues):
            self.values = {}

    return TestArgs()


@pytest.fixture
def stats_gauge(monkeypatch, mock_gauge):
    """Mock Gauge calls for the collector module path."""
    monkeypatch.setattr("prometheus_juju_exporter.collector.Gauge", mock_gauge)
    gauge = mock_gauge

    return gauge
