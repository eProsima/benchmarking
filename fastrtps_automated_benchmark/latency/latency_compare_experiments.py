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
Compare two latency experiment results as output by 'latency_job.bash'.

The script takes two latency experiment result directories (one acting as
reference and the other one as target for the comparison), scans them looking
for sub-experiment summaries as output by 'latency_process_results.py',
compares the results of the target against the reference in terms of latency
minima, median, 99 percentile, and maxima, generates comparison plots
(min-median, max-99%), and creates comparison CSVs (stored in the plots
directory). The script's exit code is 0 if all performed comparisons succeed,
and 1 otherwise. Run with '-h' or '--help' to see a complete list of arguments.

Example:
    python3 latency_compare_experiments.py \\
        --reference ./reference_results \\
        --results ./target_result \\
        --plots_directory ./comparison_plots

Output example:
    Comparison for measurements_interprocess_best_effort_summary.csv PASSED
    Comparison for measurements_interprocess_best_effort_tcp_summary.csv FAILED
    Comparison for measurements_interprocess_reliable_summary.csv PASSED
    Comparison for measurements_interprocess_reliable_tcp_summary.csv PASSED
    Comparison for measurements_intraprocess_best_effort_summary.csv PASSED
    Comparison for measurements_intraprocess_reliable_summary.csv PASSED
    5/6 comparisons passed
    Failed comparisons:
       measurements_interprocess_best_effort_tcp_summary.csv
    Comparison exit code: 1

The previous generates the following CSVs and plots:
    - /comparison_plots/interprocess_best_effort_comparison.csv
    - /comparison_plots/interprocess_best_effort_max_99%.png
    - /comparison_plots/interprocess_best_effort_min_median.png
    - /comparison_plots/interprocess_best_effort_tcp_comparison.csv
    - /comparison_plots/interprocess_best_effort_tcp_max_99%.png
    - /comparison_plots/interprocess_best_effort_tcp_min_median.png
    - /comparison_plots/interprocess_reliable_comparison.csv
    - /comparison_plots/interprocess_reliable_max_99%.png
    - /comparison_plots/interprocess_reliable_min_median.png
    - /comparison_plots/interprocess_reliable_tcp_comparison.csv
    - /comparison_plots/interprocess_reliable_tcp_max_99%.png
    - /comparison_plots/interprocess_reliable_tcp_min_median.png
    - /comparison_plots/intraprocess_reliable_comparison.csv
    - /comparison_plots/intraprocess_reliable_max_99%.png
    - /comparison_plots/intraprocess_reliable_min_median.png
    - /comparison_plots/intraprocess_best_effort_comparison.csv
    - /comparison_plots/intraprocess_best_effort_max_99%.png
    - /comparison_plots/intraprocess_best_effort_min_median.png
