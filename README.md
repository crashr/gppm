# gppm
![gppm-banner](https://github.com/user-attachments/assets/af0a6d7b-818c-476f-b3e3-9217b848c5c7)


gppm power process manager

gppm is designed for use with llama.cpp and NVIDIA Tesla P40 GPUs. The standalone llama.cpp currently lacks functionality to reduce the power consumption of these GPUs in idle mode. Although there is a patch for llama.cpp, it switches the performance mode for all GPUs simultaneously, which can disrupt setups where multiple llama.cpp instances share one or more GPUs. Implementing a communication mechanism within llama.cpp to manage task distribution and GPU status is complex. gppm addresses this challenge externally, providing a more efficient solution.
gppm allows you to define llama.cpp instances as code, enabling automatic spawning, termination, and respawning.

  
## Table of Contents

- [How it works](#how-it-works)
- [Quickstart](#quickstart)
- [Installation](#installation)
- [Command line interface](#command-line-interface)
- [Configuration](#configuration)

## How it works

gppm uses [nvidia-pstate](https://github.com/sasha0552/nvidia-pstate) under the hood which makes it possible to switch the performance state of P40 GPUs at all. gppm must be installed on the host where the GPUs are installed and llama.cpp is running. gppm monitors llama.cpp's output to recognize tasks and on which GPU lama.cpp runs them on and with this information accordingly changes the performance modes of installed P40 GPUs. It can manage any number of GPUs and llama.cpp instances. gppm switches each GPU to a low performance state as soon as none of the existing llama.cpp instances is running a task on that particular GPU and sets it into high performancemode as soon as the next task is going to be run. In doing so, gppm is able to control all GPUs independently of each other. gppm is designed as a wrapper and as such you have all llama.cpp instances configured at one place.
    
## Quickstart

Clone the repository and cd into it:

```shell
git clone https://github.com/crashr/gppm
cd gppm
```

Edit the following files to your needs:

* gppmd/config.yaml
* gppmd/llamacpp_configs/examples.yaml 

In a separate terminal run nvidia-smi to monitor the llama.cpp instances we are going run:

```shell
watch -n 0.1 nvidia-smi
```

Run the gppm daemon:

```
python3 gppmd/gppmd.py --config ./gppmd/config.yaml --llamacpp_configs_dir ./gppmd/llamacpp_configs
```

Wait for the instances to show up in the nvidia-smi command teminal.
gppm ships with a command line client (see details below). In another terminal run the cli like this to list the instances you just started:

```shell
python3 gppmc/gppmc.py get instances
```


## Installation

### Build binaries and DEB package

```shell
./tools/build_gppmd_deb.sh
./tools/build_gppmc_deb.sh
```

You should now find binaries for the daemon and the cli in the build folder:

```shell
ls -1 build/gppmd-$(git describe --tags --abbrev=0)-amd64/usr/bin/gppmd
ls -1 build/gppmc-$(git describe --tags --abbrev=0)-amd64/usr/bin/gppmc
```

Copy them wherever you want or install the DEB packages (described in the next step):

```shell
ls -1 build/*.deb
```

### Install DEB package

The DEB packages are tested for teh following dsitributions:

* Ubuntu 22.04

Install the DEB packages like this:

```sh
sudo dpkg -i build/gppmd-$(git describe --tags --abbrev=0)-amd64.deb
sudo dpkg -i build/gppmc-$(git describe --tags --abbrev=0)-amd64.deb
```

gppmd awaits it's config file at /etc/gppmd/config.yaml so put your config there. It can be minimal as this:

```
host: '0.0.0.0'
port: 5001
```

gppmd looks for llama.cpp config files in /etc/gppmd/llamacpp_configs so put your configs there. See below for detailed explaination of how the configuration works.

## Command line interface

gppm comes with a cli client:
```sh
$ gppmc
Usage: gppmc [OPTIONS] COMMAND [ARGS]...

  Group of commands for managing LlamaCpp instances and configurations.

Options:
  --help  Show this message and exit.

Commands:
  get     Get various resources.
  reload  Reload LlamaCpp configurations.
```

## Configuration

*Coming soon*
