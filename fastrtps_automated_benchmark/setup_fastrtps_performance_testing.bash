#!/bin/bash

# Copyright 2019 Proyectos y Sistemas de Mantenimiento SL (eProsima).
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
    echo "Scritp to setup Fast-RTPS performance testing environment."
    echo "------------------------------------------------------------------------"
    echo "OPTIONAL ARGUMENTS:"
    echo "   -h             Print help"
    echo "   -c [directory] The directory to place the Fast-RTPS colcon worksapce [Defaults: ./]"
    echo "   -b [branch]    The Fast-RTPS branch to use [Defaults: master]"
    echo "   -p [directory] The directory to initialize the python3 virtual environment"
    echo "                  [Defaults: ./fastrtps_performance_python3_env]"
    echo ""
    exit ${1}
}

parse_options()
{
    RUN_DIR=$(pwd)
    COLCON_WS="${RUN_DIR}"
    FASTRTPS_BRANCH="master"
    PYTHON_ENV=${RUN_DIR}/fastrtps_performance_python3_env
    SCRITP_DIR=$(scripts_directory ${@})

    while getopts ':c:b:p:h' flag
    do
        case "${flag}" in
            # Optional args
            h ) print_usage 0;;
            c ) COLCON_WS=${OPTARG};;
            b ) FASTRTPS_BRANCH=${OPTARG};;
            p ) PYTHON_ENV=${OPTARG};;
            # Wrong args
            \?) echo "Unknown option: -$OPTARG" >&2; print_usage 1;;
            : ) echo "Missing option argument for -$OPTARG" >&2; print_usage 1;;
            * ) echo "Unimplemented option: -$OPTARG" >&2; print_usage 1;;
        esac
    done

    COLCON_WS=${COLCON_WS}/fastrtps_performance_ws
    if [[ -d ${COLCON_WS} ]]
    then
        echo "Directory ${COLCON_WS} already exists."
        print_usage 1
    fi
}

scripts_directory ()
{
    local DIR=${0}
    IFS='/' read -r -a DIR <<< "${DIR}"
    if [[ ${#DIR[@]} -gt 0 ]]
    then
        local TEMP=""
        if [[ "${0}" != /* ]] && [[ "${0}" != ~/* ]]
        then
            local TEMP="${RUN_DIR}"
        fi

        unset 'DIR[${#DIR[@]}-1]'
        for ELEMENT in ${DIR[@]}
        do
            TEMP="${TEMP}/${ELEMENT}"
        done

        DIR=${TEMP}
    else
        DIR=${RUN_DIR}
    fi

    if [[ "${0}" != /* ]] && [[ "${0}" != ~/* ]]
    then
        DIR=$(full_path ${DIR})
    fi
    echo "${DIR}"
}

full_path ()
{
    local CURRENT=$(pwd)
    cd -P ${1}
    local FULL_PATH=$(pwd)
    echo ${FULL_PATH}
    cd ${CURRENT}
}

main ()
{
    parse_options ${@}

    echo "Installing dependencies..."
    sudo apt update
    sudo apt install \
        curl \
        gnupg2 \
        lsb-release
    curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
    sudo sh -c 'echo "deb [arch=amd64,arm64] http://packages.ros.org/ros2/ubuntu `lsb_release -cs` main" > /etc/apt/sources.list.d/ros2-latest.list'
    sudo apt update
    sudo apt install \
        python3 \
        python3-pip \
        python3-venv \
        python3-colcon-common-extensions \
        python3-vcstool \
        wget \
        libssl-dev \
        cmake
    sudo pip3 install virtualenv
    echo "-------------------------------------------------------------------"

    echo "Creating python3 environment..."
    python3 -m venv ${PYTHON_ENV}
    ${PYTHON_ENV}/bin/pip3 install -r ${SCRITP_DIR}/python_requirements.txt
    echo "-------------------------------------------------------------------"

    echo "Creating workspace ${COLCON_WS}"
    mkdir -p ${COLCON_WS}
    COLCON_WS=$(full_path ${COLCON_WS})
    cp ${SCRITP_DIR}/colcon.meta ${COLCON_WS}
    echo "-------------------------------------------------------------------"

    echo "Downloading Fast-RTPS source code"
    cd ${COLCON_WS}
    wget https://raw.githubusercontent.com/eProsima/Fast-RTPS/master/fastrtps.repos
    mkdir -p ${COLCON_WS}/src
    vcs import src < fastrtps.repos
    echo "-------------------------------------------------------------------"

    echo "Setting Fast-RTPS branch"
    cd ${COLCON_WS}/src/fastrtps
    git checkout ${FASTRTPS_BRANCH}
    if [[ $? != 0 ]]
    then
        echo "Could not checkout branch ${FASTRTPS_BRANCH}"
        exit 1
    fi
    echo "-------------------------------------------------------------------"

    echo "Adding external testing tools"
    cd ${COLCON_WS}/src
    git clone https://github.com/osrf/osrf_testing_tools_cpp.git
    echo "-------------------------------------------------------------------"

    echo "Building colcon workspace"
    cd ${COLCON_WS}
    colcon build
    echo "-------------------------------------------------------------------"
}

main ${@}
