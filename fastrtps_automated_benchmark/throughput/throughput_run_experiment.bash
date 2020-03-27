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
    echo "Scritp run Fast-RTPS throughput experiments."
    echo ""
    echo "Run Fast-RTPS throughput tests using colcon and c-test, then move the results to the"
    echo "direcory specified with -r. In the end, the script runs:"
    echo "colcon test --packages-select fastrtps --ctest-args -R performance.throughput"
    echo "------------------------------------------------------------------------"
    echo "REQUIRED ARGUMENTS:"
    echo "   -c [directory] The colcon worksapce root directory"
    echo ""
    echo "OPTIONAL ARGUMENTS:"
    echo "   -h             Print help"
    echo "   -r [directory] The directory to store the results [Defaults: ./results]"
    echo "   -d [file]      A throughput demands CSV file."
    echo "   -t [file]      A throughtput recoveries CSV file"
    echo ""
    exit 0
}

parse_options()
{
    if (($# == 0))
    then
        print_usage
    fi

    RUN_DIR=$(pwd)
    COLCON_WS=""
    RESULTS_DIR="${RUN_DIR}/results"
    DEMANDS=""
    RECOVERIES=""

    while getopts ':c:r:d:t:h' flag
    do
        case "${flag}" in
            # Mandatory args
            c ) COLCON_WS=${OPTARG};;
            # Optional args
            h ) print_usage;;
            r ) RESULTS_DIR=${OPTARG};;
            d ) DEMANDS=${OPTARG};;
            t ) RECOVERIES=${OPTARG};;
            # Wrong args
            \?) echo "Unknown option: -$OPTARG" >&2; print_usage;;
            : ) echo "Missing option argument for -$OPTARG" >&2; print_usage;;
            * ) echo "Unimplemented option: -$OPTARG" >&2; print_usage;;
        esac
    done

    if [[ ${COLCON_WS} == "" ]]
    then
        echo "No colcon_ws directory provided"
        print_usage
    fi

    if [[ ! -d "${COLCON_WS}" ]]
    then
        echo "-c must specify an existing directory"
        print_usage
    fi

    if [[ ! -d "${RESULTS_DIR}" ]]
    then
        mkdir -p ${RESULTS_DIR}
    fi

    if [ ${DEMANDS} != "" ] && [ ! -f ${DEMANDS} ]
    then
        echo "${DEMANDS} does not specify a file"
    fi

    if [ ${RECOVERIES} != "" ] && [ ! -f ${RECOVERIES} ]
    then
        echo "${RECOVERIES} does not specify a file"
    fi
}

main ()
{
    parse_options ${@}

    # Full path of colcon_ws dir
    cd ${COLCON_WS}
    COLCON_WS=$(pwd)

    # Source colcon workspace
    echo "Sourcing environment..."
    source ${COLCON_WS}/install/local_setup.bash
    echo "-------------------------------------------------------------------"

    # Clean old executions
    rm -r ${COLCON_WS}/build/fastrtps/test/performance/throughput/measurements_* &> /dev/null

    # Configuring demands and recoveries
    if [[ ${DEMANDS} != "" ]]
    then
        cp ${DEMANDS} ${COLCON_WS}/src/fastrtps/test/performance/throughput/payloads_demands.csv
    fi

    if [[ ${RECOVERIES} != "" ]]
    then
        cp ${RECOVERIES} ${COLCON_WS}/src/fastrtps/test/performance/throughput/recoveries.csv
    fi

    # Run tests
    echo "Runing tests..."
    colcon test \
        --event-handlers console_direct+ \
        --packages-select fastrtps \
        --ctest-args -R performance.throughput \
        --timeout 3600
    EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        exit $EXIT_CODE
    fi
    echo "-------------------------------------------------------------------"

    # Copy results to database
    echo "Moving results to database..."
    mv ${COLCON_WS}/build/fastrtps/test/performance/throughput/measurements_* ${RESULTS_DIR}
    EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        exit $EXIT_CODE
    fi
}

main ${@}
