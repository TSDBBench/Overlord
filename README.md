# Overlord
[![Build Status](https://api.travis-ci.org/TSDBBench/Overlord.svg?branch=master)](https://travis-ci.org/TSDBBench/Overlord)

The Python and Vagrant part of [TSDBBench](http://tsdbbench.github.io/) that automatically setups and benchmarks time series databases (TSDBs).

The benchmarking is done with VMs that are automatically setup by Vagrant and are running on one of the five supported elastic infrastructures (EIs).

Different cluster sizes and configurations as well as different workloads can be used to benchmark one or more TSDBs.

The benchmark is done with [YCSB-TS](https://github.com/TSDBBench/YCSB-TS).

See [docs/index.md](docs/index.md) for a full documentation.
This documentation is also rendered at http://tsdbbench.github.io/Overlord/.

## Funding

TSDBBench received funding from the
[Federal Ministry for Economic Affairs and Energy](http://www.bmwi.de/Navigation/EN/Home/home.html)
in the context of the project [NEMAR](https://www.nemar.de/).

![BMWi](https://tsdbbench.github.io/BMWi.jpg)
