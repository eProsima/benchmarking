"""Script to run a batch of performance experiments."""
import argparse
import itertools
import json
import os
import subprocess


def assert_list_of_type(list_object, element_type):
    """."""
    assert isinstance(list_object, list)
    for element in list_object:
        assert isinstance(element, element_type)


def validate_configuration(config_file):
    """
    Validate the JSON configuration file.

    :param config_file: The configuration file.
    :return: A dictionary with the configuration.
    """
    # Load config
    config = {}
    with open(config_file) as f:
        config = json.load(f)

    # Check mandatory fields
    mandatory_fields_dict = {
        'rmw_implementation': 'list of strings',
        'log_directory': 'string',
        'rates': 'list of integers',
        'topics': 'list of strings',
        'dds_domain_id': 'integer',
        'reliability': 'list of strings',
        'durability': 'list of strings',
        'keep_last': 'boolean',
        'max_runtime': 'integer',
        'num_subs': 'list of integers',
    }

    try:
        # Check mandatory fields
        assert set(mandatory_fields_dict.keys()).issubset(config.keys())
        # Check types
        assert_list_of_type(config['rmw_implementation'], str)
        assert isinstance(config['log_directory'], str)
        assert_list_of_type(config['rates'], int)
        assert_list_of_type(config['topics'], str)
        assert isinstance(config['dds_domain_id'], int)
        assert_list_of_type(config['reliability'], str)
        assert_list_of_type(config['durability'], str)
        assert isinstance(config['keep_last'], bool)
        assert isinstance(config['max_runtime'], int)
        assert_list_of_type(config['num_subs'], int)
    except:
        print('CONFIGURATION ERROR. Mandatory configuration elements and types are:')
        print(json.dumps(mandatory_fields_dict, indent=4))
        exit(1)

    # Check optional fields
    if 'history_depth' in config:
        if not isinstance(config['history_depth'], int):
            print('CONFIGURATION ERROR: history_depth must be an integer')

    # Make sure the directory is not empty and does not end with '/'
    if config['log_directory'] == '':
        config['log_directory'] = '.'
    elif config['log_directory'].endswith('/'):
        config['log_directory'] = config['log_directory'][-1]
    else:
        config['log_directory'] = config['log_directory']
    config['log_directory'] = os.path.abspath(config['log_directory'])
    return config


if __name__ == '__main__':
    # Get arguments
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-c',
        '--config_file',
        help='JSON configuration file',
        required=True,
    )
    # Load config
    args = parser.parse_args()
    config = validate_configuration(args.config_file)

    history_depth = 1000  # Default value for Apex tests
    experiment_length = config['max_runtime']
    combinations = list(
        itertools.product(
            config['topics'],
            config['rates'],
            config['num_subs'],
            config['reliability'],
            config['durability'],
        )
    )

    commands = []
    for rmw_implementation in config['rmw_implementation']:
        for combination in combinations:
            dir_name = '{}/{}/rate_{}/subs_{}'.format(
                config['log_directory'],
                rmw_implementation,
                combination[1],
                combination[2]
            )
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            # Build the command
            command = 'ROS_DOMAIN_ID={} '.format(config['dds_domain_id'])
            command += ' RMW_IMPLEMENTATION={}'.format(rmw_implementation)
            command += ' ros2 run performance_test perf_test'
            command += ' --communication ROS2'
            command += ' --topic {}'.format(combination[0])
            command += ' --rate {}'.format(combination[1])
            command += ' -p 1'
            command += ' -s {}'.format(combination[2])
            if combination[3] == 'reliable':
                command += ' --reliable'
            if combination[4] == 'transient':
                command += ' --transient'
            if config['keep_last'] is True:
                command += ' --keep_last'
                if 'history_depth' in config:
                    history_depth = config['history_depth']
                command += ' --history_depth {}'.format(history_depth)
            command += ' --max_runtime {}'.format(experiment_length)

            log_file = '{}/{}_{}'.format(
                dir_name,
                combination[3],
                combination[4]
            )
            if config['keep_last'] is True:
                log_file += '_keep_last_{}'.format(history_depth)
            else:
                log_file += '_keep_all'
            command += " -l '{}'".format(log_file)
            commands.append(command)

    with open('commands.log', 'w') as commands_log:
        for command in commands:
            commands_log.write('{}\n'.format(command))

    i = 1
    for command in commands:
        print('-------------------------------------------------')
        print('Running experiment {} of {}'.format(i, len(commands)))
        print('Command: {}'.format(command))
        experiment = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        i += 1
    print('-------------------------------------------------')
