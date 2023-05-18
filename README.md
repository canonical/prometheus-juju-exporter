# Prometheus Juju Exporter

prometheus-juju-exporter snap collects machines' running status in all models under a Juju controller. It also provides an interface to expose the metrics to Prometheus for storage and further usage.

## Deployment
To get the latest stable version of the snap from Snapstore, run:
```bash
sudo snap install prometheus-juju-exporter
```

To install snap from a specific channel, e.g. `2.9/stable`, use `--channel` flag:
```bash
sudo snap install prometheus-juju-exporter --channel 2.9/stable
```
**Note**: please refer to [Juju Version Compatibility](#juju-version-compatibility) to select the proper snap channel base on the version of juju controller that the snap will communicate with.

To get the latest development version of the snap, build from the source code and install with `--dangerous` flag:
```bash
make build
sudo snap install --dangerous prometheus-juju-exporter.snap
```

## Configuration
By default, prometheus-juju-exporter uses the configuration specified in [config_default.yaml](prometheus-juju-exporter/config_default.yaml). It's likely not fitting your need because the values provided are generic and for demonstration purposes only. To configure the snap for your own environment, create a `config.yaml` file in `$SNAP_DATA` (see [Snap Environment Variables](https://snapcraft.io/docs/environment-variables)) directory with the desired entries.

The snap requires juju user's credentials to connect to a controller and all of its models. The credentials are set as `juju.username` and `juju.password` config values. Normally, **`superuser`** privilege is expected for such a user for full access to the controller. However, in case it is not possible, the minimum privilege requirements are:
1. `login` access to the controller instance and `admin` access to the model hosting the controller
2. `admin` access to any model that's expected to be monitored by this exporter


## Juju Version Compatibility
Due to the limitations of Juju's cross-version support, channels and versions are used in the snap to accommodate different juju controller versions. The following table demonstrates the compatibility matrix between juju controller version, snap channel, snap version, and branch in the repository. The operator should select the proper snap channel at installation time accordingly.

| Juju Controller Version | Snap Channel                              | Repo Branch | Snap Version |
|-------------------------|-------------------------------------------|-------------|--------------|
| 2.8 and older           | 2.8/stable<br/>2.8/candidate<br/>2.8/edge | 2.8         | 1.x          |
| 2.9                     | 2.9/stable<br/>2.9/candidate<br/>2.9/edge | 2.9         | 2.x          |