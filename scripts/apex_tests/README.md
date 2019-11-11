# Scripts for Apex performance tests
This directory contains a set of scripts used to run and analyze performance results obtained with [ApexAI's performance test framework](https://gitlab.com/ApexAI/performance_test/).

## Scripts brief description
* [apex_run_experiments.py](apex_run_experiments.py) takes a configuration file in the form of [apex_experiments_config.json](apex_experiments_config.json) and runs all the possible combinations of `perf_test`.
* [apex_experiments_config.json](apex_experiments_config.json) is full example a configuration file for [apex_run_experiments.py](apex_run_experiments.py).
* [apex_compare.py](apex_compare.py) is meant to compare result files as output by ApexAI's `perf_test`.
* [apex_compare_tree.py](apex_compare_tree.py) is meant to compare two sets of similar results produced with [apex_run_experiments.py](apex_run_experiments.py).
* [apex_plot_results.py](apex_plot_results.py) generates comparison plots from two sets of results produced with [apex_run_experiments.py](apex_run_experiments.py).
* [ApexComparison.py](ApexComparison.py) contains python code used by several of the other scripts.
* [apex_parse_results.py](apex_parse_results.py) is a parser to transform ApexAI's performance test results to CSV (columns: `latency_min (ms)`, `latency_mean (ms)`, `latency_variance (ms)`, `ru_maxrss`, `cpu_usage (%)`)

## Run Apex tests
These steps assume that you have a ROS2 installation from sources, where the [ApexAI's performance test](https://gitlab.com/ApexAI/performance_test/) package is present.

1. On a new terminal, move to the root of the local ROS2 installation:
    ```bash
    cd <ros2_ws>/
    ```
1. Source the environment:
    ```bash
    source install/setup.bash
    ```
1. Checkout to the RMW implementation and dds vendor implementation test target versions
1. Build
    ```bash
    cd <ros2_ws>/
    colcon build
    ```
    1. For building ApexAI's performance tests with CycloneDDS, `<ros2_ws>/src/eclipse-cyclonedds/cyclonedds/colcon.pkg` must have the `-DBUILD_IDLC` option enabled:
        ```
        {
            "cmake-args": [ "-DBUILD_IDLC=ON" ]
        }
        ```
1. Configure the experiments to be performed in [apex_experiments_config.json](apex_experiments_config.json)
1. Run the experiments
    ```bash
    python3 apex_run_experiments.py -c apex_experiments_config.json
    ```
    This, apart from running and logging the experiments, will generate a log of all the commands run. and example would be:
    ```
    RMW_IMPLEMENTATION=rmw_fastrtps_cpp ros2 run performance_test perf_test --communication ROS2 --topic Array1k --rate 1000 -p 1 -s 10 --keep_last --history_depth 1000 --max_runtime 60 -l '/home/test/ros2_master/apex_run/rmw_fastrtps_cpp/rate_1000/subs_10/best-effort_volatile_keep_last_1000'
    RMW_IMPLEMENTATION=rmw_fastrtps_cpp ros2 run performance_test perf_test --communication ROS2 --topic Array16k --rate 1000 -p 1 -s 10 --keep_last --history_depth 1000 --max_runtime 60 -l '/home/test/ros2_master/apex_run/rmw_fastrtps_cpp/rate_1000/subs_10/best-effort_volatile_keep_last_1000'
    [...]
    ```

## Compare Apex results
One you have two sets of similar experiments (like two executions of the above example), you can compare them with:
```bash
python3 apex_compare_tree.py /home/test/ros2_master/apex_run/rmw_fastrtps_cpp_1/ /home/test/ros2_master/apex_run/rmw_fastrtps_cpp_2/ -R 1000 -S 10 -o comparison.out
```

You can also compare 2 different result files with:
```bash
python3 apex_compare.py file_1 file_2 -o comparison.out
```

## Plot results
You can plot an arbitrary number of sets of results (as output by [apex_run_experiments.py](apex_run_experiments.py)).
```bash
python3 apex_plot_results.py -r results_dir_1 results_dir_2 results_dir_3 -s label_1 label_2 label_3 -p plots_dir
```
This will generate one plot for each result type (combination of rate, number of subscribers, reliability, durability, history kind, and history depth). Each plot will have data types in the x axis, and one series for each result set, labeled with its corresponding label.

## Parse results
You can parse the results into CSV files specifying a directory containing ApexAI performance test raw output files. This will generate CSV files that are stored in the same results directory.
```bash
python3 apex_parse_results.py -r rate_1000/subs_10/
```
