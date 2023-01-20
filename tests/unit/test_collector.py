#!/usr/bin/python3
"""Test collctor."""
import pytest


class TestCollectorDaemon:
    """Collector test class."""

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
        assert statsd.config["detection"]["virt_macs"].get() == [
            "52:54:00",
            "fa:16:3e",
            "06:f1:3a",
            "00:0d:3a",
            "00:50:56",
        ]

    @pytest.mark.asyncio
    async def test_get_stats(self, collector_daemon):
        """Test get_stats function and the execution of the collector."""
        statsd = collector_daemon()
        statsd.currently_cached_labels = {
            "juju-000ddd-test-0": (
                {
                    "job": "prometheus-juju-exporter",
                    "hostname": "juju-000ddd-test-0",
                    "customer": "example_customer",
                    "cloud_name": "example_cloud",
                    "juju_model": "default",
                    "type": "kvm",
                },
                1,
            ),
            "juju-000ddd-0-lxd-1": (
                {
                    "job": "prometheus-juju-exporter",
                    "hostname": "juju-000ddd-0-lxd-1",
                    "customer": "example_customer",
                    "cloud_name": "example_cloud",
                    "juju_model": "test",
                    "type": "lxd",
                },
                1,
            ),
        }

        await statsd.get_stats()

        assert statsd.data == {
            "juju_machine_state": {
                "gauge_desc": "Running status of juju machines",
                "labels": [
                    "job",
                    "hostname",
                    "customer",
                    "cloud_name",
                    "juju_model",
                    "type",
                ],
                "labelvalues_remove": [
                    [
                        "prometheus-juju-exporter",
                        "juju-000ddd-0-lxd-1",
                        "example_customer",
                        "example_cloud",
                        "test",
                        "lxd",
                    ]
                ],
                "labelvalues_update": [
                    (
                        {
                            "cloud_name": "example_cloud",
                            "customer": "example_customer",
                            "hostname": "juju-000ddd-test-0",
                            "job": "prometheus-juju-exporter",
                            "juju_model": "controller",
                            "type": "kvm",
                        },
                        1,
                    ),
                    (
                        {
                            "cloud_name": "example_cloud",
                            "customer": "example_customer",
                            "hostname": "juju-000ddd-0-lxd-0",
                            "job": "prometheus-juju-exporter",
                            "juju_model": "controller",
                            "type": "lxd",
                        },
                        1,
                    ),
                    (
                        {
                            "cloud_name": "example_cloud",
                            "customer": "example_customer",
                            "hostname": "juju-000ddd-test-0",
                            "job": "prometheus-juju-exporter",
                            "juju_model": "default",
                            "type": "kvm",
                        },
                        1,
                    ),
                    (
                        {
                            "cloud_name": "example_cloud",
                            "customer": "example_customer",
                            "hostname": "juju-000ddd-0-lxd-0",
                            "job": "prometheus-juju-exporter",
                            "juju_model": "default",
                            "type": "lxd",
                        },
                        1,
                    ),
                ],
            },
        }

    @pytest.mark.parametrize(
        "mac_address,expect_machine_type",
        [("fa:16:3e:d4:00:00", "kvm"), ("00:00:00:00:00:00", "metal")],
    )
    def test_get_machine_type(self, collector_daemon, mac_address, expect_machine_type):
        """Test get_stats function and the execution of the collector."""
        statsd = collector_daemon()
        machine = {
            "network-interfaces": {
                "ens3": {
                    "mac-address": mac_address,
                }
            }
        }
        machine_type = statsd._get_machine_type(machine)

        assert machine_type.value == expect_machine_type
