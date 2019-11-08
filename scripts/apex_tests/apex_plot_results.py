"""Script to plot Apex.AI performance test results."""
import argparse
import csv
import json
import statistics

import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import numpy as np
from os import listdir
from os import makedirs
from os.path import abspath
from os.path import isdir
from os.path import exists


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


def check_directories(directories):
    """
    Check whether the argument is a list of existing directories.

    :param directories: A list of directory paths.
    :return: A list of directory paths without ending /.
    :raise: argparse.ArgumentTypeError if any directory is not a directory.
    """
    ret = []
    for directory in directories:
        if directory.endswith('/'):
            directory = directory[:-1]
        if not isdir(directory):
            raise argparse.ArgumentTypeError(
                'Cannot find directory "{}"'.format(directory)
            )
        ret.append(directory)
    return ret


def get_tree_as_dict(directory):
    """
    Get the files contained in directory.

    Directory is expected fo have the following structure:
    Directory
    ├── rate_X
    |   ├── subs_A
    |   │    ├── file_a
    |   │    └── file_b
    |   └── subs_B
    |        ├── file_c
    |        └── file_d
    └── rate_Y
        ├── subs_A
        │    ├── file_a
        │    └── file_b
        └── subs_B
             ├── file_c
             └── file_d
    :param directory: The directory to scan.
    :return: A dictionary that contains the files. This looks like:
    {
        "rate_X": {
            "subs_A": [
                file_a,
                file_b
            ],
            "subs_B": [
                file_c,
                file_d
            ]
        },
        "rate_Y": {...}
    }
    """
    tree = {}
    rates = listdir(directory)
    for rate in rates:
        tree[rate] = {}
        rate_dir = '{}/{}'.format(directory, rate)
        subs = listdir(rate_dir)
        for sub in subs:
            tree[rate][sub] = {}
            sub_dir = '{}/{}'.format(rate_dir, sub)
            list_files = listdir(sub_dir)
            for filename in list_files:
                file_type = get_experiment_type(filename)
                if file_type not in tree[rate][sub]:
                    tree[rate][sub][file_type] = []
                tree[rate][sub][file_type].append(
                    '{}/{}'.format(sub_dir, filename)
                )
    return tree


def get_experiment_type(filename):
    """
    Get the experiment type from the filename.

    The filename is assumed to be in the form of:
    '<reliability>_<durability>_<history kind>_<topic>_<timestamp>'

    :param filename: The filename to get the type.
    :return: A string where the timesptamp is taken out from the filename.
    """
    file_type = ''
    filename = filename.split('/')[-1]
    elements = filename.split('_')
    for i in range(0, len(elements) - 3):
        file_type += '{}_'.format(elements[i])
    file_type = file_type[:-1]
    return file_type


def get_experiment_topic(filename):
    """
    Get the experiment topic from the filename.

    The filename is assumed to be in the form of:
    '<reliability>_<durability>_<history kind>_<topic>_<timestamp>'

    :param filename: The filename to get the topic.
    :return: The experiment topic as a string.
    """
    filename = filename.split('/')[-1]
    topic = filename.split('_')[-3]
    return topic


def read_file_results(filename, columns_of_interest):
    """
    Extract the results from a test log filename.

    :return: A dictionary containing the results grouped by columns
    """
    results = {}
    for col in columns_of_interest:
        results[col] = []

    columns_ids = [
        'T_experiment', 'T_loop', 'received', 'sent', 'lost', 'relative_loss',
        'data_received', 'latency_min (ms)', 'latency_max (ms)',
        'latency_mean (ms)', 'latency_variance (ms)', 'pub_loop_res_min (ms)',
        'pub_loop_res_max (ms)', 'pub_loop_res_mean (ms)',
        'pub_loop_res_variance (ms)', 'sub_loop_res_min (ms)',
        'sub_loop_res_max (ms)', 'sub_loop_res_mean (ms)',
        'sub_loop_res_variance (ms)', 'ru_utime', 'ru_stime', 'ru_maxrss',
        'ru_ixrss', 'ru_idrss', 'ru_isrss', 'ru_minflt', 'ru_majflt',
        'ru_nswap', 'ru_inblock', 'ru_oublock', 'ru_msgsnd', 'ru_msgrcv',
        'ru_nsignals', 'ru_nvcsw', 'ru_nivcsw'
    ]

    with open(filename, 'r') as f:
        csv_reader = csv.DictReader(
            f,
            delimiter=',',
            fieldnames=columns_ids
        )
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
                    for col in columns_of_interest:
                        results[col].append(float(row[col]))
                line_count += 1
    return results


def plot_series_set(series_set, title, save_dir, show=False):
    """."""
    fig = plt.figure()
    max_y = 0
    for series in series_set:
        plt.plot(
            series_set[series]['latency_min (ms)'],
            'o-',
            label='{} min'.format(series)
        )
        plt.plot(
            series_set[series]['latency_mean (ms)'],
            'o-',
            label='{} mean'.format(series)
        )
        plt.xticks(
            range(len(series_set[series]['topics'])),
            series_set[series]['topics']
        )
        local_max = max(series_set[series]['latency_mean (ms)'])
        if local_max > max_y:
            max_y = local_max
    # step = 0.5
    # plt.yticks(np.arange(0, max_y + step, step=step))
    plt.xlabel('Data type')
    plt.ylabel('Latency [ms]')
    plt.grid()
    plt.title('Latency Comparison: {}'.format(title))
    plt.legend()
    if show is True:
        plt.show()

    fig_title = '{}/{}.png'.format(save_dir, title)
    print('Generating figure for file {}'.format(fig_title))
    plt.savefig(fig_title)
    plt.close(fig)


