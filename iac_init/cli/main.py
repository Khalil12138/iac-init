# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import os
import re
import sys
import click
import shutil
import logging
import threading
import errorhandler
import iac_init.validator

from . import options
from loguru import logger
from ansible_runner import run
from iac_init.conf import settings
from iac_init.yaml_conf import yaml_writer
from iac_init.scripts.ansible_tool import run_ansible_playbook

error_handler = errorhandler.ErrorHandler()
ansible_run_result = 1

@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(iac_init.__version__)
@options.yaml_dir_path
def main(
        data: str
) -> None:
    """A CLI tool to perform APIC initialize."""
    output = settings.OUTPUT_BASE_DIR

    if os.path.exists(output) and os.path.isdir(output):
        shutil.rmtree(output)

    logger.add(sink=os.path.join(settings.OUTPUT_BASE_DIR, 'iac_init_log', 'iac-init-main.log'),
               format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}', encoding='utf-8')

    validator = iac_init.validator.Validator(data, output)

    # Type single number or multiple number (1,2...)
    option_prompt = "Select single or multiple options to init APIC:\n{}\nExample: (1,2,..)".format(
        "\n".join([f"[{i + 1}]  {option}" for i, option in enumerate(settings.DEFAULT_USER_OPTIONS)]))
    option_choice = click.prompt(
        click.style(option_prompt, fg='green'),
        type=validator.validate_choices)
    if not option_choice:
        exit()

    # Type "yes" or "no" to preform APIC initiator
    option_prompt = "\nAre you sure proceed init following Procedures!?\n{}\n".format(
        "\n".join([f"[{i}]  {settings.DEFAULT_USER_OPTIONS[int(i) - 1]}" for i in option_choice]))
    option_proceed = click.prompt(click.style(option_prompt, fg='green'),
                                  type=click.Choice(['yes', 'no'], case_sensitive=False))
    validator._validate_bool(option_proceed)

    error = validator._wrapped()
    if error:
        exit()
    logger.info("Initial Validation of Yamls Directory Success!!")

    for option in option_choice:
        logger.info("Start proceeding step {}.".format(option))
        if int(option) in [1]:
            error = validator.validate_ssh_telnet_connection()
            if error:
                exit()
            yaml_path = validator.validate_yaml_exist(settings.DEFAULT_DATA_PATH)
            if not yaml_path:
                exit()
            error = validator.validate_cimc_precheck()
            if error:
                exit()
            option_yaml_path = validator.validate_yaml_exist(settings.DATA_PATH[int(option) - 1])
            if not option_yaml_path:
                exit()
            try:
                writer = yaml_writer.YamlWriter([yaml_path])
                writer.write(settings.TEMPLATE_DIR[int(option) - 1], output)
                logger.info("Generate Step {} working directory forder in {} Success!!".format(option, output))

                dir_path = os.path.join(output, os.path.basename(settings.TEMPLATE_DIR[int(option) - 1]),
                                        'aci_switch_reimage', 'vars')
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    yaml_cp_output_path = os.path.join(dir_path, 'main.yml')
                    shutil.copy(option_yaml_path, yaml_cp_output_path)
                    logger.info("Copied Yaml file to {} success.".format(yaml_cp_output_path))

                dir_path = os.path.join(output, os.path.basename(settings.TEMPLATE_DIR[int(option) - 1]),
                                        'apic_reimage', 'vars')
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    yaml_cp_output_path = os.path.join(dir_path, 'main.yml')
                    shutil.copy(option_yaml_path, yaml_cp_output_path)
                    logger.info("Copied Yaml file to {} success.".format(yaml_cp_output_path))

            except Exception as e:
                msg = "Generate working directory fail, detail: {}".format(e)
                logger.error(msg)
                exit()

            try:
                def ansible_deploy_function(playbook_name, step_name):
                    import logging
                    from logging.handlers import TimedRotatingFileHandler

                    playbook_dir = os.path.join(os.getcwd(), output,
                                                os.path.basename(settings.TEMPLATE_DIR[int(option) - 1]),
                                                playbook_name)

                    logger = logging.getLogger(playbook_dir)
                    logger.setLevel(logging.INFO)
                    log_formatter = logging.Formatter('%(message)s')
                    log_file = os.path.join(settings.OUTPUT_BASE_DIR, 'iac_init_log',
                                                 'iac-init-{}-{}.log'.format(option, step_name))
                    file_handler = TimedRotatingFileHandler(log_file, when="M", interval=30, backupCount=0)
                    file_handler.setFormatter(log_formatter)
                    logger.addHandler(file_handler)

                    def callback(res):
                        output = re.compile(r'\x1b\[\[?(?:\d{1,2}(?:;\d{0,2})*)?[m|K]').sub('', res['stdout'])
                        logger.info(output)

                    runner = run(playbook=playbook_dir, inventory=None, verbosity=5,
                                 quiet=True, event_handler=callback)

                    if runner.status == "successful":
                        logger.info("Successfully finish Step {}: {}".format(option, step_name.upper()))

                    else:
                        logger.error("Failed run Step {}: {}".format(option, step_name.upper()))
                        global ansible_run_result
                        ansible_run_result = 0
                        exit()

                thread1 = threading.Thread(target=ansible_deploy_function,
                                           args=("playbook_apic_init.yaml", settings.ANSIBLE_STEP[3]))
                thread2 = threading.Thread(target=ansible_deploy_function,
                                           args=("playbook_aci_switch_init.yaml", settings.ANSIBLE_STEP[4]))

                logger.info("Wipe aci fabric start pls wait, check log for detail.")

                thread1.start()
                thread2.start()

                thread1.join()
                thread2.join()

                global ansible_run_result
                if ansible_run_result == 0:
                    logger.error("Exist iac-init tool Step 1 failed pls check log for detail")
                else:
                    logger.info("Wipe aci fabric Success proceed.")

            except Exception as e:
                msg = "Run Step 1 wipe aci fabric ansible-playbook failed detail:\nError: {}".format(e)
                logger.error(msg)
                exit()

        elif int(option) in [2]:
            yaml_path = validator.validate_yaml_exist(settings.DEFAULT_DATA_PATH)
            if not yaml_path:
                exit()
            error = validator.validate_cimc_precheck()
            if error:
                exit()
            option_yaml_path = validator.validate_yaml_exist(settings.DATA_PATH[int(option) - 1])
            if not option_yaml_path:
                exit()
            try:
                writer = yaml_writer.YamlWriter([yaml_path])
                writer.write(settings.TEMPLATE_DIR[int(option) - 1], output)
                logger.info("Generate Step {} working directory forder in {} Success!!".format(option, output))

                dir_path = os.path.join(output, os.path.basename(settings.TEMPLATE_DIR[int(option) - 1]),
                                        'apic_discovery', 'vars')
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    yaml_cp_output_path = os.path.join(dir_path, 'main.yml')
                    shutil.copy(option_yaml_path, yaml_cp_output_path)
                    logger.info("Copied Yaml file to {} success.".format(yaml_cp_output_path))

            except Exception as e:
                msg = "Generate working directory fail, detail: {}".format(e)
                logger.error(msg)
                exit()

            try:
                def ansible_deploy_function(playbook_name, step_name):
                    import logging
                    from logging.handlers import TimedRotatingFileHandler

                    playbook_dir = os.path.join(os.getcwd(), output,
                                                os.path.basename(settings.TEMPLATE_DIR[int(option) - 1]),
                                                playbook_name)

                    logger = logging.getLogger(playbook_dir)
                    logger.setLevel(logging.INFO)
                    log_formatter = logging.Formatter('%(message)s')
                    log_file = os.path.join(settings.OUTPUT_BASE_DIR, 'iac_init_log',
                                                 'iac-init-{}-{}.log'.format(option, step_name))
                    file_handler = TimedRotatingFileHandler(log_file, when="M", interval=30, backupCount=0)
                    file_handler.setFormatter(log_formatter)
                    logger.addHandler(file_handler)

                    def callback(res):
                        output = re.compile(r'\x1b\[\[?(?:\d{1,2}(?:;\d{0,2})*)?[m|K]').sub('', res['stdout'])
                        logger.info(output)

                    runner = run(playbook=playbook_dir, inventory=None, verbosity=5,
                                 quiet=True, event_handler=callback)

                    if runner.status == "successful":
                        logger.info("Successfully finish Step {}: {}".format(option, step_name.upper()))

                    else:
                        logger.error("Failed run Step {}: {}".format(option, step_name.upper()))
                        exit()

                ansible_deploy_function("playbook_apic_discovery.yaml", settings.ANSIBLE_STEP[5])

            except Exception as e:
                msg = "Run Step 2 APIC discovery ansible-playbook fail detail:\nError: {}".format(e)
                logger.error(msg)
                exit()

        else:
            error = validator.validate_apic_aaa_connection()
            if error:
                exit()
            yaml_path = validator.validate_yaml_exist(settings.DEFAULT_DATA_PATH)
            if not yaml_path:
                exit()
            option_yaml_path = validator.validate_yaml_exist(settings.DATA_PATH[int(option) - 1])
            if not option_yaml_path:
                exit()
            try:
                writer = yaml_writer.YamlWriter([yaml_path])
                writer.write(settings.TEMPLATE_DIR[int(option) - 1], output)
                logger.info("Generate Step {} working directory forder in {} Success!!".format(option, output))
                dir_path = os.path.join(output, os.path.basename(settings.TEMPLATE_DIR[int(option) - 1]),
                                        'host_vars', 'apic1')
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    yaml_cp_output_path = os.path.join(dir_path, settings.DATA_PATH[int(option) - 1])
                    shutil.copy(option_yaml_path, yaml_cp_output_path)
                    logger.info("Copied Yaml file to {} success.".format(yaml_cp_output_path))
            except Exception as e:
                msg = "Generate working directory fail, detail: {}".format(e)
                logger.error(msg)
                exit()

            try:
                inventory_path = os.path.join(os.getcwd(), output,
                                              os.path.basename(settings.TEMPLATE_DIR[int(option) - 1]),
                                              'inventory.yaml')
                playbook_dir = os.path.join(os.getcwd(), output,
                                            os.path.basename(settings.TEMPLATE_DIR[int(option) - 1]),
                                            'aac_ansible')

                validate_result = run_ansible_playbook(settings.ANSIBLE_STEP[0], option, inventory_path,
                                                       os.path.join(playbook_dir, "apic_validate.yaml"))
                if not validate_result:
                    exit()

                deploy_result = run_ansible_playbook(settings.ANSIBLE_STEP[1], option, inventory_path,
                                                     os.path.join(playbook_dir, "apic_deploy.yaml"))
                if not deploy_result:
                    exit()

                test_result = run_ansible_playbook(settings.ANSIBLE_STEP[2], option, inventory_path,
                                                   os.path.join(playbook_dir, "apic_test.yaml"))
                if not test_result:
                    exit()

            except Exception as e:
                msg = "Run NAC ansible-playbook fail detail:\nError: {}".format(e)
                logger.error(msg)
                exit()


def exit() -> None:
    if error_handler.fired:
        sys.exit(1)
    else:
        sys.exit(0)
