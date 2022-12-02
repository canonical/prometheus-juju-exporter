"""Set up prometheus_juju_exporter python module cli scripts."""

from setuptools import setup

with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license = f.read()

setup(
    name="prometheus_juju_exporter",
    use_scm_version={"local_scheme": "node-and-date"},
    description="collects and exports juju machine status metrics",
    long_description=readme,
    author="Canonical BootStack DevOps Centres",
    url="https://github.com/canonical/prometheus-juju-exporter",
    license=license,
    packages=["prometheus_juju_exporter"],
    package_data={"prometheus_juju_exporter": ["config_default.yaml"]},
    entry_points={
        "console_scripts": [
            "prometheus-juju-exporter=prometheus_juju_exporter.cli:main",
        ]
    },
    setup_requires=["setuptools_scm"],
)
