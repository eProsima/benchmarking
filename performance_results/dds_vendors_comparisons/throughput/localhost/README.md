# Experiments' log
With the purpose of replicability, this file details the configuration used to perform each experiment.

## Last comparison (experiment 2019-11-04_15-39-11)
![](comparisons/2019-11-04_15-39-11.png)

## 2019-11-04_15-39-11

### Testing environment
* Location: eProsima’s facilities
* Machine: PowerEdge R330 e34s
    * Architecture: x86_64
    * CPU(s): 8
    * Thread(s) per core: 2
    * Model name: Intel(R) Xeon(R) CPU E3-1230 v6 @ 3.50GHz
    * Kernel: 4.15.0-64-generic
    * OS: Ubuntu 18.04.2 LTS bionic
    * Buffers' size:
        * net.core.rmem_default = 21299200
        * net.core.rmem_max = 21299200
        * net.ipv4.udp_mem = 102400 873800 21299200
        * net.core.netdev_max_backlog = 30000

### Test configuration
* Transport: UDPv4
* Reliability: RELIABLE
* History kind: KEEP_ALL
* Durability: VOLATILE
* Message sizes [Bytes]: 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, and 16384
* Recovery times [ms]: 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
* Demands [messages]: 100, 200, 500, 1000, 10000, 20000, 30000, 40000, 50000

### Software versions
* Fast-RTPS commit: 0bcafbde1c6fa3ef7285819980f932df910dba61
* CycloneDDS commit: aa5236dea46b82e6db26a0c87b90cedeca465524
* OpenSplice version: v6.9

### Software patches
* In CycloneDDS throughput test, the user specifies a payload size for the message. However, the total size of every message is a combination of a sequence number, the message number, and that payload, which results in 8 bytes more than what the user specified. To have a message of the actual user size (including data, message number, and sequence number), [cyclonedds_throughput_publisher.patch](../patches/cyclonedds_throughput_publisher.patch) is applied to `publisher.c`. This patch also disables the batching feature, since this would queue messages and group them until they filled a UDP datagram (point at where they are sent), which is a different behaviour than what is expected of a throughput test.
* To display the message size after applying the previous patch, [cyclonedds_throughput_subscriber.patch](../patches/cyclonedds_throughput_subscriber.patch) is applied to `subscriber.c`.
* [opensplice_throughput_implementation.patch](../patches/opensplice_throughput_implementation.patch) patches OpenSplice's `implementation.cpp` to adjust the message size in the same manner as for CycloneDDS.
* To set the appropriate reliability to OpenSpice's `Throughput` example, [opensplice_throughput_entities.patch](../patches/opensplice_throughput_entities.patch) is applied to entities.cpp
