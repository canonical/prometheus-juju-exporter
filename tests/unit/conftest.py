#!/usr/bin/python3
"""Pytest fixture definitions."""

import os
from unittest import mock

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
    }

    return mock_model_list


def get_juju_stats_data():
    """Mock model.get_status."""
    mock_stats = mock.AsyncMock()

    mock_stats.return_value = {
        "model": {
            "name": "",
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


def collected_stats_data():
    return {
        "example_gauge": {
            "gauge_desc": "This is an example gauge",
            "labels": [
                "job",
                "hostname",
                "customer",
                "cloud_name",
                "juju_model",
                "type",
            ],
            "labelvalues_update": [
                (
                    {
                        "job": "prometheus-juju-exporter",
                        "hostname": "hostname1",
                        "customer": "customer1",
                        "cloud_name": "cloud name",
                        "juju_model": "juju model",
                        "type": "machine type",
                    },
                    0,
                ),
                (
                    {
                        "job": "prometheus-juju-exporter",
                        "hostname": "hostname2",
                        "customer": "customer2",
                        "cloud_name": "cloud name",
                        "juju_model": "juju model",
                        "type": "machine type",
                    },
                    0,
                ),
            ],
            "labelvalues_remove": [
                [
                    "prometheus-juju-exporter",
                    "hostname3",
                    "customer3",
                    "cloud name",
                    "juju model",
                    "machine type",
                ]
            ],
        }
    }


@pytest.fixture
def update_model_status(monkeypatch, request):
    """Fixture to update the model status dynamically."""

    def _nested_update(left, right):
        """In-place nested update a dictionary."""
        for k, v in right.items():
            if isinstance(v, dict):
                left[k] = _nested_update(left.get(k, {}), v)
            else:
                left[k] = v
        return left

    mock_get_status = mock.AsyncMock()
    status_data = get_juju_stats_data().return_value
    _nested_update(status_data, request.param)
    mock_get_status.return_value = status_data
    monkeypatch.setattr("juju.model.Model.get_status", mock_get_status)


@pytest.fixture
def config_instance(monkeypatch):
    """Mock config."""
    from prometheus_juju_exporter.config import Config

    def _config(args=""):
        # Clear global
        monkeypatch.setattr(
            "prometheus_juju_exporter.config.Config.config",
            None,
        )
        mock_set_args = mock.MagicMock()
        monkeypatch.setattr(
            "prometheus_juju_exporter.config.confuse.Configuration.set_args",
            mock_set_args,
        )

        return Config(args)

    return _config


@pytest.fixture
def mock_controller_connection(monkeypatch, mock_model_connection):
    """Mock juju controller for the collector module path."""
    mock_controller = Controller
    mock_connection = mock.AsyncMock()
    mock_connection.return_value = mock_connection
    mock_controller.connect = mock_connection
    mock_controller.disconnect = mock_connection
    mock_controller.is_connected.return_value = False
    mock_controller.model_uuids = get_model_list_data()
    mock_controller.get_model = mock.AsyncMock()
    mock_controller.get_model.return_value = mock_model_connection()
    monkeypatch.setattr(
        "prometheus_juju_exporter.collector.Controller",
        mock_controller,
    )

    return mock_controller


@pytest.fixture
def mock_model_connection():
    """Mock juju model for the collector module path."""
    mock_model = Model
    mock_model.get_status = get_juju_stats_data()

    return mock_model


@pytest.fixture
def exporter_daemon(monkeypatch, stats_gauge):
    """Mock exporter daemon."""
    from prometheus_juju_exporter.exporter import ExporterDaemon

    def _daemon(*args, **kwargs):
        # Clear global
        mock_http_server = mock.MagicMock()
        mock_collector = mock.AsyncMock()
        mock_collector.return_value = collected_stats_data()
        mock_async_sleep = mock.AsyncMock()
        mock_logger = mock.MagicMock()
        mock_logger.return_value = mock_logger
        mock_logger.handlers = None

        monkeypatch.setattr(
            "prometheus_juju_exporter.exporter.start_http_server", mock_http_server
        )
        monkeypatch.setattr(
            "prometheus_juju_exporter.collector.Collector.get_stats",
            mock_collector,
        )
        monkeypatch.setattr("prometheus_juju_exporter.logging.getLogger", mock_logger)
        monkeypatch.setattr("asyncio.sleep", mock_async_sleep)
        return ExporterDaemon(*args, **kwargs)

    return _daemon


@pytest.fixture
def collector_daemon(monkeypatch, mock_controller_connection):
    """Mock collector."""
    from prometheus_juju_exporter.collector import Collector

    def _collector(*args, **kwargs):
        # Clear global
        mock_logger = mock.MagicMock()
        mock_logger.return_value = mock_logger
        mock_logger.handlers = None
        monkeypatch.setattr("prometheus_juju_exporter.logging.getLogger", mock_logger)
        return Collector(*args, **kwargs)

    return _collector


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
            self.values = []

    return TestArgs()


@pytest.fixture
def stats_gauge(monkeypatch, mock_gauge):
    """Mock Gauge calls for the collector module path."""
    monkeypatch.setattr("prometheus_juju_exporter.exporter.Gauge", mock_gauge)
    gauge = mock_gauge

    return gauge
