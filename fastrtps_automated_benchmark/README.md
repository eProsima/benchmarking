# Fast-RTPS Automated Benchmark

This directory provides utilities to test the performance of Fast-RTPS across different versions, generating an isolated testing environment to maximize the results' repeatability.
The main goal is to ease the deployment and execution of performance test runs, generating reports that can be shared and used to evaluate Fast-RTPS' performance from various angles.

* [Disclaimer](#disclaimer)
* [Getting Started](#getting-started)
    * [Running Latency Tests](#running-latency-tests)
    * [Running Throughput Tests](#running-throughput-tests)
* [CI integration](#ci-integration)
* [Testing environment](#testing-environment)
* [Directory Structure](#directory-structure)

## Disclaimer

* Even though these utilities have been developed for `Ubuntu 18.04`, other `Ubuntu` versions are expected to work.
* Working with other Linux distributions might entail modifications on the [`setup_fastrtps_performance_testing.bash`](setup_fastrtps_performance_testing.bash) script, mainly because `apt` is used to installed necessary packages, specifically:

    * `curl`
    * `gnupg2`
    * `lsb-release`
    * `python3`
    * `python3-pip`
    * `python3-venv`
    * `python3-colcon-common-extensions`
    * `python3-vcstool`
    * `wget`
    * `libssl-dev`
    * `cmake`

* The scripts are written for python 3.6.9 and do NOT work with 3.7 or >. If 3.6 is not the default python in your system the use of `pyenv` to manage several python installations in the same machine is recomended.
    Furthermore, `pip3` is used to install module `virtualenv`.
    If the previous packages are already installed, all the `apt` and `pip3` related commands can simply be commented out.

* These utilities are not expected to work in any non-linux operating system.

## Getting Started

Start testing Fast-RTPS performance in your machine is rather easy. Just run:

Set up the `colcon` repository and `python3` environment:
```bash
git clone https://gitlab.intranet.eprosima.com/eProsima/fastrtps-performance-tests-env.git
bash fastrtps-performance-tests-env/eprosima/setup_fastrtps_performance_testing.bash \
    -c fastrtps_performance \
    -b 1.9.x \
    -p fastrtps_performance/fastrtps_performance_python3_env
```

### Running Latency Tests
Extrapolate requirements for your machine
```bash
bash fastrtps-performance-tests-env/eprosima/latency/latency_extrapolate_requirements.bash \
    -c fastrtps_performance/fastrtps_performance_ws \
    -o fastrtps_performance/requirements.csv \
    -r fastrtps_performance/runs_for_requirements \
    -e fastrtps_performance/fastrtps_performance_python3_env
```

Run an experiment
```bash
bash fastrtps-performance-tests-env/eprosima/latency/latency_job.bash \
    -c fastrtps_performance/fastrtps_performance_ws \
    -d fastrtps_performance/latency_results_db \
    -r fastrtps_performance/requirements.csv \
    -e fastrtps_performance/fastrtps_performance_python3_env
```

Afterwards, you can find the results of your experiment in `fastrtps_performance/latency_results_db`.

For further information on the Latency Performance Test operation, refer to [latency](latency).

### Running Throughput Tests
Extrapolate requirements for your machine (this may take a long while, since 5 runs are performed).
```bash
bash fastrtps-performance-tests-env/eprosima/throughput/throughput_extrapolate_requirements.bash \
    -c fastrtps_performance/fastrtps_performance_ws \
    -o fastrtps_performance/requirements.csv \
    -r fastrtps_performance/runs_for_requirements \
    -e fastrtps_performance/fastrtps_performance_python3_env
```

You can extrapolate for any number of runs (defaults to 5) using the `-n` option.

Run an experiment
```bash
bash fastrtps-performance-tests-env/eprosima/throughput/throughput_job.bash \
    -c fastrtps_performance/fastrtps_performance_ws \
    -d fastrtps_performance/throughput_results_db \
    -r fastrtps_performance/requirements.csv \
    -e fastrtps_performance/fastrtps_performance_python3_env
```

Afterwards, you can find the results of your experiment in `fastrtps_performance/throughput_results_db`.

For further information on the Throughput Performance Test operation, refer to [throughput](throughput).

## CI integration

Integrating the Fast-RTPS Automated Benchmark Framework is as easy as:

1. Setting a testing environment in you testing machine (see section [Getting Started](#getting-started)).
1. Creating a CI job that:
    1. Builds Fast-RTPS using colcon.
    1. Executes the job scripts ([latency_job.bash](latency/latency_job.bash), [throughput_job.bash](throughput/throughput_job.bash)).
    1. Presents the results in the manner of your choosing. At eProsima, we use Jenkins' plugin [Image Gallery](https://plugins.jenkins.io/image-gallery/) (see an example of our [Latency Job](http://jenkins.eprosima.com:8080/view/Performance/job/FastRTPS_latency_performance/80/)).

## Testing environment
The machine running the experiments is a PowerEdge R330 e34s running Ubuntu 18.04.2 LTS bionic over both Linux 4.15.0-64-generic and RT-Linux 4.14.115-rt59 kernels.
The specifications of the machines are:

* Architecture: x86_64
* CPU(s): 8
* Thread(s) per core: 2
* Model name: Intel(R) Xeon(R) CPU E3-1230 v6 @ 3.50GHz

## Directory Structure

* [colcon.meta](colcon.meta): File to configure Fast-RTPS build (with colcon).
* [latency](latency): Utilities for latency performance testing.
* [throughput](throughput): Utilities for throughput performance testing.
* [remove_old_executions.bash](remove_old_executions.bash) is a script to clean a performance results directory from old builds.
* [setup_fastrtps_performance_testing.bash](setup_fastrtps_performance_testing.bash) is a script to automatically set your Fast-RTPS performance testing environment.

Note: All the `bash` and `python` scripts can be run with `-h` to get advance usage description.
