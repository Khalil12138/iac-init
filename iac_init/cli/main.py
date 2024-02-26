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

    # Get IP content in APIC IP config file and validate each ip if validate or not
    initiator = iac_init.initiator.Initiator(fabric_config)
    error = initiator._validate_ip_config()
    if error:
        exit()

    # Type "yes" or "no" to preform APIC initiator
    option_proceed = click.prompt("Are you sure proceed init following APIC!?\n{}".format(initiator.ip_str), type=click.Choice(['yes', 'no'], case_sensitive=False))
    if option_proceed == "yes":
        option = click.prompt("Select singel or multiple options to init APIC:\n[1] APIC/Switch PXE boot up\n[2] Fabric discovery(Single Pod, Multi Pod, Multi Site, Remote Leaf, etc..)\n[3] Management Configuration(INB, OOB, NTP, DNS, AAA, etc..)\n[4] Fabric policy creation\n[5] Access policy creation\n[6] Fabric features(SNMP, syslog, etc..)\nExample: (1,2,..6)", type=initiator._validate_choices)
        if not option:
            exit()
        option_options = click.prompt("Are you sure proceed init following Procedures!?\n{}".format(initiator.options), type=click.Choice(['yes', 'no'], case_sensitive=False))
        if option_options== "yes":
            error = initiator._create_threadingpool()
            if error:
                exit()
        else:
            exit()
    else:
        exit()

def exit() -> None:
    if error_handler.fired:
        sys.exit(1)
    else:
        sys.exit(0)
