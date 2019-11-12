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

"""Script to compare result trees of apex experiments."""
import argparse
import sys

import apex_comparison as ac


if __name__ == '__main__':
    # Get arguments
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        'reference_directory',
        type=ac.directory_type,
        help='Reference directory for comparison'
    )
    parser.add_argument(
        'target_directory',
        type=ac.directory_type,
        help='Target directory for comparison'
    )
    parser.add_argument(
        '-R',
        '--rates',
        nargs='*',
        default=['20', '50', '1000'],
        help='The expected rates sub-directories'
    )
    parser.add_argument(
        '-S',
        '--subs',
        nargs='*',
        default=['1', '3', '10'],
        help='The expected # of subscribers sub-directories'
    )
    parser.add_argument(
        '-l',
        '--latency_threshold',
        type=ac.percentage_float,
        help='A tolerance percentage over the reference latency',
        required=False,
        default=5
    )
    parser.add_argument(
        '-r', '--rss_threshold',
        type=ac.percentage_float,
        help='A tolerance percentage over the reference RSS',
        required=False,
        default=5
    )
    parser.add_argument(
        '-j',
        '--jitter_threshold',
        type=ac.percentage_float,
        help='A tolerance percentage over the reference jitter',
        required=False,
        default=5
    )
    parser.add_argument(
        '-p',
        '--print_results',
        type=ac.bool_type,
        help='Enable result printing and logging',
        required=False,
        default=True
    )
    parser.add_argument(
        '-o',
        '--output',
        help='Name for the output file.',
        required=False,
        default='comparison_<timestamp>.log'
    )
    args = parser.parse_args()

    ref_dir = args.reference_directory
    target_dir = args.target_directory
    rates = args.rates
    num_subs = args.subs
    latency_threshold = args.latency_threshold
    rss_threshold = args.rss_threshold
    jitter_threshold = args.jitter_threshold
    print_results = args.print_results
    output_file = args.output
    if output_file == 'comparison_<timestamp>.log':
        output_file = None

    # Get logger configured logger
    logger = ac.get_logger(output_file, print_results)

    # Get subdirectory names
    sub_dirs = ac.get_subdirectories(
        rates=rates, num_subs=num_subs
    )

    # Get full path file names
    ref_files_list = ac.get_file_names(ref_dir, sub_dirs)
    target_files_list = ac.get_file_names(target_dir, sub_dirs)

    # Check whether there are the same number or ref and target files
    if len(ref_files_list) != len(target_files_list):
        msg = ('Error: There are NOT the same number of ' +
               'REFERENCE and TARGET files')
        logger.error(msg)
        logger.error('')
        sys.exit(1)

    # Begin comparisons
    exit_value = 0  # An exit value of 0 means signifies
    for i in range(0, len(ref_files_list)):

        try:
            comparison = ac.compare_files(
                ref_file=ref_files_list[i],
                target_file=target_files_list[i],
                latency_threshold=latency_threshold,
                jitter_threshold=jitter_threshold,
                rss_threshold=rss_threshold
            )

            if comparison['result'] is False:
                exit_value = 1

            # Log results
            ac.log_comparison_result(
                logger,
                ref_files_list[i],
                target_files_list[i],
                comparison,
            )
        except AssertionError as e:
            logger.error(e)
            exit_value = 1  # An exit value of 1 signifies failure
        except Exception as e:
            logger.error('Exception occurred: {}'.format(e))
            exit_value = 1  # An exit value of 1 signifies failure

    logger.info('Script exit value: {}'.format(exit_value))
    sys.exit(exit_value)
