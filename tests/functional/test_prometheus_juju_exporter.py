#!/usr/bin/python3
"""Test exporter daemon."""
from subprocess import check_call


def test_snap_startup():
    """Check if the snap is in active state."""
    assert (
        check_call(
            "systemctl is-active --quiet snap.prometheus-juju-exporter.prometheus-juju-exporter.service".split()
        )
        == 0  # noqa
    )


def test_connect_registry(get_registry_data):
    """Check if registry can be reached via HTTP requests."""
    registry_data = get_registry_data()
    assert registry_data is not None


def test_machine_counts(get_machines_counts, get_registry_data):
    """Test if the snap correct recports total, active, and inactive machine counts."""
    machine_count = get_machines_counts()
    registry_data = get_registry_data()
    machines = [
        i for i in registry_data.decode().strip().splitlines() if not i.startswith("#")
    ]
    assert len(machines) == sum(machine_count.values())

    up_machines = [i for i in machines if i.endswith("1.0")]
    assert len(up_machines) == machine_count["up"]

    down_machines = [i for i in machines if i.endswith("0.0")]
    assert len(down_machines) == machine_count["down"]


def test_add_machine(add_machine, get_registry_data):
    """Test if the snap correctly recports machine counts when adding a machine."""
    current_registry_data = get_registry_data()
    current_machines = [
        i
        for i in current_registry_data.decode().strip().splitlines()
        if not i.startswith("#")
    ]

    # Add a machine to test model
    add_machine()

    new_registry_data = get_registry_data()
    new_machines = [
        i
        for i in new_registry_data.decode().strip().splitlines()
        if not i.startswith("#")
    ]
    target_count = len(current_machines) + 1

    assert len(new_machines) == target_count


def test_remove_machine(remove_machine, get_registry_data):
    """Test if the snap correctly recports machine counts when removing a machine."""
    current_registry_data = get_registry_data()
    current_machines = [
        i
        for i in current_registry_data.decode().strip().splitlines()
        if not i.startswith("#")
    ]

    # Remove a machine from test model
    remove_machine()

    new_registry_data = get_registry_data()
    new_machines = [
        i
        for i in new_registry_data.decode().strip().splitlines()
        if not i.startswith("#")
    ]
    target_count = len(current_machines) - 1

    assert len(new_machines) == target_count
