import argparse
import yaml
import logging
import time
from threading import Thread
import threading
import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import Flask, request, jsonify
from nvidia_pstate import set_pstate_low, set_pstate_high, set_pstate
import fileinput


# Parse command-line arguments
parser = argparse.ArgumentParser(description='GPU Power and Performance Manager')
parser.add_argument('--config', type=str, default='/etc/gppmd/config.yaml', help='Path to the configuration file')
args = parser.parse_args()

# Load configuration from YAML file
with open(args.config, 'r') as file:
    config = yaml.safe_load(file)

# Set up logging
logging.basicConfig(filename=config.get('log_file', '/var/log/gppmd/gppmd.log'), level=logging.INFO)

app = Flask(__name__)
sleep_time = config.get('sleep_time', 0.1)
timeout_time = config.get('timeout_time', 0.0)

gpu_semaphores = {}
for gpu in range(4):                                                    # TODO
    gpu_semaphores[gpu] = threading.Semaphore(config.get('max_llamacpp_instances', 10))

class Handler(FileSystemEventHandler):

    def __init__(self, filename):
        self.filename = filename

    def on_modified(self, event):
        if event.src_path == self.filename:
            with open(self.filename, 'rb') as f:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
                line = f.readline().decode()
                #logging.info(f"Last line added: {last_line.strip()}")
                if not line or (not "slot is processing task" in line and not "slot released" in line):
                    logging.info(f"Last line added: {line.strip()}")
                    return
                logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                data = json.loads(line)                                             # Parse the JSON line
                gpus = [int(x) for x in data["gppm"]["gppm_cvd"].split(',')]        # Get the GPU indices
                pid = data["gppm"]["llamacpp_pid"]
                tid = data["tid"]
                logging.info(f"Process {pid} using GPUs {gpus}")
                if "slot is processing task" in data["msg"]:
                    logging.info(f"Task {tid} started")
                    for gpu in gpus:
                        gpu_semaphores[gpu].acquire(blocking=False)
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
                            set_pstate([gpu], int(os.getenv("NVIDIA_PSTATE_LOW", "8")), silent=True)
                for gpu, semaphore in gpu_semaphores.items():
                    logging.info(f"Semaphore value for GPU {gpu}: {semaphore._value}")
                logging.info(f"<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                logging.info(f"")

@app.route('/set_sleep_time', methods=['POST'])
def set_sleep() -> tuple:
    global sleep_time
    logging.debug(f"Setting sleep_time to {sleep_time}")
    print(f"Setting sleep_time to {sleep_time}")
    data = request.get_json()
    if 'sleep_time' in data:
        sleep_time = float(data['sleep_time'])
        return jsonify({'sleep_time': sleep_time}), 200
    else:
        return jsonify({'error': 'Missing sleep_time parameter'}), 400

@app.route('/set_timeout_time', methods=['POST'])
def set_timeout() -> tuple:
    global timeout_time
    logging.info(f"Setting timeout_time to {timeout_time}")
    data = request.get_json()
    if 'timeout_time' in data:
        timeout_time = float(data['timeout_time'])
        return jsonify({'timeout_time': timeout_time}), 200
    else:
        return jsonify({'error': 'Missing timeout_time parameter'}), 400

if __name__ == '__main__':
    #log_thread = Thread(target=process_log, args=(config.get('log_file_to_monitor', '/var/log/llama.cpp/llama-server.log'),))
    #log_thread.start()
    #app.run(host=config.get('host', '0.0.0.0'), port=config.get('port', 5000))

    event_handler = Handler(filename=config.get('log_file_to_monitor', '/var/log/llama.cpp/llama-server.log'))
    observer = Observer()
    observer.schedule(event_handler, path=config.get('log_file_to_monitor', '/var/log/llama.cpp/llama-server.log'), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
