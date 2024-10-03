import importlib.util
import subprocess
import sys

from .cli import cli


@cli.command(
    short_help="Run an interactive python shell with all services loaded", name="shell"
)
def shell_command():
    """
    Start an interactive Python shell with preloaded imports.
    """
    # Import botocraft.services
    preload_command = "from botocraft.services import *; import boto3"

    # Check if IPython is installed
    ipython_installed = importlib.util.find_spec("IPython") is not None

    if ipython_installed:
        # If IPython is installed, start IPython with the preloaded command
        subprocess.run(["ipython", "-i", "-c", preload_command], check=False)
    else:
        # If IPython is not installed, start the default Python shell with the
        # preloaded command
        subprocess.run([sys.executable, "-i", "-c", preload_command], check=False)
