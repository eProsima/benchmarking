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

"""Provides tools to compare 2 apex performance log files."""
import argparse
import csv
from datetime import datetime
import itertools
import logging
from os import listdir
from os.path import isdir, isfile
from os.path import join
import time


WORSE = 'WORSE'
SIMILAR = 'SIMILAR'
BETTER = 'BETTER'


def bool_type(string):
    """
    Check whether a string represents a boolean.

    :param string (str): Supported values are (Both lower and upper case):
            - yes, y, true, y, 1, no, n, false, f, 0.
    :return: The boolean representation of the string.
    :raise: argparse.ArgumentTypeError if the argument is not supported.
    """
    # Convert to lower case
    string = string.lower()
    true_tuple = ('yes', 'y', 'true', 't', '1')
    false_tuple = ('no', 'n', 'false', 'f', '0')

    if string not in true_tuple and string not in false_tuple:
        raise argparse.ArgumentTypeError(
            '"{}" not supported. Supported are: {} and {}'.format(
                string, true_tuple, false_tuple
            )
        )
    else:
        return string in true_tuple


def percentage_float(x):
    """
    Check whether the float is a percentage.

    :param x: The value to check
    :return: The float representation of the argument.
    :raise: argparse.ArgumentTypeError if the argument is not in [0, 100].
    """
    x = float(x)
    if x < 0 or x > 100:
        raise argparse.ArgumentTypeError('{} not in range [0, 100]'.format(x))
    return x


def directory_type(directory):
    """
    Check whether the argument is a directory.

    :param directory: The directory path.
    :return: The directory path without ending /.
    :raise: argparse.ArgumentTypeError if the argument is not a directory.
    """
    if directory.endswith('/'):
        directory = directory[:-1]
    if not isdir(directory):
        raise argparse.ArgumentTypeError(
            'Cannot find directory "{}"'.format(directory)
        )
    return directory


def file_type(f):
    """
    Check whether the argument is a file.

    :param f: The file path.
    :return: The file path.
    :raise: argparse.ArgumentTypeError if the argument is not a file.
    """
    if not isfile(f):
        raise argparse.ArgumentTypeError(
            'Cannot find file "{}"'.format(f)
        )
    return f


def get_logger(file_name=None, print_enable=True):
    """
    Get a logger with handlers for file and terminal output.

    :param file_name: A name for the log file.
        If None, comparison_<timestamp>.log is used. Defaults: None.
    :param print_enable: The return logger will also print to stdout.
    :return: A logger.
    """
    ts = time.time()
    if file_name is None:
        file_name = 'comparison_{}.log'.format(
            datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')
        )

    # Create a custom logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(file_name)
    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.INFO)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
    f_format = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    if print_enable is True:
        logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    return logger


def get_column_ids(file_name):
    """Get a list of log file column ids."""
    with open(file_name, 'r') as f:
        start_line = False
        for line in f.readlines():
            if start_line is True:
                columns_ids = line.rstrip().split(',')
                break
            if '--EXPERIMENT-START---' in line:
                start_line = True

    for i in range(0, len(columns_ids)):
        columns_ids[i] = columns_ids[i].strip()

    # These columns must be present in the log file
    columns_of_interest = [
        'latency_min (ms)',
        'latency_mean (ms)',
        'latency_max (ms)',
        'ru_maxrss',
    ]
    try:
        assert all(elem in columns_ids for elem in columns_of_interest)
    except AssertionError:
        raise AssertionError(
            'At least one column of {} is not present in file {}'.format(
                columns_of_interest,
                file_name
            )
        )
    return columns_ids


def get_subdirectories(rates, num_subs):
    """
    Get the list of expected subdirectories in every directory.

    The expected subdirectories are obtaines from the Cartesian product
    of the elements of rates and num_subs.

    :param rates (list): The sending rates
    :param num_subs (list): All the different number of subscribers.

    :return:
        A list containing the path of all the subdirectories.

    """
    # Get subdirectory names
    combinations = list(itertools.product(rates, num_subs))
    sub_dirs = []
    for combination in combinations:
        sub_dirs.append('rate_{}/subs_{}'.format(
            combination[0], combination[1])
        )
    return sub_dirs


def get_file_names(directory, sub_dirs):
    """
    Get the file name of all the files in every subdirectory of directory.

    :param directory (str): The main directory.
    :param sub_dirs (list): A list of subdirectories to look for files.

    :return: A list of file names in the form:
        'directory/subdirectory/filename'
    """
    files = {}
    for sub_dir in sub_dirs:
        dir_name = '{}/{}'.format(directory, sub_dir)

        files_l = sorted(
            f for f in listdir(dir_name) if (
                not f.endswith('parsed') and isfile(join(dir_name, f))
            )
        )
        files[sub_dir] = files_l

    files_list = []
    for sub_dir in sub_dirs:
        for f in files[sub_dir]:
            files_list.append('{}/{}/{}'.format(directory, sub_dir, f))

    return files_list


