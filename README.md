# Overlord
[![Build Status](https://api.travis-ci.org/TSDBBench/Overlord.svg?branch=master)](https://travis-ci.org/TSDBBench/Overlord)

The Python and Vagrant part of [TSDBBench](http://tsdbbench.github.io/) that automatically setups and benchmarks time series databases (TSDBs).

The benchmarking is done with VMs that are automatically setup by Vagrant and are running on one of the five supported elastic infrastructures (EIs).

Different cluster sizes and configurations as well as different workloads can be used to benchmark one or more TSDBs.

The benchmark is done with [YCSB-TS](https://github.com/TSDBBench/YCSB-TS).

See [docs/index.md](docs/index.md) for a full documentation.
This documentation is also rendered at http://tsdbbench.github.io/Overlord/.

## License

Copyright (c) 2015-2017 Contributors to TSDBBench

This program and the accompanying materials are made available under the terms of the Apache Software License 2.0 which is available at https://www.apache.org/licenses/LICENSE-2.0.

SPDX-License-Identifier: Apache-2.0

There might files be included which come from other sources.
So, this license statement does not hold for files contained in the `files/` subfolders inside "vagrant_files/" and binary files such as `daemonize`.
Please double-check the license for each file before working with Overlord or distributing it.

## Funding

TSDBBench received funding from the
[Federal Ministry for Economic Affairs and Energy](http://www.bmwi.de/Navigation/EN/Home/home.html)
in the context of the project [NEMAR](https://www.nemar.de/).

![BMWi](https://tsdbbench.github.io/BMWi.jpg)
