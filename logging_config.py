# import logging
# from datetime import datetime
#
#
# def setup_logging():
#     # Get the current time when the script starts
#     log_filename = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
#     logging.basicConfig(
#         level=logging.INFO, handlers=[logging.FileHandler(log_filename)],
#         format='[%(levelname)s]\t%(asctime)s:\t%(message)s'
#     )

import logging
import os
from datetime import datetime


def setup_logging():

    # create logs folder if it doesn't exist
    logs_folder =  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(logs_folder, exist_ok=True)

    # Get the current time when the script starts
    log_filename = os.path.join(logs_folder, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    file_handler = logging.FileHandler(log_filename)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('[%(levelname)s]\t%(asctime)s:\t%(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)