# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import os
from loguru import logger
from ansible_runner import run
from iac_init.conf import settings

def run_ansible_playbook(step: str, option, inventory_path, playbook_path):
    logger.add(sink=os.path.join(settings.OUTPUT_BASE_DIR, 'iac_init_log', 'iac-init-{}-{}.log'.format(option, step)))

    runner = run(playbook=playbook_path, inventory=inventory_path, verbosity=5)
    logger.info(runner.stdout.read())

    if runner.status == "successful":
        logger.info("Successfully finish Step {}: {}".format(option, step.upper()))
        return True
    else:
        logger.error("Failed run Step {}: {}".format(option, step.upper()))
        return False
