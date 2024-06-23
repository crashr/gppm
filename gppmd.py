import argparse
import yaml
import logging
import time
from threading import Thread
import os
import pynvml

from flask import Flask, request, jsonify
from nvidia_pstate import set_pstate_low, set_pstate_high, set_pstate

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
    try:
        with open(filename, 'r') as file:
            file.seek(0, 2)  # Go to the end of the file
            while True:
                line = file.readline()
                if not line:
                    time.sleep(sleep_time)  # If no new line is available, wait
                    continue
                if "slot is processing task" in line:
                    slot_processing_task(line)
                elif "slot released" in line: # or "all slots are idle": # FIXME
                    logging.info(f"timeout_time: {timeout_time}")
                    time.sleep(timeout_time)
                    logging.info(f"Timeout")
                    slot_released(line)
    except FileNotFoundError:
        logging.error(f"File {filename} not found")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")


def monitor_gpu_power(device=0, threshold=5, low_mid_value=30, low_variance=10, high_mid_value=50, high_variance=10):
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(device)  # Iindex of the GPU to be monitored

    low_power_count = 0
    high_power_count = 0

    low_power_threshold_min = low_mid_value - low_variance
    low_power_threshold_max = low_mid_value + low_variance
    high_power_threshold_min = high_mid_value - high_variance
    high_power_threshold_max = high_mid_value + high_variance

    try:
        state = -1
        action = 0

        while True:
            current_time = int(time.time() * 1000)  # Get current time in milliseconds
            power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to Watts

            if low_power_threshold_min <= power_usage <= low_power_threshold_max:
                low_power_count += 1
                high_power_count = 0
                if low_power_count >= 1: #threshold:
                    set_pstate([device], int(os.getenv("NVIDIA_PSTATE_HIGH", "16")), silent=True)   # 16
                    action = 1
                    state = 1
                    low_power_count = 0
            elif high_power_threshold_min < power_usage <= high_power_threshold_max:
                high_power_count += 1
                low_power_count = 0
                if high_power_count >= 20: #threshold:
                    set_pstate([device], int(os.getenv("NVIDIA_PSTATE_LOW", "8")), silent=True)     # 8
                    action = -1
                    state = -1
                    high_power_count = 0
            else:
                action = 0
                low_power_count = 0
                high_power_count = 0

            # print device id, power usage with fixed width, and millisecond timestamp, and action
            #print(f"Timestamp: {current_time} ms, Device ID: {device}, Power Usage: {power_usage:.2f} W, Action: {action}")
            print(f"{current_time},{device},{power_usage:.2f},{action},{state}")

            #time.sleep(0.1)

    except KeyboardInterrupt:
        pynvml.nvmlShutdown()


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

    #monitor_thread = Thread(target=monitor_gpu_power, args=())
    #monitor_thread.start()

    # Create a thread for each GPU device
    pynvml.nvmlInit()
    threads = []
    #for i in range(pynvml.nvmlDeviceGetCount()):  # Get the number of GPU devices
    for i in range(1):  # Get the number of GPU devices
        #  8/0
        #thread = Thread(target=monitor_gpu_power, args=(i, 1, 27, 5, 45, 5))  # Pass the device index and threshold as arguments
        # 16/0
        thread = Thread(target=monitor_gpu_power, args=(i, 5, 27, 5, 55, 5))  # Pass the device index and threshold as arguments
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish (this will run indefinitely until a KeyboardInterrupt is raised)
    for thread in threads:
        thread.join()

    app.run(host=config.get('host', '0.0.0.0'), port=config.get('port', 5000))
