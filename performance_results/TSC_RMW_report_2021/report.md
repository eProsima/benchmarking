# Fast DDS TSC RMW report 2021

* [Benchmarking](#benchmarking)
* [Linux laptop](#performance-test-result-analysis-on-Linux-platform)
* [Raspberry Pi](#performance-test-result-analysis-on-raspberry-pi-platform)
* [Windows](#performance-test-result-analysis-on-windows-platform)

## Benchmarking

### Testing framework

Tests have been executed on Raspberry-pi 4b+, linux laptops and windows laptops.

### Benchmark tools

For the test to be reproducible, they were performed using a fork of the [Apex performance test tool](https://gitlab.com/ApexAI/performance_test.git).
This fork has the necessary changes needed for the tools to build on Windows systems.
You can get the fork [here](https://gitlab.com/MiguelCompany/performance_test), checkout commit c230727.

We have prepared a set of scripts to help automatize the launch of the tests with different configurations. These scripts include:
 * Downloading the specified [ros2.repos file](https://github.com/osrf/TSC-RMW-Reports/blob/main/humble/ros2.repos).
 * Downloading the aforementioned fork of the Apex performance tool.
 * Compiling ROS2 and the performance tool
 * Launching the tests with the configuration specified on a json file
 
All tests were executed for 5 minutes.
During this time, Apex performance tool outputs measurements every second.
This means that every test has around 300 measured samples that are statistically analysed.

### Testing setup

#### Network setup

In order to avoid external noise in the results, the experiments have been conducted in an isolated environment:

 * Devices are connected to a LAN without internet access (they are not connected to any other network).
 * To easy the process of conducting the experiments, a "gateway" machine is connected to the testing LAN,
   as well as a normal LAN, so that the testing machines can be accessed from outside the testing LAN with 2 ssh connections
   (to the gateway machine, and from there to the testing device).
   This is very useful when conducting inter-host tests, since the gateway can act as an orchestrator.
 * The WiFi interfaces were down for the experiments that do not use it (i.e., except the inter-host with WiFi experiments).


#### Tested configurations

Several configurations have been tested.
Note that the default configuration for eProsima Fast DDS is asynchronous publishing with no data-sharing,
while for Cyclone DDS it is synchronous publishing.

**Reliability**

Both best-effort and reliable configurations are tested.

**History kind and durability**

Only volatile keep-last configuration was tested.
With the kind of tests being performed, where there are no late-joiner subscribers, there is no significant difference on the results
when using transient or keep-all. In order to reduce the amount of possible lost packages on reliable configurations,
a depth of 100 was used.

**Data sizes**

In order to characterize the performance with the size of the data samples, the following data types and sizes have been used:
 * 256 B
 * 4 KB
 * 2 MB

We consider these values as examples of small, medium and large data sizes.

**Delivery rates**

In order to characterize the performance with the delivery rate, the following rates have been used:
 * 30 Hz
 * 300 Hz
 * 1000 Hz
 
We consider these values as examples of low, medium and high publication frequencies.

**Number of subscribers**

In order to characterize the performance with the number of subscribers, tests with different number of subscribers have been used:
 * 1 subscriber
 * 3 subscribers
 * 10 subscribers

**Publishing mode**

Synchronous and asynchronous publication modes have been compared.
 
**Delivery mode**

Different available delivery modes have been compared:
 * Intra-process delivery.
 * Inter-process delivery using data-sharing.
 * Inter-process delivery without data-sharing.
 * Inter-host delivery.

## Performance test result analysis on Linux platform

### Linux laptop specifications

| Board model | Architecture | CPUs | CPU max MHz | Kernel version | OS |
|-|-|-|-|-|-|
| Intel(R) Core(TM) i7-7700HQ CPU @ 2.80GHz | x86_64 | 4 | 3800 | 5.4.0-73-generic | Ubuntu 20.04.2 LTS |

### Latency

 * Generally speaking, Fast DDS synchronous mode has lower latency than Cyclone DDS synchronous mode
 * Fast DDS asynchronous mode has higher latencies, which is expected, since some of the messages will be waiting for the asynchronous thread to wake up.
 * In all cases, the smaller latencies are obtained with Fast DDS using data-sharing delivery.
 * Cyclone DDS has very poor latencies for large data sizes, around 70% larger than Fast DDS asynchronous mode and 81% larger than Fast DDS synchronous mode.
 
#### Intra-process best-effort

 * Fast DDS synchronous mode has between 6% and 14% lower latencies than cyclone, depending on the number of subscribers and publishing rate
   (except for large data sizes, where Cyclone DDS has very poor latencies).

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_be_latency_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_be_latency_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_be_latency_by_size.png" width=50% height=50%>


#### Intra-process reliable

 * This case is special in the sense that Fast DDS synchronous mode and Cyclone DDS have similar latencies
   (except for large data sizes, where Cyclone DDS has very poor latencies).
 
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_re_latency_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_re_latency_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_re_latency_by_size.png" width=50% height=50%>

#### Inter-process best-effort

 * Fast DDS synchronous mode has between 7% and 17% lower latencies than cyclone, depending on the number of subscribers and publishing rate
   (except for large data sizes, where Cyclone DDS has very poor latencies).
 * Fast DDS with data-sharing is even better, with between 17% and 24% lower latencies than Cyclone DDS for small data sizes.
 * Latency increase with data size is smallest using Fast DDS with data-sharing.
 
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_be_latency_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_be_latency_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_be_latency_by_size.png" width=50% height=50%>

#### Inter-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_re_latency_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_re_latency_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_re_latency_by_size.png" width=50% height=50%>

### Throughput

 * Throughput degrades much faster with Cyclone DDS, either with the number of subscribers, the publication rate or the data size.
 * Best throughput can be achieved with FastDDS data-sharing delivery, since it has the least dependency with the number of subscribers or the data size..

#### Intra-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_be_throughput.png" width=50% height=50%>


#### Intra-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_re_throughput.png" width=50% height=50%>

#### Inter-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_be_throughput.png" width=50% height=50%>

#### Inter-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_re_throughput.png" width=50% height=50%>

### CPU

 * Fast DDS scales much better than Cyclone DDS with the number of subscribers and, specially, the data size.
 * For 2MB data sizes Fast DDS CPU usage is about two thirds of that of Cyclone DDS.
 * Fast DDS data-sharing delivery is by far the best option for large data sizes in terms of CPU.

#### Intra-process best-effort

 * For low subscriber number and low data size, there is no significant difference among the CPU usage of all configurations.
 * For large data sizes, Fast DDS scales much better in terms of CPU usage, in all its configurations.
 * Fast DDS also scales better with the number of subscribers.

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_be_cpu_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_be_cpu_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_be_cpu_by_size.png" width=50% height=50%>


#### Intra-process reliable

 * For low subscriber number and low data size, there is no significant difference among the CPU usage of all configurations.
 * For large data sizes, Fast DDS scales much better in terms of CPU usage, in all its configurations.
 * Fast DDS also scales better with the number of subscribers.

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_re_cpu_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_re_cpu_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_re_cpu_by_size.png" width=50% height=50%>

#### Inter-process best-effort

 * Fast DDS has lower CPU usage in all its configurations.
 * For large data sizes, Fast DDS scales much better in terms of CPU usage, in all its configurations.

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_be_cpu_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_be_cpu_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_be_cpu_by_size.png" width=50% height=50%>

#### Inter-process reliable

 * This is the only configuration where Fast DDS synchronous behaves worse than Cyclone DDS.
 * However, any other Fast DDS configuration has better CPU performance.
 
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_re_cpu_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_re_cpu_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_re_cpu_by_size.png" width=50% height=50%>


### Memory

Memory consumption in Fast DDS is higher than in Cyclone DDS. This was somehow expected, since Fast DDS supports many more configurations and features that require data structures residing in memory. 
This is also why all Fast DDS configurations have similar memory requirements

#### Intra-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_be_mem_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_be_mem_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_be_mem_by_size.png" width=50% height=50%>

#### Intra-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_re_mem_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_re_mem_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/intraprocess_re_mem_by_size.png" width=50% height=50%>

#### Inter-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_be_mem_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_be_mem_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_be_mem_by_size.png" width=50% height=50%>

#### Inter-process reliable
 
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_re_mem_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_re_mem_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/linux/interprocess_re_mem_by_size.png" width=50% height=50%>


## Performance test result analysis on Raspberry Pi platform

### Raspberry Pi specifications

| Board model | Architecture | CPUs | CPU max MHz | Kernel version | OS |
|-|-|-|-|-|-|
| Raspberry Pi 4 Model B Plus Rev 1.1 | aarch64 | 4 | 1500 | 5.4.0-1042-raspi | Ubuntu 20.04.1 LTS |

### Latency

 * Generally speaking, Fast DDS synchronous mode has lower latency than Cyclone DDS synchronous mode
 * Fast DDS asynchronous mode has higher latencies for inter-process deployments, which is expected, since some of the messages will be waiting for the asynchronous thread to wake up.
 * However, on intra-process deployments, Fast DDS asynchronous mode is still faster than Cyclone DDS.
 * In all cases, the smaller latencies are obtained with Fast DDS using data-sharing delivery.
 * Cyclone DDS has very poor latencies for large data sizes, around twice that of Fast DDS.
 
#### Intra-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_be_latency_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_be_latency_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_be_latency_by_size.png" width=50% height=50%>


#### Intra-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_re_latency_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_re_latency_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_re_latency_by_size.png" width=50% height=50%>

#### Inter-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_be_latency_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_be_latency_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_be_latency_by_size.png" width=50% height=50%>

#### Inter-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_re_latency_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_re_latency_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_re_latency_by_size.png" width=50% height=50%>

### Throughput

 * Best throughput can be achieved with FastDDS data-sharing delivery, since it has the least dependency with the number of subscribers or the data size.
 * Without data-sharing delivery, Fast DDS still gets four times more throughput for a single subscriber.

#### Intra-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_be_throughput.png" width=50% height=50%>

#### Intra-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_re_throughput.png" width=50% height=50%>

#### Inter-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_be_throughput.png" width=50% height=50%>

#### Inter-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_re_throughput.png" width=50% height=50%>

### CPU

 * Fast DDS scales much better than Cyclone DDS with the number of subscribers and, specially, the data size.
 * For 2MB data sizes Fast DDS CPU usage is about two thirds of that of Cyclone DDS.
 * Fast DDS data-sharing delivery is by far the best option for large data sizes in terms of CPU.

#### Intra-process best-effort

 * For low subscriber number and low data size, there is no significant difference among the CPU usage of all configurations.
 * For large data sizes, Fast DDS scales much better in terms of CPU usage, in all its configurations.
 * Fast DDS also scales better with the number of subscribers.

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_be_cpu_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_be_cpu_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_be_cpu_by_size.png" width=50% height=50%>

#### Intra-process reliable

 * For low subscriber number and low data size, there is no significant difference among the CPU usage of all configurations.
 * For large data sizes, Fast DDS scales much better in terms of CPU usage, in all its configurations.

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_re_cpu_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_re_cpu_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_re_cpu_by_size.png" width=50% height=50%>

#### Inter-process best-effort

 * Fast DDS has lower CPU usage in all its configurations.
 * For large data sizes, Fast DDS scales much better in terms of CPU usage, in all its configurations.

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_be_cpu_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_be_cpu_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_be_cpu_by_size.png" width=50% height=50%>

#### Inter-process reliable
 
 * This is the only configuration where Fast DDS synchronous behaves worse than Cyclone DDS.
 * However, any other Fast DDS configuration has better CPU performance.

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_re_cpu_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_re_cpu_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_re_cpu_by_size.png" width=50% height=50%>

### Memory

Memory consumption in Fast DDS is higher than in Cyclone DDS. This was somehow expected, since Fast DDS supports many more configurations and features that require data structures residing in memory. 
This is also why all Fast DDS configurations have similar memory requirements

#### Intra-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_be_mem_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_be_mem_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_be_mem_by_size.png" width=50% height=50%>

#### Intra-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_re_mem_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_re_mem_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/intraprocess_re_mem_by_size.png" width=50% height=50%>

#### Inter-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_be_mem_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_be_mem_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_be_mem_by_size.png" width=50% height=50%>

#### Inter-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_re_mem_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_re_mem_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/raspi/interprocess_re_mem_by_size.png" width=50% height=50%>



## Performance test result analysis on Windows platform

The [Apex performance test tool](https://gitlab.com/ApexAI/performance_test.git) used on this benchmark is not prepared for Windows platforms.
For example, it uses Unix specific OS calls to get the CPU and memory load among other things. The fork we used on this benchmark makes the tool compile on windows platforms, avoiding these OS calls. This means that we get no CPU or memory usage data for Windows platforms. We do get the latency and throughput, though.

### Windows laptop specifications

| Board model | Architecture | CPUs | CPU max MHz | OS |
|-|-|-|-|-|
| Intel(R) Core(TM) i7-4700MQ CPU @ 2.40GHz | x86_64 | 4 | 2400 | Windows 10 Enterprise  |

### Latency

 * Latency on Windows platforms seem to be around half of the latency on the other platforms.
 * Fast DDS scales much better than Cyclone DDS with the data size. The latency on Cyclone DDS for datas of 2MB is 3 times higher than on Fast DDS on inter-process deployments and as much as 5 times higher on intra-process deployments.
 
#### Intra-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/intraprocess_be_latency_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/intraprocess_be_latency_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/intraprocess_be_latency_by_size.png" width=50% height=50%>


#### Intra-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/intraprocess_re_latency_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/intraprocess_re_latency_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/intraprocess_re_latency_by_size.png" width=50% height=50%>

#### Inter-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/interprocess_be_latency_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/interprocess_be_latency_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/interprocess_be_latency_by_size.png" width=50% height=50%>

#### Inter-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/interprocess_re_latency_by_subscribers.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/interprocess_re_latency_by_rate.png" width=50% height=50%>
<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/interprocess_re_latency_by_size.png" width=50% height=50%>

### Throughput

 * In all cases, Fast DDS achieves equal or better throughput than Cyclone DDS.
 * Fast DDS scales better with the number of subscribers, and with 10 subscribers, it gets at least 50% higher throughput, and in some cases, as much as 4 times more throughput.
 

#### Intra-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/intraprocess_be_throughput.png" width=50% height=50%>

#### Intra-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/intraprocess_re_throughput.png" width=50% height=50%>

#### Inter-process best-effort

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/interprocess_be_throughput.png" width=50% height=50%>

#### Inter-process reliable

<img src="https://github.com/eProsima/benchmarking/blob/tsc_rmw_report_2021/performance_results/TSC_RMW_report_2021/fastrtps_images/windows/interprocess_re_throughput.png" width=50% height=50%>



