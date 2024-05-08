# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import re
import os
from ansible_runner import run
from iac_init.conf import settings

def ansible_deploy_function(playbook_dir, step_name, option, inventory_path=None, quiet=True):
    import logging
    from logging.handlers import TimedRotatingFileHandler

    logger = logging.getLogger(playbook_dir)
    logger.setLevel(logging.INFO)
    log_formatter = logging.Formatter('%(message)s')
    log_file = os.path.join(settings.OUTPUT_BASE_DIR, 'iac_init_log',
                            'iac-init-{}-{}.log'.format(option, step_name))
    file_handler = TimedRotatingFileHandler(log_file, when="M", interval=30, backupCount=0)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    def callback(res):
        if not quiet and 'stdout' in res:
            print(res['stdout'])
        output = re.compile(r'\x1b\[\[?(?:\d{1,2}(?:;\d{0,2})*)?[m|K]').sub('', res['stdout'])
        logger.info(output)

    runner = run(playbook=playbook_dir, inventory=inventory_path, verbosity=5,
                 quiet=True, event_handler=callback)

    if runner.status == "successful":
        logger.info("Successfully finish Step {}: {}".format(option, step_name.upper()))
        return True

    else:
        logger.error("Failed run Step {}: {}".format(option, step_name.upper()))
        return False