# gppm
GPU Power and Performance Manager

gppm is designed for use with llama.cpp and NVIDIA Tesla P40 GPUs. The standalone llama.cpp currently lacks functionality to reduce the power consumption of these GPUs in idle mode. Although there is a patch for llama.cpp, it switches the performance mode for all GPUs simultaneously, which can disrupt setups where multiple llama.cpp instances share one or more GPUs. Implementing a communication mechanism within llama.cpp to manage task distribution and GPU status is complex. gppm addresses this challenge externally, providing a more efficient solution.

Check out a demo of gppm reducing the idle power consumption of a Tesla P40 from 50 Watts to 10 Watts with llama.cpp [here](screencast01.mkv).

Additionally, gppm allows you to define llama.cpp instances as code, enabling automatic spawning, termination, and respawning. Watch a demo of this feature [here](screencast02.mkv).

  
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

2. Run scripts to built DEB packages:
    ```sh
    ./tools/build_gppmd_deb.sh
    ./tools/build_gppmc_deb.sh
    ```

3. Install packages:
    ```sh
    sudo dpkg -i ./build/gppm*.deb
    sudo systemctl daemon-reload
    ```
    
## Quickstart

1. Stop any running llama.cpp instances, you will launch them now with gppm

2. Create the file /etc/gppmd/llamacpp_configs/configs.yaml
   Example (modify to your needs): 
   ```
   - name: "codestral"
     enabled: True
     command: "/usr/local/bin/llama-server"
     cuda_visible_devices: "0,1"
     options:
     - --host 0.0.0.0
     - -ngl 100
     - -m /models/Codestral-22B-v0.1-Q8_0.gguf
     - --port 8081
     - -fa
     - -sm row
     - -mg 0
     - --no-mmap
     - --log-format json

    - name: "Phi-3.1-mini-4k-instruct-Q5_K_M"
    enabled: True
    command: "/usr/local/bin/llama-server"
    cuda_visible_devices: "0,1"
    options:
    - --host 0.0.0.0
    - -ngl 100
    - -m /models/Phi-3.1-mini-4k-instruct-Q5_K_M.gguf
    - --port 8082
    - -fa
    - -sm row
    - -mg 0
    - --no-mmap
    - --log-format json
    - -c 2048

    - name: "ollama_01"
      enabled: True
      type: ollama
      command: "/usr/local/bin/ollama serve"
      cuda_visible_devices: "3"
      options: []
  ```
    
3. Launch all configured llama.cpp instances by running gppmd
    ```sh
  sudo systemctl start gppmd
    ```

4. Observe GPU utilization in another terminal
    ```sh
    watch -n 0.1 nvidia-smi
    ```

5. Wait for the API or web interface to be up and running and run inference.


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
