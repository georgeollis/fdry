"""Explicit command registration. Resource modules do not depend on each other."""

import click

from fdry.commands.accounts import account
from fdry.commands.agents import agent
from fdry.commands.auth import auth
from fdry.commands.config import config
from fdry.commands.connections import connection
from fdry.commands.datasets import dataset
from fdry.commands.evaluations import evaluation
from fdry.commands.files import files
from fdry.commands.fine_tuning import fine_tuning
from fdry.commands.indexes import index
from fdry.commands.models import model
from fdry.commands.projects import project
from fdry.commands.quota import quota
from fdry.commands.rest import rest
from fdry.commands.toolboxes import toolbox


def register_commands(cli: click.Group) -> None:
    for command in (
        account,
        agent,
        auth,
        config,
        connection,
        dataset,
        evaluation,
        files,
        fine_tuning,
        index,
        model,
        project,
        quota,
        rest,
        toolbox,
    ):
        cli.add_command(command)
