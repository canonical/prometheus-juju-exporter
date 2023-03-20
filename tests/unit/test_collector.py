#!/usr/bin/python3
"""Test collctor."""
from unittest import mock

import pytest

from prometheus_juju_exporter.collector import MachineType


class TestCollectorDaemon:
    """Collector test class."""

    def test_fixture(self, collector_daemon):
        """See if the helper fixture works to load charm configs."""
        stats_collector_daemon = collector_daemon()
        assert stats_collector_daemon is not None

    def test_parse_config(self, collector_daemon):
        """Test config parsing."""
        statsd = collector_daemon()
        assert statsd.config["juju"]["controller_endpoint"].get() == "192.168.1.100:17070"
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
    @pytest.mark.parametrize(
        # fmt: off
        "update_model_status",
        [
            {},
            {"machines": {"0": {"hostname": "None", "instance-id": "juju-000ddd-test-0"}}},
            {"machines": {"0": {"hostname": None, "instance-id": "juju-000ddd-test-0"}}},
            {"machines": {"0": {"containers": {"0/lxd/0": {"hostname": "None"}}}}},
            {"machines": {"0": {"containers": {"0/lxd/0": {"hostname": None}}}}},
        ],
        indirect=True,
        # fmt: on
    )
    async def test_get_stats(self, collector_daemon, update_model_status):
        """Test get_stats function and the execution of the collector."""
        statsd = collector_daemon()

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

    @pytest.mark.asyncio
    async def test_skip_inaccessible_models(self, collector_daemon):
        """Test exception handling in case a model is inaccessible."""
        statsd = collector_daemon()
        with mock.patch(
            "prometheus_juju_exporter.collector.Controller.get_model",
            side_effect=Exception,
        ):
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
                "labelvalues_update": [],
            }
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
        machine_type = statsd._get_machine_type(machine, "dummy-0")

        assert machine_type.value == expect_machine_type

    @pytest.mark.parametrize(
        "skip_interfaces, expected_type",
        [
            ([r"^virbr\d*", r"^tap-"], MachineType.METAL),
            ([], MachineType.KVM),
        ],
    )
    def test_get_machine_type_interface_skip(
        self, skip_interfaces, expected_type, collector_daemon
    ):
        """Test that blacklisted interfaces are not used to detect machine type.

        There are two scenarios to this test:
          * Without setting 'skip_interfaces', the machine should be marked as KVM
          * With right interfaces skipped, the machine should be marked as METAL
        """
        statsd = collector_daemon()
        kvm_prefix = "fa:16:3e:"
        tap_prefix = "52:54:00:"
        machine_mac = "00:00:00:00:00:00"

        machine = {
            "network-interfaces": {
                "ens3": {
                    "mac-address": machine_mac,
                },
                "virbr0": {
                    "mac-address": kvm_prefix + "00:00:01",
                },
                "virbr1": {
                    "mac-address": kvm_prefix + "00:00:02",
                },
                "tap-0": {
                    "mac-address": tap_prefix + "00:00:01",
                },
            }
        }

        statsd.config["detection"]["virt_macs"].set([kvm_prefix, tap_prefix])
        statsd.config["detection"]["skip_interfaces"].set(skip_interfaces)

        assert statsd._get_machine_type(machine, "dummy-0") == expected_type

    @pytest.mark.parametrize(
        "host, host_id",
        [
            ({"hostname": None, "instance-id": "testid"}, "testid"),
            ({"hostname": "None", "instance-id": "testid"}, "testid"),
            ({"hostname": "testhost", "instance-id": "testid"}, "testhost"),
            ({"hostname": None, "instance-id": None}, "None"),
            ({"hostname": None, "instance-id": "None"}, "None"),
            ({"hostname": "None", "instance-id": None}, "None"),
            ({"hostname": "None", "instance-id": "None"}, "None"),
            ({"hostname": None, "instance-id": "pending"}, "None"),
            ({"hostname": "testhost"}, "testhost"),
            ({"hostname": None}, "None"),
            ({"hostname": "None"}, "None"),
            ({"instance-id": "testid"}, "testid"),
            ({"instance-id": None}, "None"),
            ({"instance-id": "None"}, "None"),
            ({"instance-id": "pending"}, "None"),
            ({}, "None"),
        ],
    )
    def test_get_host_identifier(self, collector_daemon, host, host_id):
        """Test getting a valid host id from host data."""
        assert collector_daemon()._get_host_identifier(host) == host_id
