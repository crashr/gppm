# gppm
GPU Power and Performance Manager

gppm aims to be used with llama.cpp and older NVIDIA P40/P100 GPUs. Currently standalone llama.cpp doesn't provide functionality to reduce the power consumption of those GPUs in idle mode. This is where gppm jumps in. 

See a demo of gppm forcing idle power consumption of a Testla P40 to 10 Watt instead of 50 Watt with only llama.cpp [gppm demo](screencast01.mkv)
  
## Table of Contents

- [How it works](#how-it-works)
- [Installation](#installation)
- [Basic configuration](#basic-configuration)
- [Usage](#usage)

## How it works

gppm must be installed on the host where the GPUs are installed and llama.cpp is running. gppm monitors llama.cpp's output and accordingly changes the performance modes of installed P40/P100 GPUs. It can manage any number of GPUs. gppm switches each GPU to a low performance state as soon as none of the existing llama.cpp instances is running a task on that particular GPU and sets it into high performancemode as soon as the next task is going to be run. In doing so, gppm is able to control all GPUs independently of each other. gppm is designed as a wrapper and as such you have all llama.cpp instances configured at one place.

## Installation

To get started with gppm, follow these steps:

1. **Clone the repository**:
    ```sh
    git clone https://github.com/crashr/gppm.git
    cd gppm
    ```

2. **Set up a virtual environment**:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

## Basic configuration
1. **Copy configuration example**:
    ```sh
    cp gppmd_config.yaml.example gppmd_config.yaml
    ```
2. **Change log_file_to_monitor**:
   
    Set log_file_to_monitor to a path that gppm can read from and llama.cpp can write to.


## Usage

Run llama.cpp like this:
```sh
llama-server <OTHER OPTIONS> --log-format text >> /path/to/llama-server.log
```

When llama.cpp is up and running, use the following command to run gppm:

```sh
python3 gppmd.py --config gppmd_config.yaml
```
To see the effect, in another terminal run this:
```sh
watch -n0.1 nvidia-smi
```
and run inference.
