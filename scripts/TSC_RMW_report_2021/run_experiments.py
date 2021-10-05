"""Script to run a batch of performance experiments."""
import argparse
import itertools
import json
import multiprocessing
import os
import subprocess
from sys import platform


class Experiment:
    """."""

    def __init__(
        self,
        log_dir,
        communication,
        dds_domain,
        topic,
        rate,
        num_subs,
        reliability,
        durability,
        history_kind,
        history_depth,
        max_runtime,
        zero_copy,
        rmw_implementation,
        process_mode,
        roundtrip_mode,
        fastdds_xml_file='',
    ):
        """."""
        self.log_dir = log_dir
        self.communication = communication
        self.dds_domain = dds_domain
        self.topic = topic
        self.rate = rate
        self.num_subs = num_subs
        self.reliability = reliability
        self.durability = durability
        self.history_kind = history_kind
        self.history_depth = history_depth
        self.max_runtime = max_runtime
        self.rmw_implementation = rmw_implementation
        self.process_mode = process_mode
        self.zero_copy = (zero_copy if self.process_mode != 'intra-process'
                          else 'OFF')
        # Only take roundtrip argument into account if the process_mode is
        # something other than "intra-process".
        self.roundtrip_mode = (roundtrip_mode if self.process_mode != 'intra-process'
                          else 'none')
        self.fastdds_xml_file = fastdds_xml_file
        self.commands = self.__generate_commands()

    def get_num_subs(self):
        """."""
        return int(self.num_subs)

    def get_process_mode(self):
        """."""
        return self.process_mode

    def get_dir_name(self):
        """."""
        return self.get_dir_name

    def get_commands(self):
        """."""
        return self.commands

    def __generate_commands(self):
        """."""
        if (platform == "win32"):
            command = 'set "ROS_DOMAIN_ID={}" '.format(self.dds_domain)
            command += '&& set "RMW_IMPLEMENTATION={}" '.format(self.rmw_implementation)
            if (self.rmw_implementation == 'rmw_fastrtps_cpp' and
                    self.fastdds_xml_file != ''):
                command += '&& set "RMW_FASTRTPS_USE_QOS_FROM_XML=1" '
                command += '&& set "FASTRTPS_DEFAULT_PROFILES_FILE={}" '.format(
                    self.fastdds_xml_file
                )
            command += '&& '
        else:
            command = 'ROS_DOMAIN_ID={} '.format(self.dds_domain)
            command += 'RMW_IMPLEMENTATION={} '.format(self.rmw_implementation)
            if (self.rmw_implementation == 'rmw_fastrtps_cpp' and
                    self.fastdds_xml_file != ''):
                command += 'RMW_FASTRTPS_USE_QOS_FROM_XML=1 '
                command += 'FASTRTPS_DEFAULT_PROFILES_FILE={} '.format(
                    self.fastdds_xml_file
                )
        command += 'ros2 run performance_test perf_test'
        command += ' --communication {}'.format(self.communication)
        command += ' --dds-domain_id {}'.format(self.dds_domain)
        command += ' --topic {}'.format(self.topic)
        command += ' --msg {}'.format(self.topic)
        command += ' --rate {}'.format(self.rate)
        if self.reliability == 'reliable':
            command += ' --reliable'
        if self.durability == 'transient':
            command += ' --transient'
        if self.history_kind == 'keep_last':
            command += ' --keep-last'
        command += ' --history-depth {}'.format(self.history_depth)
        command += ' --max-runtime {}'.format(self.max_runtime)
        log_file = '{}/{}_{}_{}_{}_{}_{}_{}'.format(
            dir_name,
            self.reliability,
            self.durability,
            self.history_kind,
            self.history_depth,
            self.max_runtime,
            self.process_mode,
            self.zero_copy
        )
        # Append XML filename w/o extension to log name if needed
        if self.rmw_implementation == 'rmw_fastrtps_cpp':
            # XML file name
            log_file += '_{}'.format(
                self.fastdds_xml_file.split('/')[-1].split('.')[-2]
            )

        if self.process_mode == 'intra-process':
            command += ' -p 1'
            command += ' -s {}'.format(self.num_subs)
            command += ' -l "{}"'.format(log_file)
            return {'pubsub': command}
        elif self.process_mode == 'inter-process':
            if self.roundtrip_mode == 'main':
                command_pub = '{} --roundtrip-mode Main -l "{}"'.format(command, log_file)
                return {
                    'pub': command_pub,
                }
            elif self.roundtrip_mode == 'relay':
                command_sub = '{} --roundtrip-mode Relay -l "{}"'.format(command, log_file)
                return {
                    'sub': command_sub,
                }
            else:
                # In the inter-process case, there is one process with one pub
                # and as many processes with 1 sub as specified in
                # config['num_subs']
                command_pub = '{} -p 1 -s 0 -l "{}"'.format(command, log_file)
                command_sub = '{} -p 0 -s 1 -l "{}"'.format(command, log_file)
                return {
                    'pub': command_pub,
                    'sub': command_sub
                }

        return None

    def __eq__(self, other):
        """."""
        return (isinstance(other, Experiment) and
                self.log_dir == other.log_dir and
                self.communication == other.communication and
                self.dds_domain == other.dds_domain and
                self.topic == other.topic and
                self.rate == other.rate and
                self.num_subs == other.num_subs and
                self.reliability == other.reliability and
                self.durability == other.durability and
                self.history_kind == other.history_kind and
                self.history_depth == other.history_depth and
                self.max_runtime == other.max_runtime and
                self.zero_copy == other.zero_copy and
                self.rmw_implementation == other.rmw_implementation and
                self.process_mode == other.process_mode and
                self.roundtrip_mode == other.roundtrip_mode and
                self.fastdds_xml_file == other.fastdds_xml_file)


