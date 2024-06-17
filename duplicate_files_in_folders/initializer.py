import logging
import os
from argparse import Namespace
from datetime import datetime

from duplicate_files_in_folders.file_manager import FileManager
from duplicate_files_in_folders.hash_manager import HashManager
from duplicate_files_in_folders.utils import detect_pytest


def setup_logging():
    """
    Setup logging for the script. Logs are saved in the logs folder. The log file is named log_<current_date_time>.txt
    Only errors (and above) are logged to the console.
    :return: None
    """
    formatter = logging.Formatter('[%(levelname)s]\t%(asctime)s:\t%(message)s')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if not detect_pytest():
        # create logs folder if it doesn't exist
        base_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_folder = os.path.join(base_folder, 'logs')

        os.makedirs(logs_folder, exist_ok=True)

        # Get the current time when the script starts
        log_filename = os.path.join(logs_folder, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def setup_hash_manager(reference_dir: str = None, full_hash: bool = False, clear_cache: bool = False):
    """
    Setup the hash manager with the given reference directory and full hash setting.
    :param reference_dir: the reference directory
    :param full_hash: whether to use full hash
    :param clear_cache: whether to clear the cache
    :return: the hash manager instance
    """
    hash_manager = HashManager(reference_dir=reference_dir if not detect_pytest() else None,
                               full_hash=full_hash)
    if clear_cache:
        hash_manager.clear_cache()
        hash_manager.save_data()
    return hash_manager


def setup_file_manager(args: Namespace):
    """
    Setup the file manager with the reference and scan directories and the move to directory from the arguments.
    :param args: the parsed arguments
    :return: the file manager instance
    """
    fm = FileManager.reset_file_manager([args.reference_dir], [args.scan_dir, args.move_to], args.run)
    return fm
