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
    echo "Script run Fast-RTPS latency experiments."
    echo ""
    echo "Run a certain number of latency experiments using 'latency_run_experiment.bash', process"
    echo "their results with 'latency_process_results.py', and create a requirements CSV file with"
    echo "'latency_determine_requirements.py'"
    echo "------------------------------------------------------------------------"
    echo "REQUIRED ARGUMENTS:"
    echo "   -c [directory] The colcon worksapce root directory"
    echo ""
    echo "OPTIONAL ARGUMENTS:"
    echo "   -h             Print help"
    echo "   -r [directory] The directory to store the results [Defaults: ./runs_for_requirements]"
    echo "   -n [number]    Number of runs to exptrapolate requirements [Defaults: 5]"
    echo "   -o [filename]  The name of the file to store requirements [Defaults: requirements.csv]"
    echo "   -e [directory] The python3 virtual environment directory [Defaults: ../fastrtps_performance_python3_env]"
    echo ""
    echo "EXAMPLE: bash latency_extrapolate_requirements.bash \\"
    echo "             -c <colcon_ws> \\"
    echo "             -r <some_dir> \\"
    echo "             -n <number> \\"
    echo "             -o <some_filename> \\"
    echo "             -e <some_dir>"
    echo ""
    exit ${1}
}

parse_options()
{
    if (($# == 0))
    then
        print_usage 1
    fi

    RUN_DIR=$(pwd)
    SCRITP_DIR=$(scripts_directory ${@})
    COLCON_WS=""
    RUNS_DIR="${RUN_DIR}/runs_for_requirements"
    NUMBER_OF_RUNS=5
    REQUIREMENTS_FILE="${RUN_DIR}/requirements.csv"
    PYTHON_ENV="${RUN_DIR}/../fastrtps_performance_python3_env"

    while getopts ':c:r:n:o:e:h' flag
    do
        case "${flag}" in
            # Mandatory args
            c ) COLCON_WS=${OPTARG};;
            # Optional args
            h ) print_usage;;
            r ) RUNS_DIR=${OPTARG};;
            n ) NUMBER_OF_RUNS=${OPTARG};;
            o ) REQUIREMENTS_FILE=${OPTARG};;
            e ) PYTHON_ENV=${OPTARG};;
            # Wrong args
            \?) echo "Unknown option: -$OPTARG" >&2; print_usage;;
            : ) echo "Missing option argument for -$OPTARG" >&2; print_usage;;
            * ) echo "Unimplemented option: -$OPTARG" >&2; print_usage;;
        esac
    done

    if [[ ${COLCON_WS} == "" ]]
    then
        echo "No colcon_ws directory provided"
        print_usage 1
    fi

    COLCON_WS=$(full_path ${COLCON_WS})
    if [[ ! -d "${COLCON_WS}" ]]
    then
        echo "-c must specify an existing directory"
        print_usage 1
    fi

    if [[ ${PYTHON_ENV} == "" ]]
    then
        echo "No python environment directory provided"
        print_usage 1
    fi

    PYTHON_ENV=$(full_path ${PYTHON_ENV})
    PYTHON_3=${PYTHON_ENV}/bin/python3
    if [[ ! -f ${PYTHON_3} ]]
    then
        echo "${PYTHON_3} NOT found"
        print_usage 1
    fi

    if [[ ! -d "${RUNS_DIR}" ]]
    then
        mkdir -p ${RUNS_DIR}
    fi

    if [[ "${NUMBER_OF_RUNS}" -lt "0" ]]
    then
        echo "Number of runs must be positive"
        print_usage 1
    fi

    if [[ ${REQUIREMENTS_FILE} == "" ]]
    then
        echo "Invalid empty requirements file"
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
    RUNS_DIR=$(full_path ${RUNS_DIR})

    for (( i=0; i<${NUMBER_OF_RUNS}; i++ ))
    do
        TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
        RESULTS_DIR=${RUNS_DIR}/${TIMESTAMP}

        # Run experiment
        bash ${SCRITP_DIR}/latency_run_experiment.bash \
            -c ${COLCON_WS} \
            -r ${RESULTS_DIR}
        EXIT_CODE=$?
        if [ $EXIT_CODE -ne 0 ]; then
            exit $EXIT_CODE
        fi
        echo "-------------------------------------------------------------------"

        # Create plots and summary of experiment results
        rm ${RESULTS_DIR}/*summary* &> /dev/null
        DATA_FILES=($(ls ${RESULTS_DIR} -I plots))
        for FILE in ${DATA_FILES[@]}
        do
            # Get filename without extension
            IFS='.' read -r -a FILE <<< "${FILE}"
            FILE=${FILE[-2]}
            echo "Generating plots for ${FILE}..."

            # Create plots and summary
            ${PYTHON_3} ${SCRITP_DIR}/latency_process_results.py \
                --plots_directory ${RESULTS_DIR}/plots/${FILE} \
                --raw_csv ${RESULTS_DIR}/${FILE}.csv \
                --output_csv ${RESULTS_DIR}/${FILE}_summary.csv
            echo "-------------------------------------------------------------------"
        done
    done

    # Determine requirements
    echo "Determining requirements..."
    ${PYTHON_3} ${SCRITP_DIR}/latency_determine_requirements.py \
        --experiments_results ${RUNS_DIR} \
        --output_file ${REQUIREMENTS_FILE}
    EXIT_CODE=$?
    echo "-------------------------------------------------------------------"

    exit ${EXIT_CODE}
}

main ${@}
