import requests
import json
import click

BASE_URL = "http://localhost:5001"  # TODO Put in config

@click.group()
def cli():
    pass

@cli.command()
def reload_llamacpp_configs():
    response = requests.get(f"{BASE_URL}/reload_llamacpp_configs")
    print(response.json())

@cli.command()
def get_llamacpp_instances():
    response = requests.get(f"{BASE_URL}/get_llamacpp_instances")
    #print(response.text)
    print(response.json())

@cli.command()
def get_llamacpp_configs():
    response = requests.get(f"{BASE_URL}/get_llamacpp_configs")
    #print(response.text)
    print(response.json())

if __name__ == "__main__":
    cli()
