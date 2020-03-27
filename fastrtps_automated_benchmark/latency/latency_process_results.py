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
from os import makedirs
from os.path import isdir

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np

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
    args = parser.parse_args()
    plots_directory = args.plots_directory
    raw_csv = args.raw_csv
    output_csv = args.output_csv

    # Make sure output file only contains headers
    with open(output_csv, 'w') as output_file:
        output_file.write('Bytes,Samples,Max,Min,Mean,Median,Stdev,Mean jitter,Max jitter,90%,99%,99.99%\n')

    print('----------------------------')
    raw_data = pandas.read_csv(raw_csv)
    payloads = raw_data['Payload [Bytes]'].unique()
    for payload in payloads:
        sample_series = raw_data[raw_data['Payload [Bytes]'] == payload]
        sample_series = sample_series.reset_index(drop=True)

        # Jitter
        jitters = []
        latencies = sample_series['Latency [us]']
        for i in range(1, len(latencies)):
            jitters.append(abs(latencies[i] - latencies[i-1]))

        # CSV summary file
        print('Adding entry for payload {} Bytes to {}'.format(payload, output_csv))
        with open(output_csv, 'a') as output_file:
            output_file.write(
                '{},{},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f},{:.3f}\n'.format(
                    payload,
                    len(latencies),
                    np.max(latencies.to_list()),
                    np.min(latencies.to_list()),
                    np.mean(latencies.to_list()),
                    np.median(latencies.to_list()),
                    np.std(latencies.to_list()),
                    np.mean(jitters),
                    np.max(jitters),
                    np.percentile(latencies.to_list(), 90),
                    np.percentile(latencies.to_list(), 99),
                    np.percentile(latencies.to_list(), 99.99),
                )
            )

        # Histogram
        fig_title = '{}/histogram_{}.png'.format(plots_directory, payload)
        print('Generating {}'.format(fig_title))
        fig = plt.figure()
        histogram = sample_series.hist(bins=100, column='Latency [us]')
        plt.xlabel('Latency [us]')
        plt.ylabel('Number of occurrences')
        plt.title('Latency Histogram - {} Bytes'.format(payload))
        plt.savefig(fig_title)
        plt.close(fig)

        # Sample series
        fig_title = '{}/series_{}.png'.format(plots_directory, payload)
        print('Generating {}'.format(fig_title))
        sample_series = sample_series.plot(y='Latency [us]')
        plt.xlabel('Sample number')
        plt.ylabel('Latency [us]')
        plt.title('Latency Series - {} Bytes'.format(payload))
        plt.savefig(fig_title)
        plt.close(sample_series.get_figure())
        print('----------------------------')

