# gppm
GPU Power and Performance Manager

gppm aims to be used with llama.cpp and NVIDIA Tesla P40 GPUs. Currently standalone llama.cpp doesn't provide functionality to reduce the power consumption of those GPUs in idle mode.
There is a patch available for llama.cpp but because it is based on switching the performance mode for all GPUs simultaneously it is very likely to break setups in which multiple llama.cpp instances share one or more GPUs. To fix this a complex mechanism would have to be implemented in llama.cpp, via which all llama.cpp instances can communicate with each other to synchronize a distributed structure in which the status of the tasks and their distribution to the GPUs is managed. This is much easier achieved from outside of llama.cpp. This is where gppm jumps in.

See a demo of gppm forcing idle power consumption of a Testla P40 to 10 Watt instead of 50 Watt with only llama.cpp [demo](screencast01.mkv)

Beside that gppm provides a way to define llama.cpp instances as code and let them spawn/terminate/respawn automatically. See a demo of how to use this feature here [demo](screencast02.mkv)

  
## Table of Contents

- [How it works](#how-it-works)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Command line interface](#command-line-interface)

## How it works

gppm must be installed on the host where the GPUs are installed and llama.cpp is running. gppm monitors llama.cpp's output to recognize tasks and on which GPU lama.cpp runs them on and with this information accordingly changes the performance modes of installed P40 GPUs. It can manage any number of GPUs and llama.cpp instances. gppm switches each GPU to a low performance state as soon as none of the existing llama.cpp instances is running a task on that particular GPU and sets it into high performancemode as soon as the next task is going to be run. In doing so, gppm is able to control all GPUs independently of each other. gppm is designed as a wrapper and as such you have all llama.cpp instances configured at one place.

## Installation

To get started with gppm, follow these steps:

1. Clone the repository:
    ```sh
    git clone https://github.com/crashr/gppm.git
    cd gppm
    ```

2. Set up a virtual environment:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```
    
## Quickstart

1. Stop any running llama.cpp instances, you will launch them now with gppm

2. Rename one or both llama.cpp example configuration files to .yaml and edit to your needs
    ```
    cp llamacpp_configs/codestral.yaml.example llamacpp_configs/codestral.yaml
    cp llamacpp_configs/2x_replete-coder.yaml.example llamacpp_configs/2x_replete-coder.yaml
    
4. Launch all configured llama.cpp instances by running gppmd
    ```sh
    python3 gppmd.py --llamacpp_configs_dir ./llamacpp_configs
    ```

5. Observe GPU utilization in another terminal
    ```sh
    watch -n 0.1 nvidia-smi
    ```

6. Wait for the API or web interface to be up and running and run inference.


## Command line interface

gppm comes with a cli client.
```bash
python3 gppm.py 
Usage: gppm.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  get-llamacpp-configs
  get-llamacpp-instances
  reload-llamacpp-configs
```

## Configuration

*Coming soon*
