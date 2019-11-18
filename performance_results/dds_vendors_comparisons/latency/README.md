# Latency tests
This directory contains latency results obtained by running the latency test tools that each implementation vendor provides.  The experiments are performed both for several case scenarios:
* [Intra-process configuration](intraprocess): the publisher and the subscriber run in the same process.
* [Local host configuration](localhost): the publisher and the subscriber run in the same machine but different processes.
* [Dual host configuration](dualhost): the publisher and the subscriber run in separate machines connected to a local network via ethernet.

To replicate the results exposed here, look at:
* [Intra-process experiments log](intraprocess/README.md).
* [Local host experiments log](localhost/README.md).
* [Dual host experiments log](dualhost/README.md).
