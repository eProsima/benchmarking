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

"""
Script to create comparison plots using sub-experiments results summaries.

The script take a list of sub-experiment summaries as output by
'latency_process_results.py' and creates four plots (comparisons for latency
minima, median, maxima, and 99 percentile) with one series per sub-experiment.

Example:
    python3 latency_compare_subexperiments.py \\
        --subexperiment_summaries \\
            ./measurements_interprocess_best_effort_summary.csv \\
            ./measurements_intraprocess_best_effort_summary.csv \\
        --plots_directory ./comparison_plots

Ouput example:
    Plotting comparison for Min
    Plotting comparison for Median
    Plotting comparison for Max
    Plotting comparison for 99%

The previous generates the following plots:
    - ./comparison_plots/comparison_99.png
    - ./comparison_plots/comparison_max.png
    - ./comparison_plots/comparison_median.png
    - ./comparison_plots/comparison_min.png
"""
import argparse
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


def plot_comparison(
    data_frame,
    save_directory,
    column,
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
    :param print_summary: Whether or not to print the data_frame
        [Defaults: False].

    Example:
        plot_comparison(
            data_frame=pandas.DataFrame(
                {
                    'Bytes': [16, 16],
                    'Median': [15.013, 5.759],
                    'Sub-experiment': [
                        interprocess_best_effort,
                        intraprocess_best_effort
                    ]
                }
            ),
            save_directory=./comparison_plots,
            column='Median'
        )

        The example creates a figure './comparison_plots/comparison_median.png'
        which contains two series labeled 'interprocess_best_effort', and
        'intraprocess_best_effort'. In this example, the plot only consists of
        two points (one per series):
            - (16, 15.013), corresponding to 'interprocess_best_effort'
            - (16, 5,759), correspondint to 'intraprocess_best_effort'
    """
    # Validate input types
    assert(isinstance(data_frame, pandas.DataFrame))
    assert(isinstance(save_directory, str))
    assert(isinstance(column, str))
    assert(isinstance(print_summary, bool))

    print(data_frame)
    print(save_directory)
    print(column)

    # Verify that necessary columns exist
    if column not in data_frame:
        print('Dataframe does not contain column "{}"'.format(column))
        return False
    if 'Sub-experiment' not in data_frame:
        print('Dataframe does not contain column "Sub-experiment"')
        return False
    if 'Bytes' not in data_frame:
        print('Dataframe does not contain column "Bytes"')
        return False

    # Print summary if needed
    if print_summary is True:
        print(data_frame)

    # History plot
    fig, ax = plt.subplots()
    for key, grp in data_frame.groupby(['Sub-experiment']):
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
    plt.title('Comparison {}'.format(column))
    # Create save directory if needed
    if not isdir(save_directory):
        makedirs(save_directory)
    plt.savefig(
        '{}/comparison_{}.png'.format(
            save_directory,
            column.replace('%', '').lower()
        ),
        bbox_inches='tight'
    )
    plt.close(fig)
    return True


if __name__ == '__main__':
    # Get argument parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__
    )
    # Great different argument groups
    parser._action_groups.pop()
    required = parser.add_argument_group('Required arguments')
    required.add_argument(
        '-p',
        '--plots_directory',
        type=directory_type,
        help='The directory to store the plots',
        required=True
    )
    required.add_argument(
        '-e',
        '--subexperiment_summaries',
        nargs='+',
        help='A list of sub-experiment summary CSV files',
        required=True
    )
    # Get arguments
    args = parser.parse_args()
    plots_directory = args.plots_directory
    subexperiments = args.subexperiment_summaries

    # Validate arguments
    for subexperiment in subexperiments:
        assert(isfile(subexperiment))

    # Prepara summary DataFrame for plot_comparison()
    summaries_data = pandas.DataFrame()
    for subexp in subexperiments:
        subexp_type = subexp.split('/')[-1].split('.')[-2].split('_')[1:-1]
        subexp_type = '_'.join(subexp_type)

        subexp_data = pandas.read_csv(subexp)
        subexp_data['Bytes'] = subexp_data['Bytes'].astype(str)
        subexp_data['Sub-experiment'] = subexp_type
        summaries_data = summaries_data.append(subexp_data, sort=False)

    columns_plots = [
        'Min',
        'Median',
        'Max',
        '99%',
    ]

    for column in columns_plots:
        # Create min, median, max, and 99% plots with payload in x-axis,
        # latency in the y-axis, and a series for each execution
        print('Plotting comparison for {}'.format(column))
        plot_comparison(
            data_frame=summaries_data,
            save_directory=plots_directory,
            column=column,
            print_summary=False
        )
