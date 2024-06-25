import argparse
import yaml
import logging
import time
from threading import Thread
import threading

from flask import Flask, request, jsonify
from nvidia_pstate import set_pstate_low, set_pstate_high

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

def slot_processing_task(line):
    logging.debug(f"Slot is processing task: {line}")
    logging.info("Setting GPU to high performance")
    set_pstate_high()

def slot_released(line):
    logging.debug(f"Slot released: {line}")
    logging.info("Setting GPU to low performance")
    set_pstate_low()

def process_log(filename: str) -> None:
    task_semaphore = threading.Semaphore(config.get('max_llamacpp_instances', 10))
    try:
        with open(filename, 'r') as file:
            file.seek(0, 2)  # Go to the end of the file
            while True:
                line = file.readline()
                if not line:
                    time.sleep(sleep_time)  # If no new line is available, wait
                    continue
                if "slot is processing task" in line:
                    task_semaphore.acquire()
                    slot_processing_task(line)
                elif "slot released" in line: # or "all slots are idle": # FIXME
                    logging.info(f"timeout_time: {timeout_time}")
                    time.sleep(timeout_time)
                    logging.info(f"Timeout")
                    task_semaphore.release()
                    if task_semaphore._value == config.get('max_llamacpp_instances', 10):
                        slot_released(line)
    except FileNotFoundError:
        logging.error(f"File {filename} not found")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

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
    log_thread = Thread(target=process_log, args=(config.get('log_file_to_monitor', '/var/log/llama.cpp/llama-server.log'),))
    log_thread.start()
    app.run(host=config.get('host', '0.0.0.0'), port=config.get('port', 5000))
