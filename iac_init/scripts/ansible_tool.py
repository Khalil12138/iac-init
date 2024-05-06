# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import os
import re
from loguru import logger
from ansible_runner import run
from iac_init.conf import settings

def run_ansible_playbook(step: str, option, inventory_path, playbook_path):
    logger.add(sink=os.path.join(settings.OUTPUT_BASE_DIR, 'iac_init_log', 'iac-init-{}-{}.log'.format(option, step)),
               enqueue=True, format="{message}")

    def callback(res):
        output = re.compile(r'\x1b\[\[?(?:\d{1,2}(?:;\d{0,2})*)?[m|K]').sub('', res['stdout'])
        logger.info(output)

    runner = run(playbook=playbook_path, inventory=inventory_path, verbosity=5, stdout_callback="debug", quiet=True,
                 event_handler=callback)

    if runner.status == "successful":
        logger.info("Successfully finish Step {}: {}".format(option, step.upper()))
        logger.remove()
        return True
    else:
        logger.error("Failed run Step {}: {}".format(option, step.upper()))
        logger.remove()
        return False
