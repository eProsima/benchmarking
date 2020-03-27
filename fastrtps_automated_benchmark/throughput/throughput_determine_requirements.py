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

"""."""
import argparse
import logging
from os import listdir
from os.path import abspath
from os.path import isdir
from os.path import isfile

import numpy as np

import pandas


def directory_type(directory):
    """
    Check whether the argument is a directory.

    :param directory: The directory path.
    :return: The directory path without ending /.
    Exit if the directory cannot be found.
    """
    if directory.endswith('/'):
        directory = directory[:-1]
    if not isdir(directory):
        logger.error('Cannot find {}'.format(directory))
        exit(1)
    return directory


def experiment_type(filename):
    """
    Get experiment type of a summary file based on its name.

    Get experiment type of a summary file based on its name (as output by
    "throughput_process_results.py).

    :param filename: The name of the summary file.
    :raise: AssertionError if filename is not a string.
    :return: The experiment type as a string.
    """
    assert(isinstance(filename, str))
    exp_type = filename.split('/')[-1].split('.')[-2].split('_')[1:-1]
    exp_type = '_'.join(exp_type)
    logger.debug('{} is of type {}'.format(filename, exp_type))
    return exp_type


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="""
            Script to determine throughput requirements based on a set of
            experiment results. The scripts takes an <experiment_results>
            directory and creates a CSV file with requirements for each payload
            and experiment type present. The <experiment_results> directory is
            expected to contain directories with experiment results as output
            by "throughput_run_experiment.bash", and summaries created with
            "throughput_process_results.py". Each requirement is set by the 99
            percentile of the results for a given payload and experiment type.
            The scripts generate requirement for lost samples, and subscription
            throughput.
        """
    )
    parser.add_argument(
        '-e',
        '--experiments_results',
        help='The directory containing the results of all the experiments',
        required=True
    )
    parser.add_argument(
        '-o',
        '--output_file',
        help='A file to write the requirements',
        required=False,
        default='throughput_requirements.csv'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Set logging level to debug.'
    )
    args = parser.parse_args()

    # Create a custom logger
    logger = logging.getLogger('THROUGHPUT.DETERMINE.REQUIREMENTS')
    # Create handlers
    c_handler = logging.StreamHandler()
    # Create formatters and add it to handlers
    c_format = (
        '[%(asctime)s][%(filename)s:%(lineno)s][%(funcName)s()]' +
        '[%(levelname)s] %(message)s'
    )
    c_format = logging.Formatter(c_format)
    c_handler.setFormatter(c_format)
    # Add handlers to the logger
    logger.addHandler(c_handler)
    # Set log level
    if args.debug is True:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    experiments = abspath(directory_type(args.experiments_results))
    output_file = abspath(args.output_file)

    # Validate arguments
    assert(isdir(experiments))

    logger.debug('Geting results directories')
    results_dirs = sorted(
        [
            '{}/{}'.format(
                experiments,
                d
            ) for d in listdir(experiments) if isdir(
                '{}/{}'.format(
                    experiments,
                    d
                )
            )
        ]
    )
    logger.debug(results_dirs)

    # Supported experiment types
    experiment_types = [
        'interprocess_best_effort',
        'interprocess_best_effort_shm',
        'interprocess_best_effort_security',
        'interprocess_best_effort_shm_security',
        'interprocess_best_effort_tcp',
        'interprocess_best_effort_tcp_security',
        'interprocess_reliable',
        'interprocess_reliable_shm',
        'interprocess_reliable_security',
        'interprocess_reliable_shm_security',
        'interprocess_reliable_tcp',
        'interprocess_reliable_tcp_security',
        'intraprocess_best_effort',
        'intraprocess_reliable',
    ]

    # Create a dictionary with one entry per experiment type. The values are
    # Pandas DataFrames:
    # {
    #     'experiment_type_1': <Pandas DataFrame>,
    #     'experiment_type_2': <Pandas DataFrame>
    # }
    # The DataFrames contain a "Experiment" column to keep track of from which
    # experiment does every data entry come from.
    data_by_exp_type = {}
    for results_dir in results_dirs:
        # Get path of summary files
        logger.debug('Geting summaries for {}'.format(results_dir))
        results_files = sorted(
            [
                '{}/{}'.format(
                    results_dir,
                    f
                ) for f in listdir(results_dir) if isfile(
                    '{}/{}'.format(
                        results_dir,
                        f
                    )
                ) and 'summary' in f
            ]
        )
        logger.debug('Summaries: {}'.format(results_files))

        # Iterate over the summaries
        for f in results_files:
            # Get experiment type
            exp_type = experiment_type(f)
            # Check that supported
            if exp_type not in experiment_types:
                logger.error(
                    'Experiment {} found in {} is NOT supported'.format(
                        exp_type,
                        results_dir
                    )
                )
                exit(1)
            # Initialize dictionary entry
            if exp_type not in data_by_exp_type:
                data_by_exp_type[exp_type] = pandas.DataFrame()

            # Load data as DataFrame
            logger.debug('Loading data from {}'.format(f))
            file_data = pandas.read_csv(f)
            # Expand data with a "Experiment" column containing directory name
            # of experiment results.
            file_data['Experiment'] = results_dir.split('/')[-1]
            # Append data to
            data_by_exp_type[exp_type] = data_by_exp_type[exp_type].append(
                file_data,
                sort=False
            )
    logger.debug('Data by experiment type: {}'.format(data_by_exp_type))

    # Requirement columns and percentile used to derive requirements
    req_columns = {
        'Lost [samples]': 99,
        'Subscription throughput [Mb/s]': 99,
    }

    # Derive requirements for each experiment type, payload, and req_column
    # based on the percentiles. Store them in a DataFrame in the form:
    # Experiment Payload [Bytes] Lost [samples]  Subscription throughput [Mb/s]
    # 0  interprocess_best_effort_security   16   0.00   8.62310
    # 1  interprocess_best_effort_security 1024 144.54 547.46745

    requirements = pandas.DataFrame()
    for exp_type in data_by_exp_type:
        # Get experiment_type data
        exp_data = data_by_exp_type[exp_type].reset_index(drop=True)
        exp_requirements = pandas.DataFrame()

        # Iterate over payloads
        payloads = exp_data['Payload [Bytes]'].unique()
        for payload in payloads:
            # Get payload data
            payload_data = exp_data[exp_data['Payload [Bytes]'] == payload]

            # Iterate over requirement columns
            payload_reqs = pandas.DataFrame()
            for c in req_columns:
                # Calculate percentile and insert entry
                payload_reqs.at[0, c] = np.percentile(
                    payload_data[c],
                    req_columns[c]
                )

            payload_reqs.insert(0, 'Payload [Bytes]', payload)
            exp_requirements = exp_requirements.append(payload_reqs)
        exp_requirements.insert(0, 'Experiment type', exp_type)
        requirements = requirements.append(exp_requirements)

    # Save requirements as CSV file
    requirements = requirements.reset_index(drop=True)
    requirements.to_csv(output_file, float_format='%.3f', index=False)
    # Print the requirement
    pandas.set_option('display.max_rows', None)
    logger.info('Requirements: \n{}'.format(requirements))
