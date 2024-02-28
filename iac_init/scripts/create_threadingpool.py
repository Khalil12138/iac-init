# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Wang Xiao <xiawang3@cisco.com>

import logging
import concurrent.futures

from iac_init.conf import settings

logger = logging.getLogger(__name__)

def execute_init_procedure(ip: str, procedure: list, index: int):
    try:
        print("Device {} will start procedure {}".format(ip, procedure))
    except Exception as e:
        msg = f"Error occurred in thread {index}: {e}"
        logger.error(msg)

def create_threadingpool(choices):
    # Threading pool number
    num_thread_pools = len(settings.APIC_DEVICES)

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_thread_pools) as executor:
            futures = {executor.submit(execute_init_procedure, settings.APIC_DEVICES[i], choices, i): i for i in
                       range(num_thread_pools)}
    except Exception as e:
        msg = f"Error occurred in _create_threadingpool: {e}"
        logger.error(msg)
        return