def execute_comand(command):
    """Run an experiment command."""
    print('Command: {}'.format(command))
    experiment = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # If there was any error, then print output for debugging
    if experiment.returncode != 0:
        print('The experiment returned {}'.format(
            experiment.returncode)
        )
        print('---------------------')
        print(experiment.stdout)
        print('---------------------')
        print(experiment.stderr)


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
    parser.add_argument(
        '-r',
        '--run_experiments',
        help='Whether to run the generated commands.',
        action='store_true',
        required=False,
    )
    # Load config
    args = parser.parse_args()
    run_experiments = args.run_experiments
    config_file = args.config_file
    config = {}
    with open(config_file) as f:
        config = json.load(f)

    # Make sure the directory end with '/'
    if config['log_directory'].endswith('/'):
        log_dir = config['log_directory']
    else:
        log_dir = config['log_directory'] + '/'
    log_dir = os.path.abspath(log_dir)

    experiment_length = config['perf_test']['max_runtime']
    combinations = list(
        itertools.product(
            config['topics'],
            config['rates'],
            config['num_subs'],
            config['perf_test']['reliability'],
            config['perf_test']['durability'],
            config['perf_test']['history_kind'],
            config['perf_test']['history_depth'],
            config['perf_test']['max_runtime'],
            config['rmw_implementations'],
            config['fastdds_xml_files'],
            config['process_mode'],
            config['perf_test']['zero_copy'],
        )
    )

    experiments = []
    for communication in config['communication']:
        for combination in combinations:
            dir_name = '{}/{}/{}/rate_{}/subs_{}'.format(
                log_dir,
                communication,
                combination[8],  # rmw_implementation
                combination[1],  # rate
                combination[2]   # number of subscribers
            )
            # Create the directory only if the experiment is meant to be run
            if run_experiments and not os.path.exists(dir_name):
                os.makedirs(dir_name)
            # Build the command
            xml_file = (
                combination[9] if (
                        combination[9] != '' and
                        combination[8] == 'rmw_fastrtps_cpp'
                    ) else ''
            )
            experiment = Experiment(
                log_dir=dir_name,
                communication=communication,
                dds_domain=config['perf_test']['dds_domain'],
                topic=combination[0],
                rate=combination[1],
                num_subs=combination[2],
                reliability=combination[3],
                durability=combination[4],
                history_kind=combination[5],
                history_depth=combination[6],
                max_runtime=combination[7],
                zero_copy=combination[11],
                rmw_implementation=combination[8],
                process_mode=combination[10],
                roundtrip_mode=config['roundtrip_mode'],
                fastdds_xml_file=xml_file
            )
            if experiment not in experiments:
                experiments.append(experiment)

    if len(experiments) > 0 and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    pubsub_cmds = []
    pub_cmds = []
    sub_cmds = []
    for experiment in experiments:
        if experiment.get_process_mode() == 'intra-process':
            if (experiment.get_commands() is not None and
                    'pubsub' in experiment.get_commands() and
                    experiment.get_commands()['pubsub'] not in pubsub_cmds):
                pubsub_cmds.append(experiment.get_commands()['pubsub'])
        elif experiment.get_process_mode() == 'inter-process':
            if experiment.get_commands() is not None:
                if ('pub' in experiment.get_commands()  and
                        experiment.get_commands()['pub'] not in pub_cmds):
                     pub_cmds.append(experiment.get_commands()['pub'])
                if ('sub' in experiment.get_commands() and
                        experiment.get_commands()['sub'] not in sub_cmds):
                    sub_cmds.append(experiment.get_commands()['sub'])

    if len(pubsub_cmds) > 0:
        filename = '{}/pubsub_commands.log'.format(log_dir)
        print('Writing {} commands to {}'.format(len(pubsub_cmds), filename))
        with open('{}/pubsub_commands.log'.format(log_dir), 'w') as f:
            for command in pubsub_cmds:
                f.write('{}\n'.format(command))

    if len(pub_cmds) != len(sub_cmds):
        print(
            'Unequal number of inter-process commands: {}-{}'.format(
                len(pub_cmds),
                len(sub_cmds)
            )
        )

    if len(pub_cmds) > 0:
        filename = '{}/pub_commands.log'.format(log_dir)
        print('Writing {} commands to {}'.format(len(pub_cmds), filename))
        with open(filename, 'w') as f:
            for command in pub_cmds:
                f.write('{}\n'.format(command))

    if len(sub_cmds) > 0:
        filename = '{}/sub_commands.log'.format(log_dir)
        print('Writing {} commands to {}'.format(len(sub_cmds), filename))
        with open(filename, 'w') as f:
            for command in sub_cmds:
                f.write('{}\n'.format(command))

    if run_experiments is False:
        exit(0)

    num_experiments = len(experiments)
    i = 1
    for experiment in experiments:
        if experiment.get_process_mode() == 'intra-process':
            print('-------------------------------------------------')
            print(
                'Running experiment {} of {}'.format(
                    i, num_experiments
                )
            )
            execute_comand(experiment.get_commands()['pubsub'])
            print('-------------------------------------------------')
        elif experiment.get_process_mode() == 'inter-process':
            print('-------------------------------------------------')
            print(
                'Running experiment {} of {}'.format(
                    i, num_experiments
                )
            )
            processes = []
            if 'sub' in experiment.get_commands().keys():
                for j in range(0, experiment.get_num_subs()):
                    cmd = '{}_sub_{}"'.format(
                        experiment.get_commands()['sub'][:-1],
                        j
                    )
                    processes.append(
                        multiprocessing.Process(target=execute_comand, args=(cmd,))
                    )
            if 'pub' in experiment.get_commands().keys():
                cmd = '{}_pub_0"'.format(experiment.get_commands()['pub'][:-1])
                processes.append(
                    multiprocessing.Process(
                        target=execute_comand,
                        args=(cmd,)
                    ))

            for process in processes:
                process.start()
            for process in processes:
                process.join()
            print('-------------------------------------------------')
        i += 1
