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