def create_plot_from_series_set(series_set, save_dir, ignore_topics=[], show=False):
    """
    Create a plot for a set of data series.

    :param series_set: A dictionary containing the set of data series.
        It is expected to be as follows:
        {
            "series 1": [
                file_1,
                file_2
            ],
            "series 2": [...]
        }
    :param save_dir: The directory to save the plots
    :param ignore_topics: A list of topics to ignore. Defaults [].
    :param show: True to show the plots, False to just save them. Defaults False.
    :return: True on success, False otherwise
    """
    # Create the save dir if it does not exist
    if not exists(save_dir):
        makedirs(save_dir)

    columns_of_interest = [
        'latency_min (ms)',
        'latency_mean (ms)',
        'latency_variance (ms)'
    ]
    title = ''
    result_series = {}
    for series in series_set:
        result_series[series] = {}
        result_series[series]['topics'] = []

        for column in columns_of_interest:
            result_series[series][column] = []

        for filename in series_set[series]:
            topic = get_experiment_topic(filename)
            if topic in ignore_topics:
                continue
            if title == '':
                title = filename.split('/')[-3]
                title += '_{}'.format(filename.split('/')[-2])
                title += '_{}'.format(get_experiment_type(filename))
                if len(ignore_topics) > 0:
                    title += '_ignore'
                    for topic in ignore_topics:
                        title += '_{}'.format(topic)

            raw_results = read_file_results(filename, columns_of_interest)
            latency_min = min(raw_results[columns_of_interest[0]])
            latency_mean = statistics.mean(raw_results[columns_of_interest[1]])
            latency_var = statistics.mean(raw_results[columns_of_interest[2]])
            result_series[series][columns_of_interest[0]].append(latency_min)
            result_series[series][columns_of_interest[1]].append(latency_mean)
            result_series[series][columns_of_interest[2]].append(latency_var)

            if topic not in result_series[series]['topics']:
                result_series[series]['topics'].append(topic)

    plot_series_set(result_series, title=title, save_dir=save_dir)
    return True


def sort_list_by_topic_size(list_files):
    """."""
    tuple_list = []
    for filename in list_files:
        topic = get_experiment_topic(filename)
        multiplier = topic[-1]
        size = ''
        for char in topic:
            if char.isdigit():
                size += char
        size = int(size)
        if multiplier == 'k':
            size = size * 1000
        elif multiplier == 'm':
            size = size * 1000000
        tuple_list.append((filename, size))

    sorted_tuples = sorted(tuple_list, key=lambda tup: tup[1])
    sorted_files = []
    for sorted_tuple in sorted_tuples:
        sorted_files.append(sorted_tuple[0])
    return sorted_files


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-p',
        '--plots_directory',
        type=directory_type,
        help='The directory to store the plots',
        required=True
    )
    parser.add_argument(
        '-r',
        '--results',
        nargs='*',
        default=['.'],
        help='A list of results directories',
        required=True
    )
    parser.add_argument(
        '-s',
        '--set_names',
        nargs='*',
        default=[],
        help=(
            'A list of names corresponding to the set of results contained' +
            'in each results directory'
        ),
    )
    parser.add_argument(
        '-i',
        '--ignore_topics',
        nargs='*',
        default=[],
        help='A list of topics to ignore',
    )
    args = parser.parse_args()
    results_dirs = check_directories(args.results)
    plots_directory = args.plots_directory
    set_names = args.set_names
    ignore_topics = args.ignore_topics

    i = 0
    result_sets = {
        'sets': {},
        'plot_types': {},
    }
    for results_dir in results_dirs:
        # Get the set name
        set_name = set_names[i] if i < len(set_names) else results_dir

        # Get the files of the set in a dict
        result_sets['sets'][set_name] = get_tree_as_dict(results_dir)
        i += 1

        # Add the plot types that are present in the set to results_sets['plot_types']
        for rate in result_sets['sets'][set_name]:
            for sub in result_sets['sets'][set_name][rate]:
                for result_type in result_sets['sets'][set_name][rate][sub]:
                    if rate in result_sets['plot_types']:
                        if sub in result_sets['plot_types'][rate]:
                            if result_type not in result_sets['plot_types'][rate][sub]:
                                result_sets['plot_types'][rate][sub].append(result_type)
                        else:
                            result_sets['plot_types'][rate][sub] = [result_type]
                    else:
                        result_sets['plot_types'][rate] = {sub: [result_type]}

    # Create a plot for each plot type
    for rate in result_sets['plot_types']:
        for sub in result_sets['plot_types'][rate]:
            for plot_type in result_sets['plot_types'][rate][sub]:
                series_for_plot = {}
                for result_set in result_sets['sets']:
                    try:
                        if result_sets['sets'][result_set][rate][sub][plot_type]:
                            series_for_plot[result_set] = sort_list_by_topic_size(
                                result_sets['sets'][result_set][rate][sub][plot_type]
                            )
                    except KeyError:
                        continue

                create_plot_from_series_set(
                    series_set=series_for_plot,
                    save_dir=plots_directory,
                    ignore_topics=ignore_topics
                )
