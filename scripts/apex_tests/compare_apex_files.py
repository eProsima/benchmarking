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

"""Script to compare results of 2 files of apex experiments."""
import argparse
import sys

import apex_comparison as ac


if __name__ == '__main__':
    # Get arguments
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        'reference_file',
        type=ac.file_type,
        help='Reference directory for comparison'
    )
    parser.add_argument(
        'target_file',
        type=ac.file_type,
        help='Target directory for comparison'
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

    ref_file = args.reference_file
    target_file = args.target_file
    latency_threshold = args.latency_threshold
    rss_threshold = args.rss_threshold
    jitter_threshold = args.jitter_threshold
    print_results = args.print_results
    output_file = args.output
    if output_file == 'comparison_<timestamp>.log':
        output_file = None

    # Get logger configured logger
    logger = ac.get_logger(output_file, print_results)

    # Begin comparison
    exit_value = 0  # An exit value of 0 means signifies

    try:
        comparison = ac.compare_files(
            ref_file=ref_file,
            target_file=target_file,
            latency_threshold=latency_threshold,
            jitter_threshold=jitter_threshold,
            rss_threshold=rss_threshold
        )

        if comparison['result'] is False:
            exit_value = 1

        # Log results
        ac.log_comparison_result(
            logger,
            ref_file,
            target_file,
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
