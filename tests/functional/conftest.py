import logging
import os
from subprocess import check_call, check_output

import pytest
import yaml

JUJU_CRED_DIR = "/home/ubuntu/.local/share/juju/"
SNAP_CONFIG_DIR = "/var/snap/prometheus-juju-exporter/"
TMP_DIR = "/tmp"
SNAP_NAME = "prometheus-juju-exporter"


def get_juju_data():
    """Get juju account data and credentials."""
    juju_controller_file = os.path.join(JUJU_CRED_DIR, "controllers.yaml")
    juju_account_file = os.path.join(JUJU_CRED_DIR, "accounts.yaml")
    assert os.path.isfile(juju_controller_file)
    assert os.path.isfile(juju_account_file)

    with open(juju_controller_file) as controller_file:
        try:
            controller_data = yaml.safe_load(controller_file)
            current_controller = controller_data["current-controller"]
            cacert = controller_data["controllers"][current_controller]["ca-cert"]
            endpoint = controller_data["controllers"][current_controller][
                "api-endpoints"
            ][0]
            assert current_controller is not None
            assert cacert is not None
            assert endpoint is not None
        except yaml.YAMLError as e:
            logging.error(e)

    with open(juju_account_file) as account_file:
        try:
            account_data = yaml.safe_load(account_file)
            user = account_data["controllers"][current_controller]["user"]
            password = account_data["controllers"][current_controller]["password"]
        except yaml.YAMLError as e:
            logging.error(e)

    return user, password, cacert, endpoint


def generate_config_data(user, password, cacert, endpoint):
    """Generate config data with the parsed juju info."""
    return {
        "customer": {"name": "example_customer", "cloud_name": "example_cloud"},
        "juju": {
            "controller_endpoint": endpoint,
            "controller_cacert": cacert,
            "username": user,
            "password": password,
        },
        "exporter": {
            "port": 5000,
            "collect_interval": 1,
        },
    }


def configure_snap(version):
    """Configure the snap."""
    user, password, cacert, endpoint = get_juju_data()
    config_data = generate_config_data(user, password, cacert, endpoint)

    temp_config_file = os.path.join(TMP_DIR, "prometheus_juju_exporter_config.yaml")
    with open(temp_config_file, "w") as config_file:
        try:
            yaml.dump(config_data, config_file)
        except yaml.YAMLError as e:
            logging.error(e)

    snap_config_file = os.path.join(SNAP_CONFIG_DIR, version, "config.yaml")
    assert (
        check_call(f"sudo mv {temp_config_file} {snap_config_file}".split())
        == 0  # noqa
    )

    assert os.path.isfile(snap_config_file)


def get_snap_version():
    """Get the version of the installed snap."""
    try:
        output = (
            check_output(f"snap info {SNAP_NAME}".split()).decode().strip().splitlines()
        )
        package_info = [i for i in output if "installed:" in i]
        version = package_info[0].split("(")[1].split(")")[0]
    except Exception as e:
        logging.error("Error getting snap version: %s", e)

    return version


@pytest.fixture(scope="session", autouse=True)
def setup_snap():
    """Install the package to the system and cleanup afterwards.

    An environment variable TEST_SNAP is needed to install the snap.
    """
    test_snap = os.environ.get("TEST_SNAP", None)
    if test_snap:
        logging.info("Installing %s snap package...", test_snap)
        assert os.path.isfile(test_snap)
        assert (
            check_call(f"sudo snap install --dangerous {test_snap}".split())
            == 0  # noqa
        )

        version = get_snap_version()
        configure_snap(version)

        assert check_call(f"sudo snap start --enable {SNAP_NAME}".split()) == 0  # noqa
    else:
        logging.error(
            "Could not find %s snap package for testing. Needs to build it first.",
            SNAP_NAME,
        )

    yield test_snap

    if test_snap:
        logging.info("Removing %s snap package...", SNAP_NAME)
        check_call(f"sudo snap stop --disable {SNAP_NAME}".split())
        check_call(f"sudo snap remove {SNAP_NAME}".split())


@pytest.fixture(scope="session", autouse=True)
def setup_test_model():
    """Create a test model for machine manipulation."""
    test_model_name = "prometheus-juju-exporter-func-test"
    logging.info("Creating model '%s'...", test_model_name)
    assert check_call(f"juju add-model {test_model_name}".split()) == 0  # noqa

    yield test_model_name

    logging.info("Destroying model '%s'...", test_model_name)
    check_call(
        f"juju destroy-model --destroy-storage --force -y {test_model_name}".split()
    )
