# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import sys
import click
import logging
import errorhandler
import iac_init.validator

from . import options
from iac_init.scripts import create_threadingpool

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
@options.settings_path
def main(
    verbosity: str,
    data: str,
    settings: str
) -> None:
    """A CLI tool to perform APIC initialize."""
    configure_logging(verbosity)

    # Get IP content in APIC IP config file and validate each ip if validate or not
    validator = iac_init.validator.Validator(data, settings)
    error = validator._wrapped()
    if error:
        exit()

    from iac_init.conf import settings

    # Type "yes" or "no" to preform APIC initiator
    option_proceed = click.prompt("Are you sure proceed init following APIC!?\n{}".format(",".join(settings.APIC_DEVICES)),
                                  type=click.Choice(['yes', 'no'], case_sensitive=False))
    validator._validate_bool(option_proceed)

    # Type single number or multiple number (1,2...)
    option_choice = click.prompt(
        "Select single or multiple options to init APIC:\n{}\nExample: (1,2,..)".format("\n".join([f"[{i + 1}]  {option}" for i, option in enumerate(settings.DEFAULT_USER_OPTIONS)])),
        type=validator._validate_choices)
    if not option_choice:
        exit()

    # Type "yes" or "no" to preform APIC initiator
    option_proceed = click.prompt("Are you sure proceed init following Procedures!?\n{}".format("\n".join([f"[{i}]  {settings.DEFAULT_USER_OPTIONS[int(i)-1]}" for i in option_choice])),
                                  type=click.Choice(['yes', 'no'], case_sensitive=False))
    validator._validate_bool(option_proceed)

    create_threadingpool.create_threadingpool(option_choice)

def exit() -> None:
    if error_handler.fired:
        sys.exit(1)
    else:
        sys.exit(0)

