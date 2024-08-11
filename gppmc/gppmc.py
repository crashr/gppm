import requests
import json
import click
import click_completion
from halo import Halo
import yaml

click_completion.init()

BASE_URL = "http://localhost:5001"

@click.group()
def gppmc():
    """Group of commands for managing LlamaCpp instances and configurations."""
    pass

@gppmc.group('get')
def get_group():
    """Get various resources."""
    pass

@get_group.command('instances')
@click.option('--format', default='text', type=click.Choice(['json', 'text']), help='Print output in JSON or text format.')
def get_instances(format):
    """Get all LlamaCpp instances."""
    if format == 'text':
        with Halo(text='Loading instances', spinner='dots'):
            response = requests.get(f"{BASE_URL}/get_llamacpp_instances")
    else:
        response = requests.get(f"{BASE_URL}/get_llamacpp_instances")

    if format == 'json':
        #print(json.dumps(response.json(), indent=4))
        print(response.json())
    else:
        instances = response.json()["llamacpp_instances"]
        for instance in instances:
            print(instance)


@gppmc.command('apply')
@click.argument('file', type=click.File('rb'))
@click.option('--format', default='text', type=click.Choice(['json', 'text']), help='Print output in JSON or text format.')
def apply_configs(file, format):
    """Apply LlamaCpp configurations from a YAML file."""
    data = yaml.safe_load(file)

    if format == 'text':
        with Halo(text='Applying configurations', spinner='dots'):
            response = requests.post(f"{BASE_URL}/apply_llamacpp_configs", json=data)
        #print(response.text)
    else:
        response = requests.post(f"{BASE_URL}/apply_llamacpp_configs", json=data)
        print(response.json())


@get_group.command('configs')
def get_configs():
    """Get all LlamaCpp configurations."""
    with Halo(text='Loading configurations', spinner='dots'):
        response = requests.get(f"{BASE_URL}/get_llamacpp_configs")
    print(json.dumps(response.json(), indent=4))

@gppmc.command('reload')
def reload_configs():
    """Reload LlamaCpp configurations."""
    with Halo(text='Reloading configurations', spinner='dots'):
        response = requests.get(f"{BASE_URL}/reload_llamacpp_configs")
    print(json.dumps(response.json(), indent=4))

if __name__ == "__main__":
    gppmc(auto_envvar_prefix='GPPMC')
