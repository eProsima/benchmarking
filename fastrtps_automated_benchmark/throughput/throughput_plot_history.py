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
import json
import logging
from os import listdir
from os import makedirs
from os.path import abspath
from os.path import isdir
from os.path import isfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import pandas


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


def plot_history(
    data_frame,
    save_directory,
    column,
    experiment_type,
    print_summary=False,
):
    """
    Create a history plot for a given check with one data series per execution.

    :param data_frame: A Pandas DataFrame containing all the different
        executions data. The executions are marked with the 'Execution' column.
        data_frame is expected to contain columns: 'Payload [Bytes]', <column>,
        and 'Execution'.
    :param save_directory: The directory to place the plot.
    :param column: The column to plot.
    :param experiment_type: The type of experiment (used for the figure title)
    :param print_summary: Whether or not to print the data_frame.
    """
    # Validate input types
    assert(isinstance(data_frame, pandas.DataFrame))
    assert(isinstance(save_directory, str))
    assert(isinstance(column, str))
    assert(isinstance(print_summary, bool))

    # Verify that necessary columns exist
    if column not in data_frame:
        logger.error('Dataframe does not contain column "{}"'.format(column))
        return False

    if 'Execution' not in data_frame:
        logger.error('Dataframe does not contain column "Execution"')
        return False

    if 'Payload [Bytes]' not in data_frame:
        logger.error('Dataframe does not contain column "Payload [Bytes]"')
        return False

    # Print summary if needed
    if print_summary is True:
        logger.info('\n{}'.format(data_frame))

    # History plot
    fig, ax = plt.subplots()
    for key, grp in data_frame.groupby(['Execution']):
        logger.debug('Adding series "{}" of "{}"'.format(key, column))
        ax = grp.plot(
            ax=ax,
            style='.-',
            x='Payload [Bytes]',
            y=column,
            label=key,
        )
        ax.set_xticks(range(len(grp['Payload [Bytes]'])))

    plt.xlabel('Payload [Bytes]')
    plt.ylabel(column)
    plt.legend(loc='best')
    plt.grid()
    plt.title('History {} {}'.format(experiment_type, column))

    if not isdir(save_directory):
        makedirs(save_directory)
    fig_name = column.lower().replace(' ', '_').replace('/', '')
    fig_name = fig_name.replace('[', '').replace(']', '')
    fig_name = '{}/history_{}.png'.format(
        save_directory,
        fig_name
    )
    logger.debug('Saving figure "{}"'.format(fig_name))
    plt.savefig(fig_name, bbox_inches='tight')
    plt.close(fig)
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="""
            Script to create history plots based on experiments results
            summaries as output by 'throughput_process_results.py', and a
            requirements CSV file as output by
            'throughput_determine_requirements.py'. The script creates one
            history plot for each experiment type, payload and check
            (lost samples, and subscription throughput median), with the
            different executions in the X-axis, and the throughput in the
            Y-axis. These plots contain the data series (in blue), and a red
            dotted line for the requirement set for that specific experiment
            type, payload, and check. Furthermore, for each experiment type and
            check, the script creates a plot with the payload in the X-axis,
            the throughput in the Y-axis, and one data series for each
            execution.
        """
    )
    parser.add_argument(
        '-p',
        '--plots_directory',
        help='The directory to store the plots',
        required=True
    )
    parser.add_argument(
        '-r',
        '--requirements',
        help='The requirements CSV file',
        required=True
    )
    parser.add_argument(
        '-e',
        '--experiments_results',
        help='The directory containing the results of all the experiments',
        required=True
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Set logging level to debug.'
    )
    args = parser.parse_args()

    # Create a custom logger
    logger = logging.getLogger('THROUGHPUT.PLOT.HISTORY')
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
    requirements = abspath(args.requirements)
    experiments = abspath(args.experiments_results)

    # Validate arguments
    assert(isfile(requirements))
    assert(isdir(experiments))

    logger.debug('Loadind requirements from "{}"'.format(requirements))
    reqs_data = pandas.read_csv(requirements)

    # Get list of experiment types for which there are requirements
    supported_exp_types = list(set(reqs_data['Experiment type'].tolist()))
    logger.debug('Supported experiment types: {}'.format(supported_exp_types))

    # Get the list of results directories
    results_dirs = sorted(listdir(experiments))
    logger.debug('Results directories: {}'.format(results_dirs))

    # Create a dict with paths to results files
    # data_for_plots = {
    #     experiment_type_1: {
    #         build_1: file,
    #         build_2: file,
    #     },
    #     experiment_type_2: {
    #         build_1: file,
    #         build_2: file,
    #     }
    # }
    data_for_plots = {}
    for res in results_dirs:
        full_dir = '{}/{}'.format(experiments, res)
        logger.debug('Adding "{}" to data_for_plots'.format(full_dir))

        result_files = [f for f in listdir(full_dir) if 'summary' in f]
        logger.debug('Summaries in "{}": "{}"'.format(full_dir, result_files))

        for r in result_files:
            experiment_type = r.split('/')[-1].split('.')[-2].split('_')[1:-1]
            experiment_type = '_'.join(experiment_type)
            logger.debug('"{}" is of type "{}"'.format(r, experiment_type))

            if experiment_type not in supported_exp_types:
                logger.warning(
                    'No reference for "{}". Skipping'.format(experiment_type)
                )
                continue

            if experiment_type not in data_for_plots:
                data_for_plots[experiment_type] = {}

            data_for_plots[experiment_type][res] = '{}/{}/{}'.format(
                experiments,
                res,
                r
            )
    logger.debug(
        'data_for_plots:\n{}'.format(json.dumps(data_for_plots, indent=4))
    )

    columns_history_plots = [
        'Lost [samples]',
        'Subscription throughput [Mb/s]',
    ]
    columns_refs_plots = columns_history_plots

    logger.info('----------------------------')
    # Create a set of history plots for each experiment type
    for experiment_type in data_for_plots:
        logger.debug('Creating plots for "{}"'.format(experiment_type))
        logger.debug('Loading requirements for "{}"'.format(experiment_type))
        reqs = reqs_data[reqs_data['Experiment type'] == experiment_type]

        # Build a table with all the data for a given experiment type
        logger.debug(
            'Gathering data for experiment type "{}"'.format(experiment_type)
        )
        summaries_data = pandas.DataFrame()
        for execution in data_for_plots[experiment_type]:
            build_data = pandas.read_csv(
                data_for_plots[experiment_type][execution]
            )
            build_data['Payload [Bytes]'] = build_data[
                'Payload [Bytes]'
            ].astype(str)
            build_data['Execution'] = execution
            summaries_data = summaries_data.append(build_data, sort=False)
        logger.debug('Data:\n{}'.format(summaries_data))

        # Create a plot for each payload
        payloads = summaries_data['Payload [Bytes]'].unique()
        for payload in payloads:
            logger.debug('Creating plots for payload {}'.format(payload))
            payload_data = summaries_data[
                summaries_data['Payload [Bytes]'] == payload
            ]

            # Get reference values of interest
            ref = reqs[reqs['Payload [Bytes]'] == int(payload)]

            # Create one plot for each check
            for c in columns_refs_plots:
                logger.info(
                    'Plotting history of "{}" {} Bytes "{}"'.format(
                        experiment_type,
                        payload,
                        c
                    )
                )
                ax = payload_data.plot(
                    style='.-',
                    x='Execution',
                    y=c
                )
                ax.axhline(
                    y=ref[c].values[0],
                    linestyle='--',
                    color='red',
                    label='{} requirement'.format(c)
                )
                ax.set_xticks(range(len(payload_data['Execution'])))
                ax.set_xticklabels(payload_data.Execution)
                plt.xticks(rotation='vertical')
                plt.xlabel('Execution')
                plt.ylabel(c)
                plt.legend(loc='best')
                plt.grid()
                plt.title(
                    'History {} Bytes {}'.format(
                        payload,
                        experiment_type
                    )
                )
                save_directory = '{}/{}'.format(
                    plots_directory,
                    experiment_type
                )
                if not isdir(save_directory):
                    makedirs(save_directory)
                fig_name = c.lower().replace(' ', '_').replace('/', '')
                fig_name = fig_name.replace('[', '').replace(']', '')
                fig_name = '{}/{}_bytes_{}.png'.format(
                    save_directory,
                    payload,
                    fig_name
                )
                logger.debug('Saving plot "{}"'.format(fig_name))
                plt.savefig(fig_name, bbox_inches='tight')
                plt.close()

        # Create min, median, max, and 99% plots with payload in x-axis,
        # latency in the y-axis, and a series for each execution
        save_directory = '{}/{}'.format(plots_directory, experiment_type)
        for column in columns_history_plots:
            logger.info(
                'Plotting full history of "{}" "{}"'.format(
                    experiment_type,
                    column
                )
            )
            plot_history(
                data_frame=summaries_data,
                save_directory=save_directory,
                column=column,
                experiment_type=experiment_type,
                print_summary=False
            )
        logger.info('----------------------------')
