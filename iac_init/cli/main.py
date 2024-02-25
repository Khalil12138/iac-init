# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import logging
import sys
from typing import List

import click
import errorhandler

import iac_init.initiator

from . import options

logger = logging.getLogger(__name__)

error_handler = errorhandler.ErrorHandler()


def configure_logging(level: str) -> None:
    if level == "DEBUG":
        lev = logging.DEBUG
    elif level == "INFO":
        lev = logging.INFO
    elif level == "WARNING":
        lev = logging.WARNING
    elif level == "ERROR":
        lev = logging.ERROR
    else:
        lev = logging.CRITICAL
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(lev)
    error_handler.reset()


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(iac_init.__version__)
@click.option(
    "-v",
    "--verbosity",
    metavar="LVL",
    is_eager=True,
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]),
    help="Either CRITICAL, ERROR, WARNING, INFO or DEBUG",
    default="WARNING",
)

@options.path
def main(
    verbosity: str,
    fabric_config: str,
) -> None:
    """A CLI tool to perform APIC initialize."""
    configure_logging(verbosity)

    initiator = iac_init.initiator.Initiator(fabric_config)
    error = initiator._validate_ip_config()
    if error:
        exit()

def exit() -> None:
    if error_handler.fired:
        sys.exit(1)
    else:
        sys.exit(0)
