import click
import requests
import json
import yaml
from halo import Halo
import click_completion


click_completion.init()


@click.group()
@click.option("--host", default="localhost", help="The host to connect to.")
@click.option("--port", default=5001, type=int, help="The port to connect to.")
@click.pass_context
def gppmc(ctx, host, port):
    """Group of commands for managing LlamaCpp instances and configurations."""
    ctx.obj["BASE_URL"] = f"http://{host}:{port}"


@gppmc.group("get")
def get_group():
    """Get various resources."""
    pass


@get_group.command("instances")
@click.option(
    "--format",
    default="text",
    type=click.Choice(["json", "text"]),
    help="Print output in JSON or text format.",
)
@click.pass_context
def get_instances(ctx, format):
    """Get all LlamaCpp instances."""
    base_url = ctx.obj["BASE_URL"]
    if format == "text":
        with Halo(text="Loading instances", spinner="dots"):
            response = requests.get(f"{base_url}/get_llamacpp_instances")
    else:
        response = requests.get(f"{base_url}/get_llamacpp_instances")

    if format == "json":
        print(response.json())
    else:
        instances = response.json()["llamacpp_instances"]
        for instance in instances:
            print(instance)


@get_group.command("configs")
@click.option(
    "--format",
    default="text",
    type=click.Choice(["json", "text"]),
    help="Print output in JSON or text format.",
)
@click.pass_context
def get_configs(ctx, format):
    """Get all LlamaCpp configurations."""
    base_url = ctx.obj["BASE_URL"]
    if format == "text":
        with Halo(text="Loading configurations", spinner="dots"):
            response = requests.get(f"{base_url}/get_llamacpp_configs")

    if format == "json":
        print(response.json())
    else:
        print(response.json())
        # configs = response.json()["llamacpp_configs"]
        # for config in configs:
        #    print(config)


@gppmc.command("apply")
@click.argument("file", type=click.File("rb"))
@click.option(
    "--format",
    default="text",
    type=click.Choice(["json", "text"]),
    help="Print output in JSON or text format.",
)
@click.pass_context
def apply_configs(ctx, file, format):
    """Apply LlamaCpp configurations from a YAML file."""
    data = yaml.safe_load(file)
    base_url = ctx.obj["BASE_URL"]
    if format == "text":
        with Halo(text="Applying configurations", spinner="dots"):
            response = requests.post(f"{base_url}/apply_llamacpp_configs", json=data)
    else:
        response = requests.post(f"{base_url}/apply_llamacpp_configs", json=data)
        print(response.json())


@get_group.command("subprocesses")
@click.pass_context
def get_subprocesses(ctx):
    """Get all LlamaCpp subprocesses."""
    base_url = ctx.obj["BASE_URL"]
    with Halo(text="Loading subprocesses", spinner="dots"):
        response = requests.get(f"{base_url}/get_llamacpp_subprocesses")
    print(json.dumps(response.json(), indent=4))
    # print(response)


@gppmc.command("reload")
@click.pass_context
def reload_configs(ctx):
    """Reload LlamaCpp configurations."""
    base_url = ctx.obj["BASE_URL"]
    with Halo(text="Reloading configurations", spinner="dots"):
        response = requests.get(f"{base_url}/reload_llamacpp_configs")
    # print(json.dumps(response.json(), indent=4))  # TODO
    print(response)


@gppmc.command("enable")
@click.argument("name")
@click.pass_context
def enable_instance(ctx, name):
    """Enable a LlamaCpp instance."""
    base_url = ctx.obj["BASE_URL"]
    with Halo(text=f"Enabling instance {name}", spinner="dots"):
        response = requests.post(
            f"{base_url}/enable_llamacpp_instance", json={"name": name}
        )
    # print(response.json())
    print(response)


@gppmc.command("disable")
@click.argument("name")
@click.pass_context
def disable_instance(ctx, name):
    """Disable a LlamaCpp instance."""
    base_url = ctx.obj["BASE_URL"]
    with Halo(text=f"Disabling instance {name}", spinner="dots"):
        response = requests.post(
            f"{base_url}/disable_llamacpp_instance", json={"name": name}
        )
    # print(response.json())
    print(response)


if __name__ == "__main__":
    gppmc(obj={})
