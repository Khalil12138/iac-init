# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Wang Xiao <xiawang3@cisco.com>

import re
import os
import signal
from ansible_runner import run
from iac_init.conf import settings
from iac_init.scripts.log_tool import log_tool

main_logger = log_tool()


def ansible_deploy_function(
        playbook_dir, step_name, option,
        inventory_path=None, quiet=True):

    import logging
    from logging.handlers import RotatingFileHandler

    logger = logging.getLogger(playbook_dir)
    logger.setLevel(logging.INFO)
    log_formatter = logging.Formatter('%(message)s')
    log_file = os.path.join(settings.OUTPUT_BASE_DIR,
                            'iac_init_log',
                            'iac_init_{}_{}.log'.format(option, step_name))
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=30*1024*1024,
        backupCount=0
    )

    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    def callback(res):
        if not quiet and 'stdout' in res:
            print(res['stdout'])
        output = re.compile(r'\x1b\[\[?(?:\d{1,2}(?:;\d{0,2})*)?[m|K]')\
            .sub('', res['stdout'])
        logger.info(output)

    try:
        runner = run(playbook=playbook_dir,
                     inventory=inventory_path,
                     verbosity=5,
                     quiet=True,
                     event_handler=callback)

        if runner.status == "successful":
            main_logger.info("Successfully finished Step {}: {}"
                             .format(option, step_name.upper()))
            return True

        else:
            main_logger.error("Failed run Step {}: {}"
                              .format(option, step_name.upper()))
            os.kill(os.getpid(), signal.SIGILL)
            return False

    except Exception as e:
        main_logger.error("Failed run Step {}: {}"
                          .format(option, step_name.upper()))
        main_logger.error("Error: {}".format(Exception))
        os.kill(os.getpid(), signal.SIGILL)
        return False
