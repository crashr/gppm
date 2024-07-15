import requests
import json
import click
import click_completion

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
def get_instances():
    """Get all LlamaCpp instances."""
    response = requests.get(f"{BASE_URL}/get_llamacpp_instances")
    print(json.dumps(response.json(), indent=4))

@get_group.command('configs')
def get_configs():
    """Get all LlamaCpp configurations."""
    response = requests.get(f"{BASE_URL}/get_llamacpp_configs")
    print(json.dumps(response.json(), indent=4))

@gppmc.command('reload')
def reload_configs():
    """Reload LlamaCpp configurations."""
    response = requests.get(f"{BASE_URL}/reload_llamacpp_configs")
    print(json.dumps(response.json(), indent=4))

if __name__ == "__main__":
    gppmc(auto_envvar_prefix='GPPMC')