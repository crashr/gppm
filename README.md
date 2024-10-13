# gppm
![gppm-banner](https://github.com/user-attachments/assets/af0a6d7b-818c-476f-b3e3-9217b848c5c7)


gppm power process manager

gppm is designed for use with llama.cpp and NVIDIA Tesla P40 GPUs. The standalone llama.cpp currently lacks functionality to reduce the power consumption of these GPUs in idle mode. Although there is a patch for llama.cpp, it switches the performance mode for all GPUs simultaneously, which can disrupt setups where multiple llama.cpp instances share one or more GPUs. Implementing a communication mechanism within llama.cpp to manage task distribution and GPU status is complex. gppm addresses this challenge externally, providing a more efficient solution.
gppm allows you to define llama.cpp instances as code, enabling automatic spawning, termination, and respawning.

> [!NOTE]
> Both the configuration and the API will most likely continue to change for a while. When changing to a newer version, please always take a look at the current documentation.
  
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

The DEB packages are tested for the following dsitributions:

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

gppmd looks for llama.cpp config files in /etc/gppmd/llamacpp_configs so put your configs there (see below for detailed explaination on how the configuration works).

Enable and run the daemon:

```shell
sudo systemctl enable --now gppmd.service
```

## Command line interface

gppm comes with a cli client. It provides basic functionalities to interact with the daemon:

```sh
$ gppmc
Usage: gppmc [OPTIONS] COMMAND [ARGS]...

  Group of commands for managing llama.cpp instances and configurations.

Options:
  --host TEXT     The host to connect to.
  --port INTEGER  The port to connect to.
  --help          Show this message and exit.

Commands:
  apply    Apply LlamaCpp configurations from a YAML file.
  disable  Disable a LlamaCpp instance.
  enable   Enable a LlamaCpp instance.
  get      Get various resources.
  reload   Reload LlamaCpp configurations.
```

For some usage example take a look at the configuration section. 

## Configuration

After changing llama.cpp instance configuration files they can be reloded with the cli:

```shell
gppmc reload
```

This affects only instances which configs where changed. All other instances remain untouched.

The most basic configuration for a llama.cpp instance looks like this:

```yaml
- name: Biggie_SmolLM_0.15B_Base_q8_0_01
  enabled: True
  env:
    CUDA_VISIBLE_DEVICES: "0"
  command:
    "/usr/local/bin/llama-server \
      --host 0.0.0.0 \
      -ngl 100 \
      -m /models/Biggie_SmolLM_0.15B_Base_q8_0.gguf \
      --port 8061 \
      -sm none \
      --no-mmap \
      --log-format json" # Remove this for version >=1.2.0 
```

To enable gppmd to perform power state switching with NVIDIA Tesla P40 GPUs it is essential to specifiy CUDA_VISIBLE_DEVICES and json log format.

gppm allows to configure post launch hooks. With that it is possible to bundle complex setups. As an example the following configuration creates a setup consisting of two llama.cpp instances running Codestral on three GPUs behind a load balancer. For the load balancer [Paddler](https://github.com/distantmagic/paddler) is used:

```yaml
- name: "Codestral-22B-v0.1-Q8_0 (paddler balancer)"
  enabled: True
  command:
    "/usr/local/bin/paddler balancer \
      --management-host 0.0.0.0 \
      --management-port 8085 \
      --management-dashboard-enable=true \
      --reverseproxy-host 192.168.178.56 \
      --reverseproxy-port 8081"

- name: "Codestral-22B-v0.1-Q8_0 (llama.cpp 01)"
  enabled: True
  env:
    CUDA_VISIBLE_DEVICES: "0,1,2"
  command:
    "/usr/local/bin/llama-server \
      --host 0.0.0.0 \
      -ngl 100 \
      -m /models/Codestral-22B-v0.1-Q8_0.gguf \
      --port 8082 \
      -fa \
      -sm row \
      -mg 0 \
      --no-mmap \
      --slots \
      --log-format json" # Remove this for version >=1.2.0
  post_launch_hooks:
  - name: Codestral-22B-v0.1-Q8_0_(paddler_01)
    enabled: True
    command:
      "/usr/local/bin/paddler agent \
        --name 'Codestral-22B-v0.1-Q8_0 (llama.cpp 01)' \
        --external-llamacpp-host 192.168.178.56 \
        --external-llamacpp-port 8082 \
        --local-llamacpp-host 192.168.178.56 \
        --local-llamacpp-port 8082 \
        --management-host 192.168.178.56 \
        --management-port 8085"

- name: "Codestral-22B-v0.1-Q8_0_(llama.cpp_02)"
  enabled: True
  env:
    CUDA_VISIBLE_DEVICES: "0,1,2"
  command:
    "/usr/local/bin/llama-server \
      --host 0.0.0.0 \
      -ngl 100 \
      -m /models/Codestral-22B-v0.1-Q8_0.gguf \
      --port 8083 \
      -fa \
      -sm row \
      -mg 1 \
      --no-mmap \
      --log-format json" # Remove this for version >=1.2.0
  post_launch_hooks:
  - name: "Codestral-22B-v0.1-Q8_0_Paddler_02"
    enabled: True
    command:
      "/usr/local/bin/paddler agent \
        --name 'Codestral-22B-v0.1-Q8_0 (llama.cpp 02)' \
        --external-llamacpp-host 192.168.178.56 \
        --external-llamacpp-port 8083 \
        --local-llamacpp-host 192.168.178.56 \
        --local-llamacpp-port 8083 \
        --management-host 192.168.178.56 \
        --management-port 8085"
```

![image](https://github.com/user-attachments/assets/777e4c96-b960-449e-8647-6f28753d3d8b)


***More to come soon***
