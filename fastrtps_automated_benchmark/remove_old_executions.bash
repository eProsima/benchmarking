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
    echo "Scritp to remove old results from a performance test dabatase."
    echo "------------------------------------------------------------------------"
    echo "REQUIRED ARGUMENTS:"
    echo "   -r [directory]   The directory for the experiments' results"
    echo ""
    echo "OPTIONAL ARGUMENTS:"
    echo "   -h               Print help"
    echo "   -n [number]      The number of old builds to keep [Defaults: 10]"
    echo "   -s [directories] Colon-separated list of directory results to keep no matter how old"
    echo ""
    echo "EXAMPLE: bash remove_old_executions.bash \\"
    echo "             -r <path_to_results> \\"
    echo "             -n 5 \\"
    echo "             -s <path_1>:<path_2>"
    echo ""
    echo "Note 1: If a directory specified with '-s' is older than the '-n' newer ones, then only"
    echo "        '-n'-1 newer directories are kept. This means that if '-n' is equal to the"
    echo "        number of directories in '-s', and those are all older than the '-n' newer ones,"
    echo "        then only the directories in '-s' are kept."
    echo ""
    echo "Note 2: If the number of directories specified with '-s' is larger than the one specified"
    echo "        with -n, then no directories are deleted."
    exit ${1}
}

parse_options()
{
    if (($# == 0))
    then
        print_usage 1
    fi

    RUN_DIR=$(pwd)
    EXPERIMENTS_RESULTS_DIR=""
    MUST_KEEP=10
    SKIP=""

    while getopts ':r:n:s:h' flag
    do
        case "${flag}" in
            # Mandatory args
            r ) EXPERIMENTS_RESULTS_DIR=${OPTARG};;
            # Optional args
            h ) print_usage 0;;
            n ) MUST_KEEP=${OPTARG};;
            s ) SKIP=${OPTARG};;
            # Wrong args
            \?) echo "Unknown option: -$OPTARG" >&2; print_usage 1;;
            : ) echo "Missing option argument for -$OPTARG" >&2; print_usage 1;;
            * ) echo "Unimplemented option: -$OPTARG" >&2; print_usage 1;;
        esac
    done

    IFS=':' read -r -a SKIP <<< "${SKIP}"
    for DIRECTORY in ${SKIP[@]}
    do
        if [[ ! -d ${DIRECTORY} ]]
        then
            echo "Path ${DIRECTORY} does not specify a directory"
            print_usage 1
        fi
    done

    if [[ ${EXPERIMENTS_RESULTS_DIR} == "" ]]
    then
        echo "No experiments results directory provided"
        print_usage 1
    fi

    if [ "${MUST_KEEP}" -lt "0" ]
    then
        echo "-n must specify a positive number"
        print_usage 1
    fi
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

    # Full path of EXPERIMENTS_RESULTS_DIR
    EXPERIMENTS_RESULTS_DIR=$(full_path ${EXPERIMENTS_RESULTS_DIR})

    # Add the skip list to the results to keep
    KEPT_RESULTS=()
    for ELEMENT in ${SKIP[@]}
    do
        IFS='/' read -r -a ELEMENT <<< "${ELEMENT}"
        KEPT_RESULTS+=(${ELEMENT[-1]})
    done

    # Get all executions
    EXECUTIONS=($(ls -tr ${EXPERIMENTS_RESULTS_DIR}))

    # If enough executions in list, then check if need to delete some
    if [[ ${#EXECUTIONS[@]} -gt ${#KEPT_RESULTS[@]} ]]
    then
        # Calculate how many builds to keep
        MUST_KEEP=$((${MUST_KEEP}-${#KEPT_RESULTS[@]}))

        # Check if can keep more than the skip list
        if [ ${MUST_KEEP} -gt 0 ]
        then
            # Skip directories in ${SKIP} when listing
            SKIP_ARGS=""
            for ELEMENT in ${SKIP[@]}
            do
                IFS='/' read -r -a ELEMENT <<< "${ELEMENT}"
                SKIP_ARGS="${SKIP_ARGS} -I ${ELEMENT[-1]}"
            done

            # Get a list of executions without the skipped ones
            FILTERED_BUILD=($(ls -tr ${EXPERIMENTS_RESULTS_DIR} ${SKIP_ARGS}))

            # Keep the newer ones until keep limit is reached
            for (( i=${#FILTERED_BUILD[@]}; i>=0; i-- ))
            do
                KEPT_RESULTS+=(${FILTERED_BUILD[${i}]})
                MUST_KEEP=$((${MUST_KEEP}-1))

                if [ ${MUST_KEEP} -lt 0 ]
                then
                    break
                fi
            done
        fi

        # Add to REMOVED list the executions that are not to be kept
        REMOVED=()
        for EXECUTION in ${EXECUTIONS[@]}
        do
            # Check if EXECUTION is in the KEPT_RESULTS list
            KEEP_EXECUTION="FALSE"
            for KEPT in ${KEPT_RESULTS[@]}
            do
                if [ "${EXECUTION}" == "${KEPT}" ]
                then
                    # EXECUTION is in the KEPT_RESULTS list
                    KEEP_EXECUTION="TRUE"
                    break
                fi
            done
            # ADD EXECUTION to REMOVED if it is not in the KEPT_RESULTS list
            if [[ ${KEEP_EXECUTION} == "FALSE" ]]
            then
                REMOVED+=(${EXECUTION})
            fi
        done

        # Pretty output for user
        echo "${#EXECUTIONS[@]} executions detected in database. Keeping ${#KEPT_RESULTS[@]}, removing ${#REMOVED[@]}"
        echo "-------------------------------------------------------------------"
        for EXECUTION in ${KEPT_RESULTS[@]}
        do
            echo "Keeping ${EXECUTION}"
        done

        echo "-------------------------------------------------------------------"
        for EXECUTION in ${REMOVED[@]}
        do
            echo "Removing ${EXECUTION}"
            # Actual removal
            rm -rf ${EXPERIMENTS_RESULTS_DIR}/${EXECUTION}
        done
    fi
}

main ${@}
