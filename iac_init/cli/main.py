# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Wang Xiao <xiawang3@cisco.com>

import os
import sys
import click
import shutil
import errorhandler
import iac_init.validator

from . import options
from loguru import logger
from iac_init.conf import settings
from iac_init.yaml_conf import yaml_writer
from iac_init.scripts.thread_tool import MyThread
from iac_init.scripts.ansible_tool import ansible_deploy_function

error_handler = errorhandler.ErrorHandler()


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(iac_init.__version__)
@options.yaml_dir_path
def main(
        data: str
) -> None:
    """A CLI tool to bootstrap and configure ACI fabric using ACI as Code."""
    output = settings.OUTPUT_BASE_DIR

    if os.path.exists(output) and os.path.isdir(output):
        shutil.rmtree(output)

    logger.add(
        sink=os.path.join(
            settings.OUTPUT_BASE_DIR,
            'iac_init_log',
            'iac_init_main.log'
        ),
        format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}',
        encoding='utf-8'
    )

    validator = iac_init.validator.Validator(data, output)

    # Type single number or multiple numbers (1,2...)
    option_prompt = "Select single or multiple option(s) " \
                    "to init ACI Fabric:\n{}\nExample: (1,2,..)"\
        .format("\n".join([f"[{i + 1}]  {option}" for i, option
                           in enumerate(settings.DEFAULT_USER_OPTIONS)]))
    option_choice = click.prompt(
        click.style(option_prompt, fg='green'),
        type=validator.validate_choices)
    if not option_choice:
        exit()

    # Type "yes" or "no" to confirm
    option_prompt = "\nAre you sure to proceed with following option(s)?\n{}\n"\
        .format("\n".join([f"[{i}]  {settings.DEFAULT_USER_OPTIONS[int(i)-1]}"
                           for i in option_choice]))
    option_proceed = click.prompt(
        click.style(option_prompt, fg='green'),
        type=click.Choice(['yes', 'no'], case_sensitive=False)
    )
    validator._validate_bool(option_proceed)

    error = validator._wrapped()
    if error:
        logger.error("Option(s) validated failed, exiting...")
        exit()
    logger.info("Option(s) validated.")

    for option in option_choice:
        logger.info("Start processing step {}.".format(option))
        if int(option) in [1]:
            error = validator.validate_ssh_telnet_connection()
            if error:
                exit()
            yaml_path = validator.validate_yaml_exist(
                settings.DEFAULT_DATA_PATH
            )
            if not yaml_path:
                exit()
            error = validator.validate_cimc_precheck()
            if error:
                exit()
            # Rudy: If only 1, this might not need to check
            option_yaml_path = validator.validate_yaml_exist(
                settings.DATA_PATH[int(option)-1]
            )
            if not option_yaml_path:
                exit()
            try:
                writer = yaml_writer.YamlWriter([yaml_path])
                writer.write(settings.TEMPLATE_DIR[int(option) - 1], output)
                logger.info("Generate step {} working directory in {} successfully."
                            .format(option, output))

                dir_path = os.path.join(
                    output,
                    os.path.basename(settings.TEMPLATE_DIR[int(option)-1]),
                    'aci_switch_reimage',
                    'vars'
                )
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    yaml_cp_output_path = os.path.join(dir_path, 'main.yml')
                    shutil.copy(option_yaml_path, yaml_cp_output_path)
                    logger.info("Copied switch YAML file to {} successfully."
                                .format(yaml_cp_output_path))

                dir_path = os.path.join(
                    output,
                    os.path.basename(settings.TEMPLATE_DIR[int(option)-1]),
                    'apic_reimage',
                    'vars'
                )
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    yaml_cp_output_path = os.path.join(dir_path, 'main.yml')
                    shutil.copy(option_yaml_path, yaml_cp_output_path)
                    logger.info("Copied APIC YAML file to {} successfully."
                                .format(yaml_cp_output_path))

            except Exception as e:
                msg = "Generate working directory failed.\nDetail: {}".format(e)
                logger.error(msg)
                exit()

            try:
                playbook_dir_apic = os.path.join(
                    os.getcwd(),
                    output,
                    os.path.basename(settings.TEMPLATE_DIR[int(option)-1]),
                    "playbook_apic_init.yaml"
                )

                playbook_dir_switch = os.path.join(
                    os.getcwd(),
                    output,
                    os.path.basename(settings.TEMPLATE_DIR[int(option)-1]),
                    "playbook_aci_switch_init.yaml"
                )

                thread1 = MyThread(
                    target=ansible_deploy_function,
                    args=(
                        playbook_dir_apic,
                        settings.ANSIBLE_STEP[3],
                        option,
                        None,
                        True)
                )
                thread2 = MyThread(
                    target=ansible_deploy_function,
                    args=(
                        playbook_dir_switch,
                        settings.ANSIBLE_STEP[4],
                        option,
                        None,
                        True)
                )

                logger.info("ACI fabric bootstrap in progress, "
                            "check APIC/switch logs for detail.")

                thread1.start()
                thread2.start()

                thread1.join()
                thread2.join()

                if thread1.get_result() and thread2.get_result():
                    logger.info("ACI fabric bootstrap is successfully.")
                else:
                    logger.error(
                        "ACI fabric bootstrap failed, "
                        "check APIC/switch logs for detail."
                    )
                    exit()

            except Exception as e:
                msg = "Run Step 1 ACI fabric bootstrap ansible-playbook" \
                      " failed.\nDetail: {}".format(e)
                logger.error(msg)
                exit()

        elif int(option) in [2]:
            yaml_path = validator.validate_yaml_exist(
                settings.DEFAULT_DATA_PATH
            )
            if not yaml_path:
                exit()
            error = validator.validate_cimc_precheck()
            if error:
                exit()
            option_yaml_path = validator.validate_yaml_exist(
                settings.DATA_PATH[int(option)-1]
            )
            if not option_yaml_path:
                exit()
            try:
                writer = yaml_writer.YamlWriter([yaml_path])
                writer.write(settings.TEMPLATE_DIR[int(option)-1], output)
                logger.info(
                    "Generate step {} working directory in {} successfully."
                    .format(option, output)
                )

                dir_path = os.path.join(
                    output,
                    os.path.basename(settings.TEMPLATE_DIR[int(option)-1]),
                    'apic_discovery',
                    'vars'
                )
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    yaml_cp_output_path = os.path.join(dir_path, 'main.yml')
                    shutil.copy(option_yaml_path, yaml_cp_output_path)
                    logger.info(
                        "Copied APIC YAML file to {} successfully."
                        .format(yaml_cp_output_path)
                    )

            except Exception as e:
                msg = "Generate working directory failed.\nDetail: {}".format(e)
                logger.error(msg)
                exit()

            try:
                playbook_dir = os.path.join(
                    os.getcwd(),
                    output,
                    os.path.basename(settings.TEMPLATE_DIR[int(option)-1]),
                    "playbook_apic_discovery.yaml"
                )

                run_result = ansible_deploy_function(
                    playbook_dir=playbook_dir,
                    step_name=settings.ANSIBLE_STEP[5],
                    option=option,
                    quiet=False
                )
                if run_result:
                    logger.info("APIC init successfully.")
                else:
                    logger.error("APIC init failed!")
                    exit()

            except Exception as e:
                msg = "Run Step 2 APIC init ansible-playbook" \
                      " failed.\nDetail: {}".format(e)
                logger.error(msg)
                exit()

        elif int(option) in [3]:
            error = validator.validate_apic_aaa_connection()
            if error:
                exit()
            yaml_path = validator.validate_yaml_exist(
                settings.DEFAULT_DATA_PATH
            )
            if not yaml_path:
                exit()
            option_yaml_path = validator.validate_yaml_dir_exist(
                settings.DATA_PATH[int(option)-1]
            )
            if not option_yaml_path:
                exit()
            try:
                writer = yaml_writer.YamlWriter([yaml_path])
                writer.write(
                    settings.TEMPLATE_DIR[int(option)-1],
                    output
                )
                logger.info(
                    "Generate step {} working directory in {} successfully."
                    .format(option, output)
                )
                dir_path = os.path.join(
                    output,
                    os.path.basename(settings.TEMPLATE_DIR[int(option)-1]),
                    'host_vars',
                    'apic1'
                )
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    yaml_cp_output_path = os.path.join(
                        dir_path,
                        'data.yaml'
                    )
                    result = validator.write_output(
                        option_yaml_path,
                        yaml_cp_output_path
                    )
                    if not result:
                        exit()

            except Exception as e:
                msg = "Generate working directory failed.\nDetail: {}"\
                    .format(e)
                logger.error(msg)
                exit()

            try:
                inventory_path = os.path.join(
                    os.getcwd(),
                    output,
                    os.path.basename(settings.TEMPLATE_DIR[int(option)-1]),
                    'inventory.yaml'
                )
                playbook_dir_validate = os.path.join(
                    os.getcwd(),
                    output,
                    os.path.basename(settings.TEMPLATE_DIR[int(option)-1]),
                    'aac_ansible',
                    "apic_validate.yaml"
                )

                playbook_dir_deploy = os.path.join(
                    os.getcwd(),
                    output,
                    os.path.basename(settings.TEMPLATE_DIR[int(option)-1]),
                    'aac_ansible',
                    "apic_deploy.yaml"
                )

                playbook_dir_test = os.path.join(
                    os.getcwd(),
                    output,
                    os.path.basename(settings.TEMPLATE_DIR[int(option)-1]),
                    'aac_ansible',
                    "apic_test.yaml"
                )

                validate_result = ansible_deploy_function(
                    playbook_dir=playbook_dir_validate,
                    step_name=settings.ANSIBLE_STEP[0],
                    inventory_path=inventory_path,
                    option=option,
                    quiet=False)

                if not validate_result:
                    exit()

                deploy_result = ansible_deploy_function(
                    playbook_dir=playbook_dir_deploy,
                    step_name=settings.ANSIBLE_STEP[1],
                    inventory_path=inventory_path,
                    option=option,
                    quiet=False
                )

                if not deploy_result:
                    exit()

                test_result = ansible_deploy_function(
                    playbook_dir=playbook_dir_test,
                    step_name=settings.ANSIBLE_STEP[2],
                    inventory_path=inventory_path,
                    option=option,
                    quiet=False
                )

                if not test_result:
                    exit()

            except Exception as e:
                msg = "Run Step 3 NaC ansible-playbook" \
                      " failed.\nDetail: {}".format(e)
                logger.error(msg)
                exit()


def exit() -> None:
    if error_handler.fired:
        sys.exit(1)
    else:
        sys.exit(0)
