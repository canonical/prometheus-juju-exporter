"""Logging helper functions."""
from __future__ import absolute_import

import logging


def get_logger(debug=False):
    logger = logging.getLogger(name="prometheus-juju-exporter")
    logger.setLevel("DEBUG" if debug else "INFO")

    if not logger.handlers:
        console = logging.StreamHandler()
        console.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s - %(message)s")
        )
        logger.addHandler(console)

    return logger
