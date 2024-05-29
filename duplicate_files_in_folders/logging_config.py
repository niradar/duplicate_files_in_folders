import logging
import os
from datetime import datetime


def setup_logging():
    is_test = 'PYTEST_CURRENT_TEST' in os.environ
    formatter = logging.Formatter('[%(levelname)s]\t%(asctime)s:\t%(message)s')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if not is_test:
        # create logs folder if it doesn't exist
        base_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_folder = os.path.join(base_folder, 'logs')

        os.makedirs(logs_folder, exist_ok=True)

        # Get the current time when the script starts
        log_filename = os.path.join(logs_folder, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
