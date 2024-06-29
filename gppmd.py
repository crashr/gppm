import argparse
import yaml
import logging
#import time
#from threading import Thread
import threading
import json
import os
from nvidia_pstate import set_pstate_low, set_pstate_high, set_pstate
from flask import Flask
import subprocess
import tempfile
import re
import shlex

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

def launch_llamacpp(llamacpp_config):
    tmp_dir = tempfile.TemporaryDirectory(dir='/tmp')
    os.makedirs(tmp_dir.name, exist_ok=True)
    pipe = os.path.join(tmp_dir.name, "pipe")
    os.mkfifo(pipe)
    logging.info(f"Created {pipe}")

    llamacpp_options = []
    for option in llamacpp_config["options"]:
        if isinstance(option, dict):
            logging.info("DEBUG: {option}")
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

    while True:
        line = llamacpp_process.stdout.readline()            
        if pattern.search(line):
            data = json.loads(line)
            data['gppm'] = {'llamacpp_pid': llamacpp_process.pid, 'gppm_cvd': env["CUDA_VISIBLE_DEVICES"]} # TODO
            process_line(data)

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def test_endpoint():
    logging.info("API test endpoint hit")
    return "Test endpoint hit"

if __name__ == '__main__':

    logging.info(f"Reading llama.cpp configs")

    threads = []

    llamacpp_configs_dir = config.get('llamacpp_configs_dir', '/etc/gppmd/llamacpp_configs')

    for filename in os.listdir(llamacpp_configs_dir):
        if filename.endswith('.yaml'):
            with open(os.path.join(llamacpp_configs_dir, filename), 'r') as f:
                configs = yaml.safe_load(f)

            for config in configs:
                thread = threading.Thread(target=launch_llamacpp, args=(config,))
                thread.start()
                threads.append(thread)

    logging.info(f"All llama.cpp instances launched")

    # TODO if activated in config
    app.run(host='0.0.0.0', port=5000)

    for thread in threads:
        thread.join()
