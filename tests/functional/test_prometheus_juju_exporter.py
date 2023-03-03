#!/usr/bin/python3
"""Test exporter daemon."""
from subprocess import check_call

from helpers import add_machine, get_machines_counts, get_registry_data, remove_machine


def test_snap_startup():
    """Check if the snap is in active state."""
    assert (
        check_call(
            "systemctl is-active --quiet "
            "snap.prometheus-juju-exporter.prometheus-juju-exporter.service".split()
        )
        == 0  # noqa
    )


def test_connect_registry():
    """Check if registry can be reached via HTTP requests."""
    registry_data = get_registry_data()
    assert registry_data is not None


def test_machine_counts():
    """Test if the snap correct reports total, active, and inactive machine counts."""
    machine_count = get_machines_counts()
    registry_data = get_registry_data()
    machines = [
        machine
        for machine in registry_data.decode().strip().splitlines()
        if not machine.startswith("#")
    ]
    assert len(machines) == sum(machine_count.values())

    up_machines = [machine for machine in machines if machine.endswith("1.0")]
    assert len(up_machines) == machine_count["up"]

    down_machines = [machine for machine in machines if machine.endswith("0.0")]
    assert len(down_machines) == machine_count["down"]


def test_add_machine(setup_test_model):
    """Test if the snap correctly reports machine counts when adding a machine."""
    current_registry_data = get_registry_data()
    current_machines = [
        machine
        for machine in current_registry_data.decode().strip().splitlines()
        if not machine.startswith("#")
    ]

    # Add a machine to test model
    add_machine()

    new_registry_data = get_registry_data()
    new_machines = [
        machine
        for machine in new_registry_data.decode().strip().splitlines()
        if not machine.startswith("#")
    ]
    target_count = len(current_machines) + 1

    assert len(new_machines) == target_count


def test_remove_machine(setup_test_model):
    """Test if the snap correctly reports machine counts when removing a machine."""
    # Add a machine to test model
    add_machine()

    current_registry_data = get_registry_data()
    current_machines = [
        machine
        for machine in current_registry_data.decode().strip().splitlines()
        if not machine.startswith("#")
    ]

    # Remove a machine from test model
    remove_machine()

    new_registry_data = get_registry_data()
    new_machines = [
        machine
        for machine in new_registry_data.decode().strip().splitlines()
        if not machine.startswith("#")
    ]
    target_count = len(current_machines) - 1

    assert len(new_machines) == target_count
