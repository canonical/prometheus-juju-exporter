# Prometheus Juju Exporter

prometheus-juju-exporter snap collects machines' running status in all models under a Juju controller. It also provides an interface to expose the metrics to Prometheus for storage and further usage.

## Deployment
To get the latest stable version of the snap from Snapstore, run:
```bash
sudo snap install prometheus-juju-exporter
```
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

