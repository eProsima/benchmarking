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
Check a latency experiment result against a set of requirements.

Script to check the results of a latency experiment, performed with
"latency_run_experiment.bash", against a set of requirements given as a CSV
file in the format output by "latency_determine_requirements.py". The script
generates check plots in the <plots_directory> directory, as well as CSV files
for each check, placed in the <experiment_directory> directory.
"""

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


def experiment_type(filename):
    """
    Get a experiment type from a file name.

    Assuming that filename is the path to a file name as
    measurements_<experiment_type>.csv, get the experiment type.

    :param filename: The name of the file (it can be full path).
    :raise: AssertionError if <filename> is not a string
    :return: A string representing the experiment type.
    """
    assert(isinstance(filename, str))
    exp_type = filename.split('/')[-1].split('.')[-2].split('_')[1:-1]
    exp_type = '_'.join(exp_type)
    return exp_type


def check_requirement(
    requirements_data,
    experiment_data,
    column,
    payload
):
    """
    Check if a single result meets the requirement.

    :param requirements_data: A Pandas DataFrame with at least column <column>,
        and only one entry.
    :param experiment_data: A Pandas DataFrame with at least column <column>,
        and only one entry.
    :param column: The column to check
    :param payload: The checked payload.
    :raise: AssertionError if:
        * <requirements_data> is not a DataFrame
        * <experiment_data> is not a DataFrame
        * <column> is not on <requirements_data> and in <experiment_data>
        * <column> is not a string
        * <payload> is not a string
    :return: False on check failure, True on check pass
    :return: A one entry Pandas DataFrame with columns: 'Check', 'Bytes',
        'Requirement', 'Experiment', 'Difference', 'Percentage over
        requirement', and 'Status'. Status is either "failed" or "passed"
    """
    assert(isinstance(requirements_data, pandas.DataFrame))
    assert(isinstance(experiment_data, pandas.DataFrame))
    assert(isinstance(column, str))
    assert(column in requirements_data)
    assert(column in experiment_data)
    assert(isinstance(payload, str))

    # Get the requirement
    req = requirements_data[column].values[0]
    # Get the experiment result
    exp = experiment_data[column].values[0]

    diff = req - exp  # Difference
    perc = (-diff * 100) / req  # Percentage of result over the requirement

    # Resulting DataFrame
    result = pandas.DataFrame(
        {
            'Check': column,
            'Bytes': payload,
            'Requirement': [req],
            'Experiment': [exp],
            'Difference': [abs(diff)],
            'Percentage over requirement': [perc],
            'Status': ['failed' if diff < 0 else 'passed']
        }
    )
    return bool(diff >= 0), result


def check_requirements(
    requirements,
    experiment,
):
    """
    Check results of an experiment type agains requirements.

    Check experiment results in terms of median, percentile 99, and maximum
    latency.

    :param requirements: A Pandas DataFrame with one row entry per payload, and
        at least the columns "Bytes", "Median", "99%", and "Max".
    :param experiment: A Pandas DataFrame with one row entry per payload, and
        at least the columns "Bytes", "Median", "99%", and "Max".
    :raise: AssertionError if:
        * requirements is not a DataFrame
        * experiment is not a DataFrame
        * Any of the mandatory columns is not in the DataFrames
    :return: A return code (0 success)
    :return: A dictionary with one entry per check (Median, 99%, and Max). Each
        entry is a DataFrame as returned from check_requirement()

    """
    # Validate arguments
    assert(isinstance(requirements, pandas.DataFrame))
    assert(isinstance(experiment, pandas.DataFrame))

    # Columns to check
    columns = [
        'Bytes',
        'Median',
        '99%',
        'Max',
    ]

    # Validate that columns in dataframes
    for column in columns:
        assert(column in requirements)
        assert(column in experiment)

    return_code = 0
    columns.pop(0)  # Remove 'Bytes' column

    checks = {}

    # Iterate over the payloads
    payloads = requirements['Bytes'].unique()
    for payload in payloads:
        # Extract payload data
        requirements_data = requirements[requirements['Bytes'] == payload]
        result_data = experiment[experiment['Bytes'] == payload]

        # Check payload data for each column
        i = 0
        for column in columns:
            check, failed = check_requirement(
                requirements_data,
                result_data,
                column,
                str(payload)
            )

            # Append results
            if column not in checks:
                checks[column] = pandas.DataFrame()
            checks[column] = checks[column].append(failed, sort=False)
            checks[column] = checks[column].reset_index(drop=True)

            # Update return_code
            if check is False:
                return_code += pow(2, i)
            i += 1

    return return_code, checks


def plot(
    requirements,
    experiment,
    column,
    plots_directory,
    title
):
    """
    Plot the result of an experiment type against requirements.

    Create a comparison graph where one series is the experiment results (in
    blue), an another one (in red) represents the requirements. The X-axis
    represents the payload in Bytes as labels (distance between tick remains
    constant no matter the values), and the Y-axis represents the latency in
    microseconds.

    Note 1: There is no validation on whether the requirements' and experiment
        payloads are the same.
    Note 2: The figure is stored in the plots_directory with the name
        "comparison_<column>.png", without any '%' symbols.

    :param requirements: A Pandas DataFrame with one row entry per payload, and
        at least the columns "Label" and "<column>".
    :param experiment: A Pandas DataFrame similar to requirements.
    :raise: AssertionError if:
        * requirements is not a DataFrame
        * experiment is not a DataFrame
        * column is not a string
        * plots_directory is not a directory
        * title is not a string
    """
    # Validate arguments
    assert(isinstance(requirements, pandas.DataFrame))
    assert(isinstance(experiment, pandas.DataFrame))
    assert(isinstance(column, str))
    assert(isdir(plots_directory))
    assert(isinstance(title, str))

    color_codes = [
        ['#09487e'],  # Blues for results
        ['#ff0000'],  # Reds for requirements
    ]

    # Agregate requirements and experiment data in one DataFrame
    summaries_data = requirements
    summaries_data = summaries_data.append(experiment, sort=False)
    summaries_data.Bytes = summaries_data.Bytes.astype(str)

    fig, ax = plt.subplots()
    i = 0
    # Make one series for each 'Label' (one for reqs and one for summary)
    for key, grp in summaries_data.groupby(['Label']):
        key = '{} {}'.format(key, column)
        ax = grp.plot(
            ax=ax,
            style='.-',
            x='Bytes',
            y=column,
            label=key,
            color=color_codes[i],
        )
        ax.set_xticks(range(len(grp['Bytes'])))
        i += 1 if i < (len(color_codes) - 1) else 0

    plt.xlabel('Payload [Bytes]')
    plt.ylabel('Latency [us]')
    plt.legend(loc='best')
    plt.grid()
    plt.title('Comparison {}'.format(title))
    plt.savefig(
        '{}/comparison_{}.png'.format(plots_directory, title.replace('%', ''))
    )
    plt.close(fig)


def plot_and_check(
    requirements,
    experiment,
    plots_directory
):
    """
    Plot and check experiment data against requirements.

    Plot the experiment data and requirements data series.
    Check whether the experiment data meet the requirements.

    :param requirements: Pandas DataFrame containing the requirements for a
        specific experiment type.
    :param experiment: Pandas DataFrame containing the summary of a specific
        experiment type.
    :param plots_directory: A directory to place the resulting plots.
    :raise: AssertionError if requirements or experiment are not Pandas
        Dataframes.
    :return: The return of "check_requirements()"
    """
    # Validate arguments
    assert(isinstance(requirements, pandas.DataFrame))
    assert(isinstance(experiment, pandas.DataFrame))

    # Columns to check
    columns = ['Median', '99%', 'Max']
    # Plot comparison for each column
    for column in columns:
        plot(
            requirements=requirements,
            experiment=experiment,
            column=column,
            plots_directory=plots_directory,
            title=column.lower()
        )
    # Check the requirements
    return check_requirements(requirements, experiment)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="""
            Script to check the results of a latency experiment,
            performed with "latency_run_experiment.bash", against a set
            of requirements given as a CSV file in the format output by
            "latency_determine_requirements.py".
            The script looks for summary files as output by
            "latency_process_results.py" in the <experiment_directory>
            directory, i.e. summary files named as:
            "measurements_<experiment_type>_summary.csv". An exit code of
            0 indicates that all check passed, else, some check failed.
            The script generates check plots in the <plots_directory>
            directory, as well as CSV files for each check, placed in the
            <experiment_directory> directory.
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
        '--experiment_directory',
        help="The experiment's results directory",
        type=directory_type,
        required=True
    )
    parser.add_argument(
        '-P',
        '--print_summaries',
        action='store_true',
        help='Whether to print a table with the summaries for each result',
        required=False
    )
    args = parser.parse_args()
    plots_directory = args.plots_directory
    requirements = args.requirements
    experiment_directory = args.experiment_directory
    print_summaries = args.print_summaries

    # Check arguments
    assert(isfile(requirements))
    assert(isdir(experiment_directory))
    exit_code = 0

    # Get list of summaries by list all files in directory and selecting the
    # ones containing 'summary' in the name.
    summaries = sorted(
        [
            '{}/{}'.format(
                experiment_directory,
                f
            ) for f in listdir(experiment_directory) if isfile(
                '{}/{}'.format(
                    experiment_directory,
                    f
                )
            ) and 'summary' in f
        ]
    )

    total_checks = 0
    passed_checks = 0
    # Get requirements
    requirements = pandas.read_csv(requirements)

    # Check each summary separately
    for summary in summaries:
        # Get experiment type
        exp_type = experiment_type(summary)
        print('Checking {}  '.format(exp_type), end='', flush=True)

        # Get requirements for experiment type
        reqs = requirements[requirements['Experiment type'] == exp_type]
        reqs.insert(0, 'Label', 'requirements')
        reqs = reqs.reset_index(drop=True)

        # Get experiment summary data
        experiment = pandas.read_csv(
            summary,
            usecols=[
                'Bytes',
                'Median',
                '99%',
                'Max'
            ]
        )
        experiment['Experiment type'] = exp_type
        experiment.insert(0, 'Label', 'experiment')

        # Plot experiment and requirements, and check the experiment
        status, column_checks = plot_and_check(
            requirements=reqs,
            experiment=experiment,
            plots_directory='{}/measurements_{}'.format(
                plots_directory,
                exp_type
            )
        )

        # Checkup check status
        if status == 0:
            print('[PASSED]')
        else:
            print('[FAILED]')
            exit_code += 1

        # Generate check report
        checks = pandas.DataFrame()
        for check in column_checks:
            checks = checks.append(column_checks[check], sort=False)
        checks = checks.reset_index(drop=True)
        checks.to_csv(
            '{}/checks_{}.csv'.format(experiment_directory, exp_type),
            float_format='%.3f',
            index=False
        )

        # Count passed check
        total_checks += len(checks.index)
        passed_checks += len(checks[checks['Status'] == 'passed'])
        if print_summaries:
            print(checks)
            print('----------------------------')

    if not print_summaries:
        print('----------------------------')

    # Print analysis summary and exit with exit_code
    print(
        '{:.3f}% checks passed: ({}/{})'.format(
            passed_checks * 100 / total_checks,
            passed_checks,
            total_checks,
        )
    )
    if exit_code > 0:
        print(
            (
                'Experiment check failed: ' +
                "{} sub-experiment don't meet the requirements".format(
                     exit_code
                )
            )
        )
    else:
        print('Experiment check passed')
    exit(exit_code)
