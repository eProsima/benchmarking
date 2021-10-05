#!/bin/bash

# Copyright 2021 Proyectos y Sistemas de Mantenimiento SL (eProsima).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

print_usage()
{
    echo "------------------------------------------------------------------------"
    echo "Scritp to init the workspace for RMW report 2021."
    echo "------------------------------------------------------------------------"
    echo "OPTIONAL ARGUMENTS:"
    echo "   -h                 Print help"
    echo "   -d [directory]     The directory where the workspace should be created"
    echo "                      [Defaults: ./rmw_report_ws]"
    echo ""
    echo "EXAMPLE: bash init_workspace -d temp/report_ws"
    exit ${1}
}

parse_options()
{
    EXECUTION_DIR=$(pwd)
    WS_DIR="${EXECUTION_DIR}/rmw_report_ws"

    while getopts ':d:h' flag
    do
        case "${flag}" in
            # Mandatory args
            h ) print_usage 0;;
            d ) WS_DIR=${OPTARG};;
            # Wrong args
            \?) echo "Unknown option: -$OPTARG" >&2; print_usage 1;;
            : ) echo "Missing option argument for -$OPTARG" >&2; print_usage 1;;
            * ) echo "Unimplemented option: -$OPTARG" >&2; print_usage 1;;
        esac
    done

    if [[ ! -d ${WS_DIR} ]]
    then
        mkdir -p ${WS_DIR}
    fi
}

main()
{
    parse_options ${@}

    # Install ROS 2 dependencies
    sudo apt update && sudo apt install -y curl gnupg lsb-release
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key  -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
    sudo apt update && sudo apt install -y \
        build-essential \
        cmake \
        git \
        python3-colcon-common-extensions \
        python3-flake8 \
        python3-pip \
        python3-pytest-cov \
        python3-rosdep \
        python3-setuptools \
        python3-vcstool \
        wget
    python3 -m pip install -U \
        flake8-blind-except \
        flake8-builtins \
        flake8-class-newline \
        flake8-comprehensions \
        flake8-deprecated \
        flake8-docstrings \
        flake8-import-order \
        flake8-quotes \
        pytest-repeat \
        pytest-rerunfailures \
        pytest \
        setuptools

    # Create workspace
    mkdir -p ${WS_DIR}/src
    cd ${WS_DIR}
    wget https://raw.githubusercontent.com/osrf/TSC-RMW-Reports/main/humble/ros2.repos
    vcs import src < ros2.repos
    cd src
    git clone https://gitlab.com/ApexAI/performance_test.git
    cd performance_test
    git remote add company https://gitlab.com/MiguelCompany/performance_test
    git fetch company
    git checkout c230727  # HEAD of feature/build-on-windows
    cd ../../

    # Download dependencies
    sudo rosdep init
    rosdep update
    rosdep install --from-paths src --ignore-src --rosdistro rolling -y --skip-keys "console_bridge fastcdr fastrtps rti-connext-dds-5.3.1 urdfdom_headers"

    # Build
    colcon build --packages-up-to performance_test ros2cli_common_extensions --merge-install --cmake-args -DSECURITY=ON
}

main ${@}
