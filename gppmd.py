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
import subprocess
import tempfile
import re
import shlex
from werkzeug.serving import make_server
import select


app = Flask(__name__)
#app.config['DEBUG'] = True

parser = argparse.ArgumentParser(description='GPU Power and Performance Manager')
parser.add_argument('--config', type=str, default='/etc/gppmd/config.yaml', help='Path to the configuration file')
parser.add_argument('--llamacpp_configs_dir', type=str, default='/etc/gppmd/llamacpp_configs', help='Path to the llama.cpp configuration file')
args = parser.parse_args()

with open(args.config, 'r') as file:
    config = yaml.safe_load(file)

for key, value in config.items():
    parser.add_argument(f'--{key}', type=type(value), default=value, help=f'Set {key}')

args = parser.parse_args()

for key, value in vars(args).items():
    config[key] = value

logging.basicConfig(filename=config.get('log_file', '/var/log/gppmd/gppmd.log'), level=logging.INFO)

result = subprocess.run(['nvidia-smi', '-L'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
num_gpus = len(result.stdout.decode('utf-8').strip().split('\n'))

gpu_semaphores = {}
for gpu in range(num_gpus):
    gpu_semaphores[gpu] = threading.Semaphore(config.get('max_llamacpp_instances', 10))

def process_line(data):
    #print(data)
    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    gpus = [int(x) for x in data["gppm"]["gppm_cvd"].split(',')]
    pid = data["gppm"]["llamacpp_pid"]
    tid = data["tid"]
    logging.info(f"Process {pid} using GPUs {gpus}")
    if "slot is processing task" in data["msg"]:
        logging.info(f"Task {tid} started")
        for gpu in gpus:
            gpu_semaphores[gpu].acquire(blocking=True)
            logging.info(f"Aquired semaphore for GPU {gpu}")
        for gpu in gpus:
            logging.info(f"Setting GPU {gpu} into high performance mode")
            set_pstate([gpu], int(os.getenv("NVIDIA_PSTATE_HIGH", "16")), silent=True)
    elif "slot released" in data["msg"]:
        logging.info(f"Task {tid} terminated")
        for gpu in gpus:
            gpu_semaphores[gpu].release()
            logging.info(f"Released semaphore for GPU {gpu}")
            if gpu_semaphores[gpu]._value is config.get('max_llamacpp_instances', 10):
                logging.info(f"Setting GPU {gpu} into low performance mode")
                set_pstate([gpu], int(os.getenv("NVIDIA_PSTATE_LOW", "8")), silent=True)
    for gpu, semaphore in gpu_semaphores.items():
        logging.info(f"Semaphore value for GPU {gpu}: {semaphore._value}")
    logging.info(f"<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    logging.info(f"")

def list_thread_names():
    thread_names = "\n".join([thread._args[0]['name'] for thread in threads])
    return thread_names

def launch_llamacpp(llamacpp_config, stop_event):
    tmp_dir = tempfile.TemporaryDirectory(dir='/tmp')
    os.makedirs(tmp_dir.name, exist_ok=True)
    pipe = os.path.join(tmp_dir.name, "pipe")
    os.mkfifo(pipe)

    llamacpp_options = []
    for option in llamacpp_config["options"]:
        if isinstance(option, dict):
            pass
        else:
            llamacpp_options.append(str(option))

    llamacpp_cmd = shlex.split(llamacpp_config["command"] + ' ' + ' '.join(llamacpp_options))

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = llamacpp_config["cuda_visible_devices"]    

    llamacpp_process = subprocess.Popen(
        llamacpp_cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        bufsize=1,
        universal_newlines=True
    )

    pattern = re.compile(r'slot is processing task|slot released')

    while not stop_event.is_set():
        # Wait for data to be available for reading
        ready_to_read, _, _ = select.select([llamacpp_process.stdout], [], [], 0.1)
        if ready_to_read:
            # New data available, read it
            line = llamacpp_process.stdout.readline()
            if pattern.search(line):
                data = json.loads(line)
                data['gppm'] = {'llamacpp_pid': llamacpp_process.pid, 'gppm_cvd': env["CUDA_VISIBLE_DEVICES"]}
                process_line(data)
        else:
            # No new data available, check if the subprocess has terminated
            if llamacpp_process.poll() is not None:
                break

    llamacpp_process.terminate()
    llamacpp_process.wait()

global llamacpp_configs_dir
llamacpp_configs_dir = config.get('llamacpp_configs_dir', '/etc/gppmd/llamacpp_configs')

#global configs
configs = {}
threads = []

def load_llamacpp_configs(llamacpp_configs_dir=llamacpp_configs_dir,configs=configs):
    for filename in os.listdir(llamacpp_configs_dir):
        if filename.endswith('.yaml'):
            with open(os.path.join(llamacpp_configs_dir, filename), 'r') as f:
                configs = yaml.safe_load(f)
                return configs

configs = load_llamacpp_configs()

def purge_thread(thread):
    thread._args[1].set()   # Signal to stop
    thread.join()           # Wait for the thread to finish
    threads.remove(thread)  # Remove the thread from the list

def reload_llamacpp_configs(llamacpp_configs_dir=llamacpp_configs_dir):
    global threads
    global configs

    #print(f"Current threads:")
    #for thread in threads:
    #    print(f" {thread._args[0]['name']} {thread}")

    new_threads = []
    new_configs = load_llamacpp_configs(llamacpp_configs_dir)
    
    for config in new_configs:
        #print(f"Found config {config['name']}")

        no_match_found=True
        create_new_thread=True

        for thread in threads:

            #print(f" Comparing existing thread {thread._args[0]['name']} with {config['name']}")

            if thread._args[0]['name'] == config['name']:
                #print("  Names match. Does config differ? ", end='')
                if thread._args[0] != config:
                    #print("   Yes.")
                    purge_thread(thread)
                    #print("   Thread removed. Creating new one.")                    
                    stop_event = threading.Event()
                    thread = threading.Thread(target=launch_llamacpp, args=(config, stop_event))
                    thread.start()
                    new_threads.append(thread)                    
                    #print("   New thread up and running")
                #else:
                #    print("   No.")
                #    #break
                create_new_thread=False

            #else:
            #    print(" Thread with that name not found yet.")

        if create_new_thread==True:
            # Thread doesn't exist, create a new one
            stop_event = threading.Event()
            thread = threading.Thread(target=launch_llamacpp, args=(config, stop_event))
            thread.start()
            new_threads.append(thread)
            #print(" Created and appended new thread")

        #print(f"Config {config['name']} processed")

    for thread in new_threads:
        threads.append(thread)

    # Search threads left that are not in new config and remove them
    for thread in threads:
        if thread._args[0]['name'] not in [config['name'] for config in new_configs]:
            #print(f"{thread._args[0]['name']} is going to be removed")
            purge_thread(thread)

    configs = new_configs

    #for thread in threads:
    #    print(f"{thread._args[0]['name']} {thread}")

    return new_configs, threads


@app.route('/reload_llamacpp_configs', methods=['GET'])
def api_reload_llamacpp_configs():
    #global configs
    #global threads
    #configs, threads = reload_llamacpp_configs(llamacpp_configs_dir)
    reload_llamacpp_configs(llamacpp_configs_dir)
    return {"status":"OK"}

@app.route('/get_llamacpp_instances', methods=['GET'])
def api_get_llamacpp_instances():
    instances = {"llamacpp_instances": []}
    for thread in threads:
        thread_name = thread._args[0]['name']
        instances["llamacpp_instances"].append(thread_name)
    return jsonify(instances)

@app.route('/get_llamacpp_configs', methods=['GET'])
def api_get_llamacpp_configs():
    return jsonify(configs)

@app.route('/gui', methods=['GET'])
def gui():
    return render_template('home.html')

server = make_server('0.0.0.0', 5001, app)
server_thread = threading.Thread(target=server.serve_forever)
server_thread.start()


if __name__ == '__main__':

    logging.info(f"Reading llama.cpp configs")
    configs = load_llamacpp_configs()
    #print(configs)

    for config in configs:
        stop_event = threading.Event()
        thread = threading.Thread(target=launch_llamacpp, args=(config, stop_event))
        thread.start()
        threads.append(thread)

    logging.info(f"All llama.cpp instances launched")

    for thread in threads:
        thread.join()
