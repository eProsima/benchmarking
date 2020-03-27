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
from os import listdir
from os import makedirs
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
        makedirs(directory)
    return directory


def plot_history(
    data_frame,
    save_directory,
    column,
    experiment_type,
    print_summary=False
):
    """
    Create a history plot for a given check with one data series per execution.

    :param data_frame: A Pandas DataFrame containing all the different
        executions data. The executions are marked with the 'Execution' column.
        data_frame is expected to contain columns: 'Bytes', <column>, and
        'Execution'.
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
        print('Dataframe does not contain column "{}"'.format(column))
        return False

    if 'Execution' not in data_frame:
        print('Dataframe does not contain column "Execution"')
        return False

    if 'Bytes' not in data_frame:
        print('Dataframe does not contain column "Bytes"')
        return False

    # Print summary if needed
    if print_summary is True:
        print(data_frame)

    # History plot
    fig, ax = plt.subplots()
    for key, grp in data_frame.groupby(['Execution']):
        ax = grp.plot(
            ax=ax,
            style='.-',
            x='Bytes',
            y=column,
            label=key,
        )
        ax.set_xticks(range(len(grp['Bytes'])))

    plt.xlabel('Payload [Bytes]')
    plt.ylabel('Latency [us]')
    plt.legend(loc='best')
    plt.grid()
    plt.title('History {} {}'.format(experiment_type, column))

    if not isdir(save_directory):
        makedirs(save_directory)
    plt.savefig(
        '{}/history_{}.png'.format(
            save_directory,
            column.replace('%', '')
        ),
        bbox_inches='tight'
    )
    plt.close(fig)
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="""
            Script to create history plots based on experiments results
            summaries as output by 'latency_process_results.py', and a
            requirements CSV file as output by
            'latency_determine_requirements.py'. The script creates one history
            plot for each experiment type, payload and check (latency median,
            maximum, and 99 percentile), with the different executions in the
            X-axis, and the latency in the Y-axis. These plots contain the data
            series (in blue), and a red dotted line for the requirement set for
            that specific experiment type, payload, and check. Furthermore, for
            each experiment type and check, the script creates a plot with the
            payload in the X-axis, the latency in the Y-axis, and one data
            series for each execution.
        """
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
    args = parser.parse_args()
    plots_directory = args.plots_directory
    requirements = args.requirements
    experiments = args.experiments_results

    # Validate arguments
    assert(isfile(requirements))
    assert(isdir(experiments))

    # Get requirements
    reqs_data = pandas.read_csv(requirements)
    # Get list of experiment types for which there are requirements
    supported_exp_types = reqs_data['Experiment type'].tolist()

    # Get the list of results directories
    results_dirs = sorted(listdir(experiments))

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
        result_files = [f for f in listdir(full_dir) if 'summary' in f]

        for r in result_files:
            experiment_type = r.split('/')[-1].split('.')[-2].split('_')[1:-1]
            experiment_type = '_'.join(experiment_type)

            if experiment_type not in supported_exp_types:
                print('No reference for {}. Skipping'.format(experiment_type))
                continue

            if experiment_type not in data_for_plots:
                data_for_plots[experiment_type] = {}

            data_for_plots[experiment_type][res] = '{}/{}/{}'.format(
                experiments,
                res,
                r
            )

    columns_history_plots = [
        'Min',
        'Median',
        'Max',
        '99%',
    ]
    columns_refs_plots = columns_history_plots[1:]

    # Create a set of history plots for each experiment type
    for experiment_type in data_for_plots:

        reqs = reqs_data[reqs_data['Experiment type'] == experiment_type]

        # Build a table with all the data for a given experiment type
        summaries_data = pandas.DataFrame()
        for execution in data_for_plots[experiment_type]:
            build_data = pandas.read_csv(
                data_for_plots[experiment_type][execution]
            )
            build_data.Bytes = build_data.Bytes.astype(str)
            build_data['Execution'] = execution
            summaries_data = summaries_data.append(build_data, sort=False)

        # Create a plot for each payload
        payloads = summaries_data['Bytes'].unique()
        for payload in payloads:
            payload_data = summaries_data[summaries_data['Bytes'] == payload]

            # Get reference values of interest
            ref = reqs[reqs['Bytes'] == int(payload)]

            # Create one plot for each check
            for c in columns_refs_plots:
                print(
                    'Plotting history of {} {} Bytes {}'.format(
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
                plt.ylabel('Latency [us]')
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
                plt.savefig(
                    '{}/{}_bytes_{}.png'.format(
                        save_directory,
                        payload,
                        c.replace('%', '')
                    ),
                    bbox_inches='tight'
                )
                plt.close()

        # Create min, median, max, and 99% plots with payload in x-axis,
        # latency in the y-axis, and a series for each execution
        save_directory = '{}/{}'.format(plots_directory, experiment_type)
        for column in columns_history_plots:
            print(
                'Plotting full history of {} {}'.format(
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
        print('----------------------------')
