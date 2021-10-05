# RMW Report 2021 utilities

This project contains utilities to run and analyze the experiments performed by eProsima to elaborate a report for the ROS 2 Humble default RMW implementation selection as specified by [Default DDS provider template](https://osrf.github.io/TSC-RMW-Reports/humble/dds_provider_question_template.html).

## Setup testing environment

The experiments should be conducted in an isolated environment.
That means:
1. Create a LAN without internet access to which the testing devices are exclusively connected (they are not connected to any other network).
1. To easy the process of conducting the experiments, it is convenient to have a "gateway" machine which is connected to the testing LAN, as well as a normal LAN, so that the testing machines can be accessed from outside the testing LAN with 2 ssh connections (to the gateway machine, and from there to the testing device).
This is very useful when conducting inter-host tests, since the gateway can act as an orchestrator.
1. It is ideal to down the WiFi interfaces for the experiments that do not use it, i.e. all except the inter-host with WiFi experiments.
This way, there is a less noise as possible in the testing devices.

At eProsima, we have selected RPi4 model B with Ubuntu 20.04 as OS for executing the Ubuntu experiments.

## Initialize a ROS 2 workspace

The template sets exact commits for building ROS 2 from source and performed the experiments.
To set up the workspace and build ROS 2 in an easy manner run:

```bash
bash init_workspace.bash -d <directory_for_ws>
```

## Configure and run the experiments

The experiments are run with:

```bash
python3 run_experiments.py -c <config_file> -r
```

Where `<config_file>` should be a JSON file following the schema of `rmw_report_2021_config.json`

