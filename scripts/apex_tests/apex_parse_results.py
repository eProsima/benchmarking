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

import argparse
import csv
import os

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
        'ru_nsignals', 'ru_nvcsw', 'ru_nivcsw', 'cpu_usage (%)'
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

if __name__ == '__main__':
    # Define arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-r',
        '--results_dir',
        help='The raw results directory',
        required=True
    )
    # GET ARGUMENTS
    args = parser.parse_args()
    results_dir = os.path.abspath(args.results_dir)

    raw_files = [os.path.join(results_dir, f) for f in os.listdir(results_dir) if os.path.isfile(os.path.join(results_dir, f))]
    columns_of_interest = [
        'latency_min (ms)',
        'latency_mean (ms)',
        'latency_variance (ms)',
        'ru_maxrss',
        'cpu_usage (%)'
    ]
    headers = ''
    for column in columns_of_interest:
        headers = '{},{}'.format(headers, column)
    headers = headers[1:]

    for raw_file in raw_files:
        if raw_file.endswith('parsed'):
            continue
        results = read_file_results(raw_file, columns_of_interest)
        csv_file = '{}_parsed'.format(raw_file)
        with open(csv_file, 'w') as csvfile:
            csvfile.write('{}\n'.format(headers))
            i = 0
            while i < len(results['latency_min (ms)']):
                entry = ''
                for column in columns_of_interest:
                    entry = '{},{}'.format(entry, results[column][i])
                entry = entry[1:]
                i += 1
                csvfile.write('{}\n'.format(entry))
        print('{} generated'.format(csv_file))
