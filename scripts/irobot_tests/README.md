# iRobot Performance Test Utilities
This directory contains utilities to perform experiments using [iRobot's performance test framework](https://github.com/irobot-ros/ros2-performance/).

* [topologies](topologies) contains custom topologies outside those defined by iRobot:
    * [eprosima topology](topologies/eprosima.json) is a version of the Mont Blanc topology, with the particularity that all the publishers and subscribers live within the same node.
* [xml](xml) contains xml files to configure different middleware aspects for different test-cases.