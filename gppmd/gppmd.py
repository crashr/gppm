import argparse
import yaml
import logging
import time
import threading
import json
import os
from nvidia_pstate import set_pstate_low, set_pstate_high, set_pstate
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
import subprocess
import tempfile
import re
import shlex
from werkzeug.serving import make_server
import select
import signal
import sys


global llamacpp_configs_dir
global configs
global threads
configs = []
threads = []
subprocesses = {}

app = Flask(__name__, template_folder=os.path.abspath("/etc/gppmd/templates"))
app.config["DEBUG"] = True

parser = argparse.ArgumentParser(description="gppm power process manager")
parser.add_argument(
    "--config",
    type=str,
    default="/etc/gppmd/config.yaml",
    help="Path to the configuration file",
)
parser.add_argument(
    "--llamacpp_configs_dir",
    type=str,
    default="/etc/gppmd/llamacpp_configs",
    help="Path to the llama.cpp configuration file",
)
parser.add_argument(
    "--port",
    type=int,
    default=5002,
    help="Port number for the API to listen on",
)
args = parser.parse_args()

with open(args.config, "r") as file:
    config = yaml.safe_load(file)

# for key, value in config.items():
#    parser.add_argument(f"--{key}", type=type(value), default=value, help=f"Set {key}")
for key, value in config.items():
    if key != "port":  # Exclude "--port" from the loop
        parser.add_argument(
            f"--{key}", type=type(value), default=value, help=f"Set {key}"
        )

args = parser.parse_args()

for key, value in vars(args).items():
    config[key] = value

# logging.basicConfig(
#    filename=config.get("log_file", "/var/log/gppmd/gppmd.log"), level=logging.INFO
# )

