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
import multiprocessing
from os import makedirs
from os.path import isdir
from os.path import abspath

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import pandas

import seaborn as sns


def directory_type(directory):
    """
    Check whether <directory> is an exists. Create it if it does not.

    :param directory: The directory path.
    :return: The directory path without ending /.
    """
    if directory.endswith('/'):
        directory = directory[:-1]
    if not isdir(directory):
        logger.debug('Creating directory {}'.format(directory))
        makedirs(directory)
    return directory


def create_throughput_summary(raw_data, output_csv):
    """
    Create a throughput summary from a dataframe.

    :param raw_data: A DataFrame containing the data of a throughput experiment
        output CSV file.
    :param output_csv: The path to a file to store the summary.
    :return: A DataFrame containing the summary.
    """
    summary_df = pandas.DataFrame()
    payloads = raw_data['Payload [Bytes]'].unique()
    for payload in payloads:
        logger.debug(
            'Adding entry for payload {} Bytes to "{}"'.format(
                payload,
                output_csv
            )
        )
        sample_series = raw_data[raw_data['Payload [Bytes]'] == payload]
        sample_series = sample_series.reset_index(drop=True)
        max_row = sample_series[
            (
                sample_series['Subscription throughput [Mb/s]'] ==
                sample_series['Subscription throughput [Mb/s]'].max()
            )
        ]
        summary_df = summary_df.append(max_row)

    # Save summary as CSV file
    summary_df = summary_df.reset_index(drop=True)
    summary_df.to_csv(output_csv, float_format='%.3f', index=False)
    logger.debug('Summary for {}:\n{}'.format(output_csv, summary_df))
    return summary_df


def create_scatter_plot(
    data,
    x_axis_column,
    y_axis_column,
    data_column,
    plot_file,
    title='Scatter Plot',
    palette='brg'
):
    """."""
    logger.debug('Generating data subset from columns "{}", "{}", "{}"'.format(
        x_axis_column,
        y_axis_column,
        data_column
        )
    )
    data[x_axis_column] = data[x_axis_column].astype(str)
    data = data[[x_axis_column, y_axis_column, data_column]]

    logger.debug('Creating scatter plot {} in "{}":'.format(title, plot_file))
    sns.set()
    ax = sns.scatterplot(
        x=x_axis_column,
        y=y_axis_column,
        data=data,
        hue=data_column,
        size=data_column,
        sizes=(10, 1000),
        alpha=0.65,
        palette=palette,
    )

    logger.debug('Adding value to bubbles')
    for line in range(0, data.shape[0]):
        ax.text(
            data[x_axis_column][line],
            data[y_axis_column][line],
            data[data_column][line],
            horizontalalignment='center',
            size='medium',
            color='black',
        )
    ax.get_legend().remove()
    plt.title(title)
    logger.debug('Saving figure {} in "{}"'.format(title, plot_file))
    plt.savefig(plot_file)
    plt.close()


def plotting_function(payload, raw_data, plots_directory):
    """."""
    logger.debug('Creating scatter plots for payload {}'.format(payload))
    payload_data = raw_data[raw_data['Payload [Bytes]'] == payload]
    payload_data = payload_data.reset_index(drop=True)
    create_scatter_plot(
        data=payload_data,
        x_axis_column='Demand [sample/burst]',
        y_axis_column='Recovery time [ms]',
        data_column='Subscription throughput [Mb/s]',
        plot_file='{}/throughput_scatterplot_{}.png'.format(
            plots_directory,
            payload
        ),
        title='Throughput Scatterplot {} Bytes'.format(payload),
        palette='brg',
    )
    create_scatter_plot(
        data=payload_data,
        x_axis_column='Demand [sample/burst]',
        y_axis_column='Recovery time [ms]',
        data_column='Lost [samples]',
        plot_file='{}/lost_samples_scatterplot_{}.png'.format(
            plots_directory,
            payload
        ),
        title='Lost Samples Scatterplot {} Bytes'.format(payload),
        palette='Reds',
    )


def create_experiment_plots(raw_data, plots_directory):
    """."""
    payloads = raw_data['Payload [Bytes]'].unique()
    logger.debug('Creating plotting processes')
    plot_processes = []
    for payload in payloads:
        logger.debug('Creating plotting process for {}'.format(payload))
        plot_processes.append(
            multiprocessing.Process(
                target=plotting_function,
                args=(payload, raw_data, plots_directory,)
            )
        )
    try:
        logger.debug('Starting processes')
        for process in plot_processes:
            process.start()

        logger.debug('Joining processes')
        for process in plot_processes:
            process.join()
        logger.debug('All processes have finished working')
        return True
    except Exception as e:
        logger.error('Exception occurred while plotting: {}'.format(e))
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-p',
        '--plots_directory',
        help='The directory to store the plots',
        required=True
    )
    parser.add_argument(
        '-c',
        '--raw_csv',
        help='The CSV file from which the data is extracted',
        required=True
    )
    parser.add_argument(
        '-o',
        '--output_csv',
        help='The file name of the output CSV',
        required=True
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Set logging level to debug.'
    )
    args = parser.parse_args()

    # Create a custom logger
    logger = logging.getLogger('THROUGHPUT.PROCESS.RESULTS')
    # Create handlers
    c_handler = logging.StreamHandler()
    # Create formatters and add it to handlers
    c_format = (
        '[%(asctime)s][%(filename)s:%(lineno)s][%(funcName)s()]' +
        '[%(processName)s][%(levelname)s] %(message)s'
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

    plots_directory = abspath(directory_type(args.plots_directory))
    raw_csv = abspath(args.raw_csv)
    output_csv = abspath(args.output_csv)

    logger.debug('Reading data from "{}"'.format(raw_csv))
    raw_data = pandas.read_csv(raw_csv)

    logger.info('Creating summary in "{}"'.format(output_csv))
    summary_df = create_throughput_summary(raw_data, output_csv)

    logger.info(
        'Creating plots for "{}" in "{}"'.format(raw_csv, plots_directory)
    )
    if create_experiment_plots(raw_data, plots_directory) is True:
        logger.debug('All work is done!')
        exit(0)
    else:
        logger.error('Something went wrong!')
        exit(1)
