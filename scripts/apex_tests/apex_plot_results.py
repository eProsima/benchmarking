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

"""Script to plot Apex.AI performance test results."""
import argparse
import csv
import statistics

import matplotlib.pyplot as plt
import pandas
import seaborn as sns
import apex_comparison as ac

from os import listdir
from os import makedirs
from os.path import isdir
from os.path import exists


def plot_series_set(
        series_set,
        title,
        save_dir,
        show=False
    ):
    """
    Create a latency plot from a series_set.

    :param series_set: The set of data series. It is expected to be organized as:
        series_set = {
            series_1: {
                column_1: [data],
                column_2: [data],
                [...]
            },
            series_2: {...}
        }
    :param title: Title for the figure.
    :param save_dir: Directory to save the figure.
    :param show: A boolean to decide whether to show the figure or simply save it.
        Defaults: False.
    """
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

    plt.xlabel('Data type')
    plt.ylabel('Latency [ms]')
    plt.grid()
    plt.title('Latency Comparison: {}'.format(title))
    plt.legend()
    if show is True:
        plt.show()

    fig_title = '{}/{}.png'.format(save_dir, title)
    print('Generating figure file {}'.format(fig_title))
    plt.savefig(fig_title)
    plt.close(fig)


def violin_plot_series_set(
        data,
        x,
        y,
        hue,
        title,
        save_dir,
        x_label=None,
        y_label=None,
        show=False
    ):
    """
    Create a violin plot from a data frame.

    :param data: A pandas data frame.
    :param x: The name of the column to use as X-axis.
    :param y: The name of the column to use as Y-axis.
    :param hue: The name of the column to filter data out.
        Acts as a filter to the data.
    :param title: Title for the figure.
    :param save_dir: Directory to save the figure.
    :param x_label: A label for the X-axis. Defaults: None.
    :param y_label: A label for the Y-axis. Defaults: None.
    :param show: A boolean to decide whether to show the figure or simply save it.
        Defaults: False.
    """
    # Create figure object
    fig = plt.figure()

    # Plot the date frame
    ax = sns.violinplot(
        x=x,
        y=y,
        hue=hue,
        data=data,
        split=True,
    )

    # Figure set up
    if x_label is not None:
        plt.xlabel(x_label)
    if y_label is not None:
        plt.ylabel(y_label)

    plt.grid()
    plt.title(title)
    plt.legend(loc='upper left')

    # Show figure
    if show is True:
        plt.show()

    # Save figure
    fig_title = '{}/{}.png'.format(save_dir, title)
    print('Generating figure file {}'.format(fig_title))
    plt.savefig(fig_title)
    plt.close(fig)


def create_latency_plot_from_series_set(
        series_set,
        save_dir,
        ignore_topics=[],
        show=False
    ):
    """
    Create a latency plot from a set of data series.

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
    # Validate arguments
    assert isinstance(series_set, dict)
    assert isinstance(save_dir, str)
    assert isinstance(ignore_topics, list)
    assert isinstance(show, bool)

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
            topic = ac.get_experiment_topic(filename)
            if topic in ignore_topics:
                continue
            if title == '':
                title = 'latency'
                title += '_{}'.format(filename.split('/')[-3])
                title += '_{}'.format(filename.split('/')[-2])
                title += '_{}'.format(ac.get_experiment_type(filename))
                if len(ignore_topics) > 0:
                    title += '_ignore'
                    for topic in ignore_topics:
                        title += '_{}'.format(topic)

            raw_results = ac.read_file_results(filename)
            latency_min = min(raw_results[columns_of_interest[0]])
            latency_mean = min(raw_results[columns_of_interest[1]])
            latency_var = statistics.mean(raw_results[columns_of_interest[2]])
            result_series[series][columns_of_interest[0]].append(latency_min)
            result_series[series][columns_of_interest[1]].append(latency_mean)
            result_series[series][columns_of_interest[2]].append(latency_var)

            if topic not in result_series[series]['topics']:
                result_series[series]['topics'].append(topic)

    plot_series_set(result_series, title=title, save_dir=save_dir)
    return True


def create_violin_plot_from_series_set(
        series_set,
        save_dir,
        columns_of_interest,
        ignore_topics=[],
        show=False
    ):
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
    :param save_dir: The directory to save the plots.
    :param columns_of_interest: A list of columns from which data is extracted.
    :param ignore_topics: A list of topics to ignore. Defaults [].
    :param show: True to show the plots, False to just save them. Defaults False.
    :return: True on success, False otherwise
    """
    # Validate arguments
    assert isinstance(series_set, dict)
    assert isinstance(save_dir, str)
    assert isinstance(columns_of_interest, list)
    assert isinstance(ignore_topics, list)
    assert isinstance(show, bool)

    # Create the save dir if it does not exist
    if not exists(save_dir):
        makedirs(save_dir)

    # Loop over the columns of interest
    for column_of_interest in columns_of_interest:
        title = ''
        data_for_frame = []
        # Loop over the series
        for series in series_set:
            # Loop over the files
            for filename in series_set[series]:
                # Manage topic
                topic = ac.get_experiment_topic(filename)
                if topic in ignore_topics:
                    continue

                # Generate title
                if title == '':
                    title = column_of_interest.split()[0]
                    title += '_{}'.format(filename.split('/')[-3])
                    title += '_{}'.format(filename.split('/')[-2])
                    title += '_{}'.format(ac.get_experiment_type(filename))
                    title += '_violin'
                    if len(ignore_topics) > 0:
                        title += '_ignore'
                        for ignored_topic in ignore_topics:
                            title += '_{}'.format(ignored_topic)

                # Create data entries for the frame in the form of a list of dict
                raw_results = ac.read_file_results(filename)
                for measurement in raw_results[column_of_interest]:
                    data_for_frame.append(
                        {
                            'implementation': series,
                            'topic': topic,
                            column_of_interest: measurement
                        }
                    )

        # Create the violin plot
        violin_plot_series_set(
            data=pandas.DataFrame(data=data_for_frame),
            x='topic',
            y=column_of_interest,
            hue='implementation',
            title=title,
            save_dir=save_dir,
            x_label='Data type',
            y_label=column_of_interest,
        )
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-p',
        '--plots_directory',
        type=ac.directory_type,
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
    results_dirs = ac.check_directories(args.results)
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
        result_sets['sets'][set_name] = ac.get_tree_as_dict(results_dir)
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
                            series_for_plot[result_set] = ac.sort_files_by_topic_size(
                                result_sets['sets'][result_set][rate][sub][plot_type]
                            )
                    except KeyError:
                        continue

                create_latency_plot_from_series_set(
                    series_set=series_for_plot,
                    save_dir=plots_directory,
                    ignore_topics=ignore_topics
                )
                create_violin_plot_from_series_set(
                    series_set=series_for_plot,
                    save_dir=plots_directory,
                    columns_of_interest = [
                        'latency_min (ms)',
                        'latency_mean (ms)',
                        'latency_max (ms)',
                    ],
                    ignore_topics=ignore_topics
                )
