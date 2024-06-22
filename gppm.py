import requests
import json
import yaml
import argparse
import os

def load_config(path: str) -> dict:
    try:
        with open(path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"Configuration file not found at {path}. Using default settings.")
        return {}

def set_sleep_time(sleep_time: float, url: str) -> None:
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({'sleep_time': sleep_time})

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        print(f"Successfully set sleep time to {sleep_time}")
    else:
        print(f"Failed to set sleep time. Server responded with: {response.json()}")

def set_timeout_time(timeout_time: float, url: str) -> None:
   headers = {'Content-Type': 'application/json'}
   data = json.dumps({'timeout_time': timeout_time})

   response = requests.post(url, headers=headers, data=data)

   if response.status_code == 200:
       print(f"Successfully set timeout time to {timeout_time}")
   else:
       print(f"Failed to set timeout time. Server responded with: {response.json()}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GPU Performance Manager Client')
    parser.add_argument('--sleep', type=float, help='The sleep time to set')
    parser.add_argument('--timeout', type=float, help='The timeout time to set')
    parser.add_argument('--config', type=str, default=os.path.expanduser("~/.gppm/config.yaml"), help='Path to the configuration file')
    args = parser.parse_args()

    config = load_config(args.config)
    url = config.get('server_url', "http://localhost:5000")

    if args.sleep is not None:
        url_ep = url + "/set_sleep_time"
        print(url_ep)
        set_sleep_time(args.sleep, url_ep)

    if args.timeout is not None:
        url_ep = url + "/set_timeout_time"

        set_timeout_time(args.timeout, url + "/set_timeout_time")