result = subprocess.run(
    ["nvidia-smi", "-L"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
num_gpus = len(result.stdout.decode("utf-8").strip().split("\n"))

gpu_semaphores = {}
for gpu in range(num_gpus):
    set_pstate([gpu], int(os.getenv("NVIDIA_PSTATE_LOW", "8")), silent=True)
    gpu_semaphores[gpu] = threading.Semaphore(config.get("max_llamacpp_instances", 10))


def run_post_launch_hooks(config, subprocesses):
    if "post_launch_hooks" in config:
        for post_launch_hook in config["post_launch_hooks"]:
            if post_launch_hook["enabled"]:
                with open("/dev/null", "w") as devnull:
                    new_subprocess = subprocess.Popen(
                        shlex.split(post_launch_hook["command"]),
                        shell=False,
                        stdout=devnull,
                        stderr=devnull,
                    )
                subprocesses.append(new_subprocess)
                run_post_launch_hooks(post_launch_hook, subprocesses)


def list_thread_names():
    thread_names = "\n".join([thread._args[0]["name"] for thread in threads])
    return thread_names


def process_line(data, config):  # Need config for hooks

    gpus = [int(x) for x in data["gppm"]["gppm_cvd"].split(",")]

    pid = data["gppm"][
        "llamacpp_pid"
    ]  # TODO This needs to be changed to work with ollama

    tid = data["tid"]

    if "processing task" in data["msg"]:
        # logging.info(f"Task {tid} started")
        for gpu in gpus:
            gpu_semaphores[gpu].acquire(blocking=True)
            # logging.info(f"Aquired semaphore for GPU {gpu}")
        for gpu in gpus:
            # logging.info(f"Setting GPU {gpu} into high performance mode")
            set_pstate([gpu], int(os.getenv("NVIDIA_PSTATE_HIGH", "16")), silent=True)
    elif "stop processing: " in data["msg"]:
        # logging.info(f"Task {tid} terminated")
        for gpu in gpus:
            gpu_semaphores[gpu].release()
            # logging.info(f"Released semaphore for GPU {gpu}")
            if gpu_semaphores[gpu]._value is config.get("max_llamacpp_instances", 10):
                # logging.info(f"Setting GPU {gpu} into low performance mode")
                set_pstate([gpu], int(os.getenv("NVIDIA_PSTATE_LOW", "8")), silent=True)

    # for gpu, semaphore in gpu_semaphores.items():
    #    logging.info(f"Semaphore value for GPU {gpu}: {semaphore._value}")


def launch_llamacpp(llamacpp_config, stop_event):
    """
    tmp_dir = tempfile.TemporaryDirectory(dir="/tmp")
    os.makedirs(tmp_dir.name, exist_ok=True)
    pipe = os.path.join(tmp_dir.name, "pipe")
    os.mkfifo(pipe)
    """

    env = os.environ.copy()
    # env["CUDA_VISIBLE_DEVICES"] = llamacpp_config[
    #    "cuda_visible_devices"
    # ]  # TODO remove this
    if "env" in llamacpp_config:
        for key, value in llamacpp_config["env"].items():
            # print(f"ENV: {key}:{value}")
            env[key] = value

    llamacpp_cmd = shlex.split(llamacpp_config["command"])

    llamacpp_process = subprocess.Popen(
        llamacpp_cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        bufsize=1,
        universal_newlines=True,
    )

    if llamacpp_process.pid not in subprocesses:
        subprocesses[llamacpp_process.pid] = []

    run_post_launch_hooks(llamacpp_config, subprocesses[llamacpp_process.pid])

    pattern = re.compile(r"slot .* \| .* \| .+")

    while not stop_event.is_set():
        # Wait for data to be available for reading
        ready_to_read, _, _ = select.select([llamacpp_process.stderr], [], [], 0.1)
        if ready_to_read:
            # New data available, read it
            line = llamacpp_process.stderr.readline()
            # if line:
            #    print(f"DEBUG line: {line}", end="")
            #    pass
            if pattern.search(line):
                # FIXME
                line = line.strip()
                parts = line.split(" | ")
                id_slot = 0  # TODO
                id_task = 0  # TODO

                data = {
                    "tid": "",
                    "timestamp": "",
                    "msg": parts[2],
                    "id_slot": id_slot,
                    "id_task": id_task,
                    "gppm": {
                        "llamacpp_pid": llamacpp_process.pid,
                        "gppm_cvd": env["CUDA_VISIBLE_DEVICES"],
                    },
                }

                process_line(data, llamacpp_config)
        else:
            # No new data available, check if the subprocess has terminated
            if llamacpp_process.poll() is not None:
                break

    # Check if subprocesses are still running
    for llamacpp_subprocess in subprocesses[llamacpp_process.pid]:
        if llamacpp_subprocess.poll() is None:
            llamacpp_subprocess.terminate()
            while llamacpp_subprocess.poll() is None:
                pass

    llamacpp_process.terminate()
    llamacpp_process.wait()


# WIP with very low prio
def launch_ollama(ollama_config, stop_event):
    tmp_dir = tempfile.TemporaryDirectory(dir="/tmp")
    os.makedirs(tmp_dir.name, exist_ok=True)
    pipe = os.path.join(tmp_dir.name, "pipe")
    os.mkfifo(pipe)

    ollama_options = []

    for option in ollama_config["options"]:
        if isinstance(option, dict):
            pass
        else:
            ollama_options.append(str(option))

    ollama_cmd = shlex.split(ollama_config["command"] + " " + " ".join(ollama_options))

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = ollama_config["cuda_visible_devices"]
    env["OLLAMA_HOST"] = ollama_config["ollama_host"]
    env["OLLAMA_DEBUG"] = "1"

    # for env_var in ollama_config["env_vars"]:
    #    for k, v in env_var.items():
    #        env[k] = v

    ollama_process = subprocess.Popen(
        ollama_cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        bufsize=1,
        universal_newlines=True,
    )

    data = {"model": ollama_config["model"], "keep_alive": -1}
    response = requests.post(
        f"http://" + ollama_config["ollama_host"] + "/api/generate", data
    )

    pattern = re.compile(r"slot is processing task|slot released")

    while not stop_event.is_set():
        # Wait for data to be available for reading
        ready_to_read, _, _ = select.select([ollama_process.stdout], [], [], 0.1)
        if ready_to_read:
            # New data available, read it
            line = ollama_process.stdout.readline()
            # print(line) # FIXME
            if pattern.search(line):
                try:
                    data = json.loads(line)
                    data["gppm"] = {
                        "ollama_pid": ollama_process.pid,
                        "gppm_cvd": env["CUDA_VISIBLE_DEVICES"],
                    }
                except:
                    data = {}
                    data["gppm"] = {  # FIXME
                        "llamacpp_pid": ollama_process.pid,
                        "ollama_pid": ollama_process.pid,
                        "gppm_cvd": env["CUDA_VISIBLE_DEVICES"],
                    }
                    data["tid"] = 0
                    data["msg"] = line
                process_line(data)
        else:
            # No new data available, check if the subprocess has terminated
            if ollama_process.poll() is not None:
                break

    ollama_process.terminate()
    ollama_process.wait()


llamacpp_configs_dir = config.get("llamacpp_configs_dir", "/etc/gppmd/llamacpp_configs")


def load_llamacpp_configs(llamacpp_configs_dir=llamacpp_configs_dir):
    new_configs = []
    for filename in os.listdir(llamacpp_configs_dir):
        if filename.endswith(".yaml"):
            with open(os.path.join(llamacpp_configs_dir, filename), "r") as f:
                configs = yaml.safe_load(f)
                for config in configs:
                    new_configs.append(config)
    return new_configs


def purge_thread(thread):
    thread._args[1].set()  # Signal to stop
    thread.join()  # Wait for the thread to finish
    threads.remove(thread)  # Remove the thread from the list


def sync_threads_with_configs(threads, configs, launch_llamacpp):
    existing_config_names = [thread._args[0]["name"] for thread in threads]

    # new_config_names = [config['name'] for config in configs]
    new_config_names = []
    for config in configs:
        new_config_names.append(config["name"])

    # Remove threads that are not in the configs
    for thread in threads[:]:
        if thread._args[0]["name"] not in new_config_names:
            purge_thread(thread)
            # threads.remove(thread)

    # Add or update threads based on the configs
    for config in configs:
        if config["name"] in existing_config_names:  # FIXME is that needed?
            # Update existing thread
            for thread in threads:
                if thread._args[0]["name"] == config["name"]:
                    if (
                        thread._args[0] != config or config["enabled"] == False
                    ):  # FIXME does order of options in config file matter?
                        # print("Thread config has changed. Purging thread.")
                        purge_thread(thread)
                        # print("DEBUG: Purged.")
                        if config["enabled"] == True:
                            stop_event = threading.Event()
                            new_thread = threading.Thread(
                                target=launch_llamacpp, args=(config, stop_event)
                            )
                            new_thread.start()
                            threads.append(new_thread)
        else:
            if config["enabled"] == True:
                # Add new thread
                stop_event = threading.Event()  # FIXME
                new_thread = threading.Thread()  # FIXME

                if config.get("type", "llamacpp") == "llamacpp":
                    new_thread = threading.Thread(
                        target=launch_llamacpp, args=(config, stop_event)
                    )
                elif config.get("type") == "ollama":
                    new_thread = threading.Thread(
                        target=launch_ollama, args=(config, stop_event)
                    )
                else:
                    # Handle unknown type or default to llamacpp
                    new_thread = threading.Thread(
                        target=launch_llamacpp, args=(config, stop_event)
                    )

                new_thread.start()
                threads.append(new_thread)

    return threads


@app.route("/apply_llamacpp_configs", methods=["POST"])
def api_apply_llamacpp_configs():
    global configs
    global threads
    configs = load_llamacpp_configs()
    configs_to_apply = request.json
    for config in configs_to_apply:
        configs.append(config)
    threads = sync_threads_with_configs(threads, configs, launch_llamacpp)
    return {"status": "OK"}


@app.route("/reload_llamacpp_configs", methods=["GET"])
def api_reload_llamacpp_configs():
    global configs
    global threads
    configs = load_llamacpp_configs()
    threads = sync_threads_with_configs(threads, configs, launch_llamacpp)
    return {"status": "OK"}


@app.route("/get_llamacpp_instances", methods=["GET"])
def api_get_llamacpp_instances():
    instances = {"llamacpp_instances": []}
    for thread in threads:
        thread_name = thread._args[0]["name"]
        instances["llamacpp_instances"].append(thread_name)
    return jsonify(instances)


@app.route("/get_llamacpp_subprocesses", methods=["GET"])
def api_get_llamacpp_subprocesses():
    serialized_subprocesses = {
        pid: [
            {"pid": p.pid, "args": p.args, "returncode": p.returncode}
            for p in processes
        ]
        for pid, processes in subprocesses.items()
    }
    print(serialized_subprocesses)
    return jsonify(serialized_subprocesses)


@app.route("/get_llamacpp_configs", methods=["GET"])
def api_get_llamacpp_configs():
    return jsonify(configs)


@app.route("/gui", methods=["GET"])
def gui():
    return render_template("home.html")


@app.route("/get_instances", methods=["GET"])
def api_get_instances():
    instances = {"instances": []}
    for thread in threads:
        thread_data = {
            "name": thread._args[0]["name"],
            "pid": thread._args[0]["pid"],
            "cvd": thread._args[0]["cuda_visible_devices"],
            # add more data if needed
        }
        instances["instances"].append(thread_data)
    return jsonify(instances)


@app.route("/enable_llamacpp_instance", methods=["POST"])
def api_enable_llamacpp_instance():
    global configs
    global threads
    name = request.json.get("name")

    for config in configs:
        print(config)
        if config["name"] == name:
            config["enabled"] = True
            threads = sync_threads_with_configs(threads, configs, launch_llamacpp)
            return {"status": "OK", "message": f"Instance {name} enabled"}
    return {"status": "ERROR", "message": f"Instance {name} not found"}


@app.route("/disable_llamacpp_instance", methods=["POST"])
def api_disable_llamacpp_instance():
    global configs
    global threads
    name = request.json.get("name")

    for config in configs:
        print(config)
        if config["name"] == name:
            config["enabled"] = False
            threads = sync_threads_with_configs(threads, configs, launch_llamacpp)
            return {"status": "OK", "message": f"Instance {name} disabled"}
    return {"status": "ERROR", "message": f"Instance {name} not found"}


server = make_server("0.0.0.0", args.port, app)
server_thread = threading.Thread(target=server.serve_forever)
server_thread.start()


if __name__ == "__main__":

    logging.info(f"Reading llama.cpp configs")

    configs = load_llamacpp_configs()
    threads = sync_threads_with_configs(threads, configs, launch_llamacpp)

    logging.info(f"All llama.cpp instances launched")

    for thread in threads:
        thread.join()
