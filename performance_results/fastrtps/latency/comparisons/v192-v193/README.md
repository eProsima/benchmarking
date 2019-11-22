# v1.9.2 - v1.9.3 Comparison
We have performed latency performance test for both Fast-RTPS `v1.9.2` and `v1.9.3` (checkout the [release notes](https://eprosima-fast-rtps.readthedocs.io/en/latest/notes.html)). We wanted, not only to keep track of the performance evolution in terms of latency in the local host test case, but also to compare the behaviour in the intra-process test case. We were specially interested in the latter, since v1.9.3 incorporates an intra-process delivery mechanism, which was lacking in previous Fast-RTPS versions. To do this, we had to [modify our Latency test](https://github.com/eProsima/Fast-RTPS/pull/863) to allow for running both publisher and subscriber agents in the same process. The results are as follows:

###### Local host (different process)
![localhost comp](v192-v193.png)
*Figure 1: Local host comparison (min, mean, median, and 99% percentile)*

![localhost comp max](v192-v193_maxima.png)
*Figure 2: Local host comparison (maxima)*

###### Intra-process
![intraprocess comp](v192-v193_intraprocess.png)
*Figure 3: Intra-process comparison (min, mean, median, and 99% percentile)*

###### Jitter
![jitter comp](v192-v193_jitter_mean.png)
*Figure 4: Jitter mean*

![jitter comp max](v192-v193_jitter_maxima.png)
*Figure 5: Jitter maxima*

It is clear to see that, although `v1.9.3` performs similarly to `v1.9.2`, there are improvements in the mean jitter, mean that `v1.9.3` latency is more stable throughout the execution. Furthermore, as was expected, the intra-process delivery feature improves performance significantly, delivering a much lower and stable latency.