"""
import argparse
import logging
from os import listdir
from os import makedirs
from os.path import isdir
from os.path import isfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import pandas as pd


def directory_type(directory):
    """
    Check whether the argument is a directory.

    :param directory: The directory path.
    :return: The directory path without ending /.
    """
    if directory.endswith('/'):
        directory = directory[:-1]
    if not isdir(directory):
        makedirs(directory)
    return directory


def experiment_type_from_filename(filename):
    """
    Get the experiment type based on filename.

    It is assumed that the filename is compliant with
    '<some_path>/measurements_<experiment_type>_summary.csv'

    :param filename: A string representing the file name. It can be either full
        or relative path.
    :return: A string representing the filename:

    Example:
        exp_type = experiment_type_from_filename(
            './measurements_interprocess_best_effort_tcp_summary.csv'
        )
        exp_type -> interprocess_best_effort_tcp
    """
    exp_type = filename.split('/')[-1].split('.')[-2].split('_')[1:-1]
    return '_'.join(exp_type)


def compare_(
    reference_data,
    result_data,
    columns,
    fail_threshold,
):
    """
    Compare the reference and result data for certain columns.

    Take a pd.Dataframe containing reference and results data, and compare
    certain columns by payload (Bytes) using a fail threshold. If the value in
    <result_data> is bigger than the equivalent reference times
    (1 + <fail_threshold>), then the comparison fails. In this sense,
    <fail_threshold> acts as a percentage over the reference, but expressed in
    based 1 instead of 100.

    The function makes the following assumptions about the DataFrames:
        - They contain a 'Bytes' column.
        - There is only one entry for a given 'Bytes' value.
        - The 'Bytes' column is identical for both DataFrames.
        - All the columns in <columns> are present in the DataFrames.

    :param reference_data: A DataFrame with the reference for the comparison.
    :param result_data: A DataFrame with the data to check.
    :param columns: The columns to compare.
    :param fail_threshold: The limit over the reference.

    :returns: A tuple containing:
        - Return code: True if all comparisons succeeded (meaning the result
            was always below the reference + threshold). Else otherwise.
        - Dictionary: A dictionary which keys are the columns, and the values
            are DataFrames containing the comparisons. Each DataFrame has the
            following columns:
                - Bytes: the payload
                - Reference <column>: The reference value
                - Result <column>: The result value
                - Fail threshold: The fail threshold used
                - Comparison: Either 'passed' of 'failed'

    Example:
        ret, dfs = compare_(
            reference_data=pd.DataFrame({'Bytes': [16], 'data': [0.458]}),
            result_data=pd.DataFrame({'Bytes': [16], 'data': [3.934]}),
            columns=['data'],
            fail_threshold=0.1
        )
        ret -> False
        dfs -> {
            'data':
                Bytes  Reference data  Result data  Fail threshold Comparison
                   16           0.458        3.934             0.1     failed
        }
    """
    ret = True  # Function return code
    comp_dfs = {}  # A dictionary containing the comparison DataFrames
    # Iterate over columns
    for column in columns:
        comp_df = pd.DataFrame()  # DataFrame for the colum comparison
        # Iterate over payloads (Bytes) in reference_data
        for payload, ref_grp in reference_data.groupby(['Bytes']):
            # Get result_data for that payload
            res_grp = result_data.loc[result_data['Bytes'] == payload]
            # DataFrame for payload entry
            comp_entry = pd.DataFrame(
                {
                    'Bytes': [payload],
                    'Reference {}'.format(column): ref_grp[column].values,
                    'Result {}'.format(column): res_grp[column].values,
                    'Fail threshold': [fail_threshold],
                }
            )
            # Perform the actual comparison
            if (res_grp[column].values[0] >
                    ref_grp[column].values[0]) * (1 + fail_threshold):
                # Once one check fails, the entire comparison fails.
                ret = False
                comp_entry['Comparison'] = 'failed'
            else:
                comp_entry['Comparison'] = 'passed'
            # Add entry to column DataFrame
            comp_df = comp_df.append(comp_entry, sort=False)
        # Add column DataFrame to dictionary, using column as key
        comp_df = comp_df.reset_index(drop=True)
        comp_dfs[column] = comp_df
    return ret, comp_dfs


def plot_(
    data,
    columns,
    fig_name,
    plots_directory,
):
    """
    Create a comparison plot for a set of columns in a DataFrame.

    Take a DataFrame and a set of columns and create a plot with one series for
    each column and label in 'Label' column, using 'Bytes' column as X-axis.

    :param data: A DataFrame containing the data to plot. It is assumed that:
        - There is a 'Bytes' column.
        - All the columns in <column> are present in <data>.
        - There is a 'Label' column with two different values at most.
    :param columns: The columns to plot. For clarity, only a maximum of 2
        columns is supported.
    :param fig_name: The name of the figure. This will be used for:
        - Figure title: 'Comparison <fig_name>'.
        - Figure filename: '<plots_directory>/<fig_name>.png'
    :param plots_directory: The directory to store the plot.

    Example:
        plot_(
            data=pd.DataFrame(
                {
                    'Bytes': ['16', '16'],
                    'Min': [0.432, 3.654],
                    'Median': [0.458, 3.934],
                    'Label': ['Reference', 'Result']
                }
            ),
            columns=['Min', 'Median'],
            fig_name='intraprocess_reliable_min_median',
            plots_directory='./',
        )

        Creates a ./intraprocess_reliable_min_median.png figure with 4 series:
            - 'Reference Min' with color red #ff0000,
            - 'Reference Median' with color red #ff6666,
            - 'Result Min' with color blue #09487e,
            - 'Result Median' with color blue #0895cd,
    """
    # Check that columns does not have more than 2 elements
    if len(columns) > 2:
        logger.error(
            'Only a maximum of 2 columns is supported. {} were given'.format(
                len(columns)
            )
        )
        return

    # Color codes for the series
    color_codes = [
        ['#ff0000', '#ff6666'],  # Reds for reference
        ['#09487e', '#0895cd'],  # Blues for results
    ]

    fig, ax = plt.subplots()
    i = 0
    # Group by label (reference and result)
    for key, grp in data.groupby(['Label']):
        # Set series' labels
        keys = []
        for c in columns:
            keys.append('{} {}'.format(key, c))
        # One series per label and column
        ax = grp.plot(
            ax=ax,
            style='.-',
            x='Bytes',
            y=columns,
            label=keys,
            color=color_codes[i],
        )
        ax.set_xticks(range(len(grp['Bytes'])))  # One x-tick per payload
        i += 1 if i < (len(color_codes) - 1) else 0
    # Configure plot and save
    plt.xlabel('Payload [Bytes]')
    plt.ylabel('Latency [us]')
    plt.legend(loc='best')
    plt.grid()
    plt.title('Comparison {}'.format(fig_name))
    fig_path = '{}/{}.png'.format(plots_directory, fig_name)
    plt.savefig(fig_path)
    logger.debug('Generated figure: {}'.format(fig_path))
    plt.close(fig)


def compare_and_plot(
    reference,
    result,
    plots_directory,
    columns=['Min', 'Median', 'Max', '99%'],
    reference_label='reference',
    result_label='result',
    fail_threshold=0.1
):
    """
    Compare and plot latency results against a reference.

    Compare and plot latency results agains a reference by providing summary
    CSV files in the format output by "latency_process_results.py. Specify
    which columns are to be compared, where to store the generated plots, as
    well as a fail threshold. This method is a wrapper to aggregate and
    simplify the call to 'compare_()' and 'plot_()'.

    :param reference: The path to the reference CSV file. It is assumed to be
        of the form:'<some_path>/measurements_<experiment_type>_summary.csv'
    :param result: The path to the results CSV file. It is assumed to be
        of the form:'<some_path>/measurements_<experiment_type>_summary.csv'
    :param plots_directory: The path to the plot to store direcotries.
    :param columns: The columns to compare. For clarity, one plot is genereted
        for every 2 columns provided, grouping them in paris starting at the
        beginning of the list. If an odd number of columns is provided, the
        last one has a plot for its own.
        Defaults: ['Min', 'Median', 'Max', '99%']
    :param reference_label: The label for the reference data.
        Defaults: 'reference'.
    :param result_label: The label for the result data.
        Defaults: 'result'.
    :param fail_threshold: The limit over the reference. Defaults: 0.1.

    :returns: A tuple containing:
        - Return code: True if all comparisons succeeded (meaning the result
            was always below the reference + threshold). Else otherwise.
        - Dictionary: A dictionary which keys are the columns, and the values
            are DataFrames containing the comparisons. Each DataFrame has the
            following columns:
                - Bytes: the payload
                - Reference <column>: The reference value
                - Result <column>: The result value
                - Fail threshold: The fail threshold used
                - Comparison: Either 'passed' of 'failed'
        - Summaries_data: A DataFrame agragating the reference and result
            summaries, adding a column 'Label' populated with <reference_label>
            and <result_label> respectively.

    Example:
        reference_summary.csv contains:
            Bytes,Max,99%
            16,482.873,38.817

        result_summary.csv contains:
            Bytes,Max,99%
            16,1350.840,218.852

        comp_result, comp_dfs, summaries_data = compare_and_plot(
            reference='ref/measurements_interprocess_best_effort_summary.csv',
            result=res/measurements_interprocess_best_effort_summary.csv,
            plots_directory=./comparison_plots,
            columns=['Max', '99%'],
            reference_label='Reference label',
            result_label='Result: label',
        )

        The call to 'compare_and_plot()' will create one comparison figure
        './comparison_plots/interprocess_best_effort_max_99%.png'

        comp_result -> False
        comp_dfs -> {
            'Max':
                Bytes  Reference Max  Result Max  Fail threshold Comparison
                   16        482.873    1350.840             0.1     failed
                ,
            '99%':
                Bytes  Reference 99%  Result 99%  Fail threshold Comparison
                   16         38.817     218.852             0.1     failed
        }
        summaries_data ->
                Bytes       Max      99%            Label
            0      16   482.873   38.817  Reference label
            1      16  1350.840  218.852     Result label
    """
    # Validate arguments
    assert(isfile(reference))
    assert(isfile(result))
    assert(isdir(plots_directory))
    assert(isinstance(columns, list))
    assert(isinstance(reference_label, str))
    assert(isinstance(result_label, str))
    assert(fail_threshold >= 0 and fail_threshold <= 1)

    # Summaries combination
    summaries_data = pd.DataFrame()

    # Data from reference
    reference_data = pd.read_csv(reference)
    reference_data['Label'] = reference_label

    # Data from result
    result_data = pd.read_csv(result)
    result_data['Label'] = result_label

    # Compare results
    comp_result, comp_dfs = compare_(
        reference_data=reference_data,
        result_data=result_data,
        columns=columns,
        fail_threshold=fail_threshold
    )

    # Prepare data for plots
    reference_data.Bytes = reference_data.Bytes.astype(str)
    result_data.Bytes = result_data.Bytes.astype(str)
    # Create summary
    summaries_data = summaries_data.append(reference_data, sort=False)
    summaries_data = summaries_data.append(result_data, sort=False)
    summaries_data = summaries_data.reset_index(drop=True)

    # Create one comparison plot for each 2 columns
    column_pairs = [columns[x:x+2] for x in range(0, len(columns), 2)]
    for column_pair in column_pairs:
        # Figure name is <experiment_type>_<col_1>_<col_2>
        fig_name = experiment_type_from_filename(reference)
        fig_name += '_{}'.format(
            '_'.join(c.lower() for c in column_pair)
        )
        # Generate the plot
        plot_(
            data=summaries_data,
            columns=column_pair,
            fig_name=fig_name,
            plots_directory=plots_directory,
        )
    return comp_result, comp_dfs, summaries_data


if __name__ == '__main__':
    # Get argument parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__
    )
    # Great different argument groups
    parser._action_groups.pop()
    required = parser.add_argument_group('Required arguments')
    optional = parser.add_argument_group('Optional arguments')
    # Define arguments
    required.add_argument(
        '-p',
        '--plots_directory',
        type=directory_type,
        help='The directory to store the plots',
        required=True
    )
    required.add_argument(
        '-R',
        '--reference',
        help='The reference directory',
        required=True
    )
    required.add_argument(
        '-r',
        '--results',
        help='The results directory',
        required=True
    )
    optional.add_argument(
        '-t',
        '--fail_threshold',
        help="""The limit that the "results" data is allowed to exceed the
                reference data. Represents a percentage over the reference,
                expressed in based 1 instead of 100.""",
        default=0.1,
        required=False
    )
    optional.add_argument(
        '-P',
        '--print_summaries',
        action='store_true',
        help='Whether to print a table with the summaries for each result',
        required=False
    )
    optional.add_argument(
        '-d',
        '--debug',
        action='store_true',
        help='Print debug info.'
    )
    # Get arguments
    args = parser.parse_args()
    # Validate arguments
    plots_directory = args.plots_directory
    reference = args.reference
    reference = reference[:-1] if reference.endswith('/') else reference
    results = args.results
    results = results[:-1] if results.endswith('/') else results
    print_summaries = args.print_summaries
    fail_threshold = float(args.fail_threshold)

    # Create a custom logger
    logger = logging.getLogger('LATENCY_COMPARISON')
    # Create handlers
    l_handler = logging.StreamHandler()
    # Create formatters and add it to handlers
    l_format = '[%(asctime)s][%(levelname)s] %(message)s'
    l_format = logging.Formatter(l_format)
    l_handler.setFormatter(l_format)
    # Add handlers to the logger
    logger.addHandler(l_handler)
    # Set log level
    if args.debug is True:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Get list of summary files in reference and results directories
    reference_files = [f for f in listdir(reference) if 'summary' in f]
    results_files = [f for f in listdir(results) if 'summary' in f]

    # Check that all results have a reference to compare with
    for f in results_files:
        if f not in reference_files:
            logger.error(
                '{} present in results but not in reference'.format(f)
            )
            exit(1)

    exit_code = 0
    failed_comparisons = []
    # Iterate over results_files.
    for result in results_files:
        logger.debug('Analyzing {}'.format(result))
        # To identify which reference corresponds to each result, the
        # correspoding files have the same name.
        reference_file = '{}/{}'.format(reference, result)
        result_file = '{}/{}'.format(results, result)
        # Check that reference exists
        if not isfile(reference_file):
            logger.warning(
                'No reference file found for {}. Skipping'.format(result)
            )
            continue
        # Compare a plot experiment for latency minima, meadian, maxima, and
        # 99 percentile.
        comp_result, comp_dfs, summaries_data = compare_and_plot(
            reference=reference_file,
            result=result_file,
            plots_directory=plots_directory,
            columns=['Min', 'Median', 'Max', '99%'],
            reference_label='Reference: {}'.format(reference.split('/')[-1]),
            result_label='Result: {}'.format(results.split('/')[-1]),
            fail_threshold=fail_threshold
        )
        # Save comparison summary CSV in the plots directory
        csv_name = '{}/{}_comparison.csv'.format(
            plots_directory,
            experiment_type_from_filename(result)
        )
        summaries_data.to_csv(csv_name, float_format='%.3f', index=False)
        logger.debug('Generated CSV: {}'.format(csv_name))

        # Check exit code
        if comp_result is True:
            logger.info('Comparison for {} PASSED'.format(result))
        else:
            exit_code = 1
            failed_comparisons.append(result)
            logger.error('Comparison for {} FAILED'.format(result))

        # Print if necessary
        if print_summaries is True or args.debug:
            logger.info('{} summary:\n{}'.format(result, summaries_data))
            if comp_result is False:
                for key in comp_dfs:
                    logger.debug('Comparison summary for {}'.format(key))
                    logger.debug('{}\n'.format(comp_dfs[key]))

    # Log comparison summary
    logger.info(
        '{}/{} comparisons passed'.format(
            len(results_files) - len(failed_comparisons),
            len(results_files)
        )
    )
    if exit_code != 0:
        logger.info('Failed comparisons:')
        for failure in failed_comparisons:
            logger.info('   {}'.format(failure))

    # Exit with 0 if all passed, 1 otherwise.
    logger.info('Comparison exit code: {}'.format(exit_code))
    exit(exit_code)
