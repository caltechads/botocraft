#!/usr/bin/env python
import sys

import click

import botocraft


@click.group(invoke_without_command=True)
@click.option(
    "--version/--no-version",
    "-v",
    default=False,
    help="Print the current version and exit.",
)
@click.pass_context
def cli(_, version):
    """
    botocraft command line interface.
    """
    if version:
        print(botocraft.__version__)
        sys.exit(0)