def read_file_results(file_name):
    """
    Extract the results from a test log file.

    :return: A dictionary containing the results grouped by columns
    """
    columns_ids = get_column_ids(file_name)
    results = {}
    for col in columns_ids:
        results[col] = []

    with open(file_name, 'r') as f:
        csv_reader = csv.DictReader(f, delimiter=',',
                                    fieldnames=columns_ids)
        line_count = 0
        experiment_start = False
        for row in csv_reader:
            # Experiment NOT started
            if not experiment_start:
                if '--EXPERIMENT-START---' not in row[columns_ids[0]]:
                    continue
                else:
                    experiment_start = True
            # Experiment started
            else:
                if line_count > 0:
                    for col in columns_ids:
                        try:
                            results[col].append(float(row[col]))
                        except:
                            results[col].append(row[col])
                line_count += 1
    return results


def calculate_jitter(latencies):
    """
    Calculate the jitter of a set of latencies.

    :param latencies (list): The set of latencies

    :return: A list containing the jitters
    """
    jitter = []
    prev_i = 0
    first = True
    for i in latencies:
        if first:
            first = False
        else:
            jitter.append(abs(i - prev_i))
        prev_i = i
    return jitter


def compare_measurements(
        reference,
        target,
        threshold,
    ):
    """."""
    result = {}
    result['reference'] = reference
    result['target'] = target
    result['threshold'] = threshold
    result['difference'] = target - reference
    result['percentage'] = result['difference'] * 100. / reference

    if result['percentage'] < 0:
        result['comparison'] = BETTER
    elif result['percentage'] <= threshold:
        result['comparison'] = SIMILAR
    else:
        result['comparison'] = WORSE

    return result


def log_comparison_result(
        logger,
        ref_file,
        target_file,
        comparison,
    ):
    """."""
    analysis = comparison['analysis']

    logger.info('###################################################')
    logger.info('       RUNNING COMPARISON WITH CONFIGURATION       ')
    logger.info('###################################################')
    logger.info('Reference file: {}'.format(ref_file))
    logger.info('Target file: {}'.format(target_file))
    for entry in analysis:
        logger.info(
            '{} threshold: {}'.format(entry, analysis[entry]['threshold']
        )
    )
    logger.info('###################################################')
    logger.info('RESULTS')
    logger.info('---------------------------------------------------')
    logger.info('REFERENCE FILE:   {}'.format(ref_file))
    for entry in analysis:
        logger.info(
           '{}: {:.5f}'.format(entry, analysis[entry]['reference'])
        )
    logger.info('---------------------------------------------------')
    logger.info('TARGET FILE:      {}'.format(target_file))
    for entry in analysis:
        logger.info(
           '{}: {:.5f}'.format(entry, analysis[entry]['target'])
        )
    logger.info('---------------------------------------------------')
    logger.info('COMPARISON:')
    for entry in analysis:
        logger.info(
            '{} {}: {:.5f} ({:.5f} %)'.format(
                analysis[entry]['comparison'],
                entry,
                analysis[entry]['difference'],
                analysis[entry]['percentage']
            )
        )
    logger.info('---------------------------------------------------')
    logger.info(
        'FINAL RESULT: Comparison {}'.format(
            'passed =)' if comparison['result'] is True else 'failed =('
        )
    )
    logger.info('---------------------------------------------------')


def compare_files(
        ref_file,
        target_file,
        latency_threshold,
        jitter_threshold,
        rss_threshold
    ):
    """."""
    ref_results = read_file_results(ref_file)
    target_results = read_file_results(target_file)
    analysis = {}

    # Latency min comparison
    analysis['latency_min (ms)'] = compare_measurements(
        reference=min(ref_results['latency_min (ms)']),
        target=min(target_results['latency_min (ms)']),
        threshold=latency_threshold
    )

    # Latency mean comparison
    analysis['latency_mean (ms)'] = compare_measurements(
        reference=min(ref_results['latency_mean (ms)']),
        target=min(target_results['latency_mean (ms)']),
        threshold=latency_threshold
    )


    # Latency max comparison
    analysis['latency_max (ms)'] = compare_measurements(
        reference=max(ref_results['latency_max (ms)']),
        target=max(target_results['latency_max (ms)']),
        threshold=jitter_threshold
    )

    # Jitter comparison
    analysis['jitter_max (ms)'] = compare_measurements(
        reference=max(calculate_jitter(ref_results['latency_max (ms)'])),
        target=max(calculate_jitter(target_results['latency_max (ms)'])),
        threshold=jitter_threshold
    )

    # RSS comparison
    analysis['ru_maxrss (KB)'] = compare_measurements(
        reference=max(ref_results['ru_maxrss']),
        target=max(target_results['ru_maxrss']),
        threshold=rss_threshold
    )

    # Get the overall result
    comparison_result = all(
        analysis[entry]['comparison'] == BETTER
        for entry in analysis.keys()
    )

    ret = {
        'ref_results': ref_results,
        'target_results': target_results,
        'analysis': analysis,
        'result': comparison_result
    }
    return ret