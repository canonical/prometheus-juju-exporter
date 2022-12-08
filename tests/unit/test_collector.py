#!/usr/bin/python3
"""Test collctor daemon."""
import pytest


class TestCollectorDaemon:
    """Collector daemon test class."""

    def test_fixture(self, collector_daemon):
        """See if the helper fixture works to load charm configs."""
        stats_collector_daemon = collector_daemon()
        assert stats_collector_daemon is not None

    def test_parse_config(self, collector_daemon):
        """Test config parsing."""
        statsd = collector_daemon()
        assert (
            statsd.config["juju"]["controller_endpoint"].get() == "192.168.1.100:17070"
        )
        assert (
            statsd.config["juju"]["controller_cacert"].get()
            == "-----BEGIN CERTIFICATE-----\n-----END CERTIFICATE-----\n"
        )
        assert statsd.config["juju"]["username"].get() == "example_user"
        assert statsd.config["juju"]["password"].get() == "example_password"
        assert statsd.config["customer"]["name"].get() == "example_customer"
        assert statsd.config["customer"]["cloud_name"].get() == "example_cloud"

    @pytest.mark.asyncio
    async def test_get_stats(self, collector_daemon):
        """Test get_stats function and the execution of the collector."""
        statsd = collector_daemon()
        await statsd.get_stats()
        assert statsd.currently_cached_labels == {
            "juju-000ddd-test-0": {
                "job": "prometheus-juju-exporter",
                "hostname": "juju-000ddd-test-0",
                "customer": "example_customer",
                "cloud_name": "example_cloud",
                "juju_model": "test",
                "type": "kvm",
                "value": 1,
            },
            "juju-000ddd-0-lxd-0": {
                "job": "prometheus-juju-exporter",
                "hostname": "juju-000ddd-0-lxd-0",
                "customer": "example_customer",
                "cloud_name": "example_cloud",
                "juju_model": "test",
                "type": "lxd",
                "value": 1,
            },
        }

    def test_create_gauge_label(self, collector_daemon):
        """Test _create_gauge_label function."""
        statsd = collector_daemon()

        labels = statsd._create_gauge_label("host", "model", "machine", 0)

        assert labels == {
            "job": "prometheus-juju-exporter",
            "hostname": "host",
            "customer": statsd.config["customer"]["name"].get(str),
            "cloud_name": statsd.config["customer"]["cloud_name"].get(str),
            "juju_model": "model",
            "type": "machine",
            "value": 0,
        }

    def test_get_gauge_value(self, collector_daemon):
        """Test _get_gauge_value function."""
        statsd = collector_daemon()

        up_status = statsd._get_gauge_value("started")
        assert up_status == 1

        down_status = statsd._get_gauge_value("down")
        assert down_status == 0

    @pytest.mark.asyncio
    async def test_get_labels_to_remove(self, collector_daemon):
        """Test _remove_stale_lables function."""
        statsd = collector_daemon()

        statsd.currently_cached_labels = {
            "juju-000ddd-test-0": {
                "job": "prometheus-juju-exporter",
                "hostname": "juju-000ddd-test-0",
                "customer": "example_customer",
                "cloud_name": "example_cloud",
                "juju_model": "test",
                "type": "kvm",
                "value": 1,
            },
            "juju-000ddd-0-lxd-0": {
                "job": "prometheus-juju-exporter",
                "hostname": "juju-000ddd-0-lxd-0",
                "customer": "example_customer",
                "cloud_name": "example_cloud",
                "juju_model": "test",
                "type": "lxd",
                "value": 1,
            },
            "juju-000ddd-0-lxd-1": {
                "job": "prometheus-juju-exporter",
                "hostname": "juju-000ddd-0-lxd-1",
                "customer": "example_customer",
                "cloud_name": "example_cloud",
                "juju_model": "test",
                "type": "lxd",
                "value": 1,
            },
        }

        await statsd.get_stats()
        assert statsd.data["juju_machine_state"]["labelvalues_remove"] == [
            [
                "prometheus-juju-exporter",
                "juju-000ddd-0-lxd-1",
                "example_customer",
                "example_cloud",
                "test",
                "lxd",
                1,
            ]
        ]

    @pytest.mark.asyncio
    async def test_get_models(self, collector_daemon):
        """Test _get_models for getting a list of all models under a controller."""
        statsd = collector_daemon()

        uuid = await statsd._get_models(
            endpoint=statsd.config["juju"]["controller_endpoint"].get(),
            username=statsd.config["juju"]["username"].get(),
            password=statsd.config["juju"]["password"].get(),
            cacert=statsd.config["juju"]["controller_cacert"].get(),
        )

        assert uuid == {
            "controller": "65f76aed-789f-4dbf-a75a-a32e5d90ab7e",
            "default": "77643b91-a6f8-4cf6-8755-83c6becd09bb",
            "test": "68c4cc81-9b3d-44a2-a419-d25dfb9d5588",
        }

    @pytest.mark.asyncio
    async def test_connect_controller(self, collector_daemon):
        """Test _connect_controller function."""
        statsd = collector_daemon()
        await statsd._connect_controller(
            endpoint=statsd.config["juju"]["controller_endpoint"].get(),
            username=statsd.config["juju"]["username"].get(),
            password=statsd.config["juju"]["password"].get(),
            cacert=statsd.config["juju"]["controller_cacert"].get(),
        )

        statsd.controller.connect.assert_called_once_with(
            endpoint=statsd.config["juju"]["controller_endpoint"].get(),
            username=statsd.config["juju"]["username"].get(),
            password=statsd.config["juju"]["password"].get(),
            cacert=statsd.config["juju"]["controller_cacert"].get(),
        )

    @pytest.mark.asyncio
    async def test_connect_model(self, collector_daemon):
        """Test _connect_model function."""
        statsd = collector_daemon()
        await statsd._connect_model(
            uuid="68c4cc81-9b3d-44a2-a419-d25dfb9d5588",
            endpoint=statsd.config["juju"]["controller_endpoint"].get(),
            username=statsd.config["juju"]["username"].get(),
            password=statsd.config["juju"]["password"].get(),
            cacert=statsd.config["juju"]["controller_cacert"].get(),
        )

        statsd.model.connect.assert_called_once_with(
            uuid="68c4cc81-9b3d-44a2-a419-d25dfb9d5588",
            endpoint=statsd.config["juju"]["controller_endpoint"].get(),
            username=statsd.config["juju"]["username"].get(),
            password=statsd.config["juju"]["password"].get(),
            cacert=statsd.config["juju"]["controller_cacert"].get(),
        )
