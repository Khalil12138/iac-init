from loguru import logger
import os

def setup_logging():
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
