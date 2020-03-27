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
    echo "Scritp to run Fast-RTPS latency performance tests, plot results, and check against a set"
    echo "of requirements."
    echo ""
    echo "1. Run a latency experiment with 'latency_run_experiment.bash'."
    echo "2. Process results and create summaries with 'latency_process_results.py'."
    echo "3. Clean database form old experiments with 'remove_old_executions.bash'."
    echo "4. Check results against requirements with 'latency_check_experiment.py'."
    echo "5. Update database history plots with 'latency_plot_history.py'."
    echo "------------------------------------------------------------------------"
    echo "REQUIRED ARGUMENTS:"
    echo "   -c [directory] The colcon worksapce root directory"
    echo ""
    echo "OPTIONAL ARGUMENTS:"
    echo "   -h             Print help"
    echo "   -d [directory] The directory for the results' database [Defaults: ./latency_results_db]"
    echo "   -D [number]    The history depth (maximum executions in the database) [Defaults: 10]"
    echo "   -r [filename]  A requirements file. [Defaults: ./requirements.csv]"
    echo "   -l [string]    A string to name the experiment results' directory [Defaults: YYYY-MM-DD_hh-mm-ss]"
    echo "   -e [directory] The python3 virtual environment directory [Defaults: ../fastrtps_performance_python3_env]"
    echo ""
    echo "EXAMPLE: bash latency_job.bash \\"
    echo "             -c <colcon_ws> \\"
    echo "             -d <database_directory> \\"
    echo "             -D <database_depth> \\"
    echo "             -r <requirements_filename> \\"
    echo "             -l <experiment_name> \\"
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
    DATABASE_DIR="${RUN_DIR}/latency_results_db"
    HISTORY_DEPTH=10
    REQUIREMENTS="${RUN_DIR}/requirements.csv"
    LOG_DIR_NAME=""
    PYTHON_ENV="${RUN_DIR}/../fastrtps_performance_python3_env"

    while getopts ':c:d:D:r:l:e:h' flag
    do
        case "${flag}" in
            # Mandatory args
            c ) COLCON_WS=${OPTARG};;
            # Optional args
            h ) print_usage 0;;
            d ) DATABASE_DIR=${OPTARG};;
            D ) HISTORY_DEPTH=${OPTARG};;
            r ) REQUIREMENTS=${OPTARG};;
            l ) LOG_DIR_NAME=${OPTARG};;
            e ) PYTHON_ENV=${OPTARG};;
            # Wrong args
            \?) echo "Unknown option: -$OPTARG" >&2; print_usage 1;;
            : ) echo "Missing option argument for -$OPTARG" >&2; print_usage 1;;
            * ) echo "Unimplemented option: -$OPTARG" >&2; print_usage 1;;
        esac
    done

    if [[ ${COLCON_WS} == "" ]]
    then
        echo "-------------------------------------------------------------------"
        echo "No colcon_ws directory provided"
        print_usage 1
    fi

    if [[ ! -d "${COLCON_WS}" ]]
    then
        echo "-------------------------------------------------------------------"
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

    if [[ ! -d "${DATABASE_DIR}" ]]
    then
        mkdir -p ${DATABASE_DIR}
    fi

    if [[ "${HISTORY_DEPTH}" -lt "0" ]]
    then
        echo "-------------------------------------------------------------------"
        echo "-D must specify a positive number"
        print_usage 1
    fi

    if [[ ! -f ${REQUIREMENTS} ]]
    then
        echo "-------------------------------------------------------------------"
        echo "Requirements file ${REQUIREMENTS} NOT found"
        print_usage 1
    fi

    if [[ ${LOG_DIR_NAME} == "" ]]
    then
        LOG_DIR_NAME=$(date '+%Y-%m-%d_%H-%M-%S')
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
    EXIT_CODE=0

    # Full paths
    cd ${RUN_DIR}
    COLCON_WS=$(full_path ${COLCON_WS})
    DATABASE_DIR=$(full_path ${DATABASE_DIR})
    EXPERIMENTS_RESULTS_DIR=${DATABASE_DIR}/experiments_results
    RESULTS_DIR=${EXPERIMENTS_RESULTS_DIR}/${LOG_DIR_NAME}
    HISTORY_PLOTS_DIR=${DATABASE_DIR}/history_plots

    echo "-------------------------------------------------------------------"
    echo "COLCON_WS:           ${COLCON_WS}"
    echo "DATABASE:            ${DATABASE_DIR}"
    echo "EXPERIMENTS_RESULTS: ${EXPERIMENTS_RESULTS_DIR}"
    echo "EXPERIMENTS_RESULTS: ${RESULTS_DIR}"
    echo "HISTORY_PLOTS_DIR:   ${HISTORY_PLOTS_DIR}"
    echo "REQUIREMENTS:        ${REQUIREMENTS}"
    echo "PYTHON_ENVIRONMENT:  ${PYTHON_ENV}"
    echo "-------------------------------------------------------------------"

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
    SUMMARIES=""
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

        # Add summary to list
        SUMMARIES="${SUMMARIES} ${RESULTS_DIR}/${FILE}_summary.csv"
        echo "-------------------------------------------------------------------"
    done

    # Create comparison plots
    echo "Creating sub-experiment comparison plots"
    ${PYTHON_3} ${SCRITP_DIR}/latency_compare_subexperiments.py \
            --plots_directory ${RESULTS_DIR}/plots/ \
            --subexperiment_summaries ${SUMMARIES}
    echo "-------------------------------------------------------------------"

    # Clean database
    bash ${SCRITP_DIR}/../remove_old_executions.bash \
        -r ${EXPERIMENTS_RESULTS_DIR} \
        -n ${HISTORY_DEPTH} \
        -s ${REFERENCE_DIR}:${RESULTS_DIR}
    echo "-------------------------------------------------------------------"

    # Check results against the requirements
    echo "Checking experiment results against requirements..."
    ${PYTHON_3} ${SCRITP_DIR}/latency_check_experiment.py \
        --requirements ${REQUIREMENTS} \
        --experiment_directory ${RESULTS_DIR} \
        --plots_directory ${RESULTS_DIR}/plots \
        --print_summaries
    EXIT_CODE=$?
    echo "-------------------------------------------------------------------"

    # Update history plots
    echo "Updating history plots..."
    ${PYTHON_3} ${SCRITP_DIR}/latency_plot_history.py \
        --requirements ${REQUIREMENTS} \
        --experiments_results ${EXPERIMENTS_RESULTS_DIR} \
        --plots_directory ${HISTORY_PLOTS_DIR}
    echo "-------------------------------------------------------------------"

    echo "Result: ${EXIT_CODE} checks failed"
    exit $EXIT_CODE
}

main ${@}
