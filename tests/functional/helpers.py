import json
import logging
import urllib.request
from subprocess import check_call, check_output
from time import sleep

import juju_wait

PORT = 5000
COLLECTION_INTERVAL = 60
MAX_RETRY_COUNT = 10
CONNECTION_TIMEOUT_IN_SECONDS = 10
WAIT_BETWEEN_CONNECTION_IN_SECONDS = 10


def get_registry_data():
    """Connect to the registry and wait to get labelvalues data upon completing the collection."""
    previous_registry_data = None
    registry_data = None
    connection_retry = 0

    # Make sure the registry_data is accessible and collection process
    # is complete (no more labelvalues added to registry)
    while connection_retry < MAX_RETRY_COUNT and (
        registry_data is None or registry_data != previous_registry_data
    ):
        try:
            previous_registry_data = registry_data
            localhost = urllib.request.urlopen(
                f"http://localhost:{PORT}/", timeout=CONNECTION_TIMEOUT_IN_SECONDS
            )
            sleep(COLLECTION_INTERVAL)
            registry_data = localhost.read()
            localhost.close()
        except urllib.error.URLError as e:
            connection_retry += 1
            logging.debug(
                "Unable to connect to registry. This is the %d's attempt. %s",
                connection_retry,
                e,
            )
            sleep(WAIT_BETWEEN_CONNECTION_IN_SECONDS)

    return registry_data


def get_juju_models():
    """Get a list of juju models under the current controller."""
    models_output = check_output("juju models --format json".split()).decode()
    models = json.loads(models_output)

    model_names = []
    for model in models["models"]:
        model_names.append(model["short-name"])
    return model_names


def get_machines_in_model(machines):
    """Parse machine stats to get machine counts under a model."""
    ups = 0
    downs = 0

    for machine in machines["machines"].values():
        active = int(machine["juju-status"]["current"] == "started")
        ups += active
        downs += 1 - active

        if "containers" in machine.keys():
            for container in machine["containers"].values():
                active = int(container["juju-status"]["current"] == "started")
                ups += active
                downs += 1 - active

    return ups, downs


def get_machines_counts():
    """Get the number of active and inactive machines under the current controller."""
    models = get_juju_models()
    machine_counts = {"up": 0, "down": 0}

    for model in models:
        machines_output = check_output(f"juju machines -m {model} --format json".split()).decode()
        machines = json.loads(machines_output)
        model_ups, model_downs = get_machines_in_model(machines)
        machine_counts["up"] += model_ups
        machine_counts["down"] += model_downs

    return machine_counts


def juju_wait_until_complete():
    """Block until reaching the target status."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logging.info("Calling juju-wait")
    juju_wait.wait(logger, machine_pending_timeout=600)
    logging.debug("juju-wait complete")


def add_machine():
    """Add a machine to the test model."""
    assert check_call("juju add-machine".split()) == 0  # noqa
    juju_wait_until_complete()


def remove_machine():
    """Remove a machine from the test model."""
    assert check_call("juju remove-machine 0 --no-prompt".split()) == 0  # noqa
    juju_wait_until_complete()
