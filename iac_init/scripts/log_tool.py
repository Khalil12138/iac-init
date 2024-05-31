# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Wang Xiao <xiawang3@cisco.com>

import os
from loguru import logger
from iac_init.conf import settings


def log_tool():
    logger.add(
        sink=os.path.join(
            settings.OUTPUT_BASE_DIR,
            'iac_init_log',
            'iac_init_main.log'
        ),
        format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}',
        encoding='utf-8'
    )

    return logger
