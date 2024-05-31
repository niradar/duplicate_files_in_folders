import argparse
import logging
import os
import sys
from typing import List

from duplicate_files_in_folders.hash_manager import HashManager

logger = logging.getLogger(__name__)


def validate_folder(folder, name):
    """ Validate if a folder exists and is not empty. """
    if not os.path.isdir(folder) or not os.path.exists(folder):
        print_error(f"{name} folder does not exist.")
    if not os.listdir(folder):
        print_error(f"{name} folder is empty.")
    return True


def log_and_print(message):
    print(message)
    logger.info(message)


def display_initial_config(args):
    header = "=== Script Configuration ==="
    separator = "-" * 50
    blank_line = ""
    fixed_width = 25

    config_items = {
        "Source Folder": args.src,
        "Target Folder": args.target,
        "\"Move to\" Folder": args.move_to,
        "Ignoring Settings": get_ignore_diff_string(args.ignore_diff),
        "Files Content": "Full Content Check (Slower)" if args.full_hash else "Partial Content Check (Faster)",
        "Size Constraints": get_size_constraints_string(args.min_size, args.max_size),
    }
    # args.whitelist_ext is a set
    if args.whitelist_ext:
        config_items["File Types (Whitelist)"] = ', '.join(args.whitelist_ext)
    elif args.blacklist_ext:
        config_items["File Types (Blacklist)"] = ', '.join(args.blacklist_ext)

    if not args.delete_empty_folders:
        config_items["Empty Folders"] = "Do Not Delete Empty Folders in Source Folder"

    config_items["Script Mode"] = "Run Mode" if args.run else "Test Mode"

    # Print header
    log_and_print(blank_line)
    log_and_print(header)
    log_and_print(separator)

    # Print configuration items
    for key, value in config_items.items():
        log_and_print(f"{key.ljust(fixed_width)}: {value}")

    # Print footer
    log_and_print(separator)
    log_and_print(blank_line)


def get_ignore_diff_string(ignore_diff_set):
    ignore_options = {
        'mdate': 'Modification Date',
        'filename': 'File Name'
    }

    # Construct the ignored parts string
    ignored_parts = [ignore_options[item] for item in ignore_diff_set]
    ignored_str = ', '.join(ignored_parts) if ignored_parts else 'None'

    # Construct the checked parts string
    all_options = set(ignore_options.keys())
    checked_parts = all_options - ignore_diff_set
    checked_parts_str = ', '.join([ignore_options[item] for item in checked_parts])

    result = f"Ignore: {ignored_str}. Check: File Size, {checked_parts_str}."
    return result


def format_number_with_commas(number):
    return f"{number:,}"


def get_size_constraints_string(min_size=None, max_size=None):
    size_constraints = [
        f"Minimum Size: {min_size:,} bytes" if min_size is not None else None,
        f"Maximum Size: {max_size:,} bytes" if max_size is not None else None
    ]
    size_constraints = [constraint for constraint in size_constraints if constraint]
    return f"{', '.join(size_constraints)}." if size_constraints else "No Size Constraints."


def confirm_script_execution(args):
    # if the script is run from command line, and not by pytest, ask for confirmation
    if not detect_pytest():
        print(f"This script will move duplicate files from {args.src}. No additional confirmation will be asked.")
        print("Do you want to continue? (y/n): ")
        if input().lower() != 'y':
            print("Exiting the script.")
            sys.exit(0)


def detect_pytest():
    return 'PYTEST_CURRENT_TEST' in os.environ


def any_is_subfolder_of(folders: List[str]) -> bool:
    for i in range(len(folders)):
        for j in range(len(folders)):
            if i != j and folders[i].startswith(folders[j]):
                print_error(f"{folders[i]} is a subfolder of {folders[j]}")
                return True
    return False


def parse_size(size_str) -> int:
    """
    Parses a human-readable file size string (e.g., '10MB') and returns the size in bytes.
    """
    units = {"KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3, "B": 1}  # 'B' must be last to avoid matching 'KB'
    size_str = size_str.upper()
    int_value = None
    try:
        for unit in units.keys():
            if size_str.endswith(unit):
                int_value = int(size_str[:-len(unit)]) * units[unit]
                break
        if int_value is None:
            int_value = int(size_str)
    except ValueError:
        raise ValueError("Invalid size format")
    if int_value < 0:
        raise ValueError("Size cannot be negative")
    return int_value


def parse_arguments(cust_args=None):
    parser = argparse.ArgumentParser(
        description="Identify duplicate files between source and target folders, move duplicates to a separate folder.")
    parser.add_argument('--src', '--source', required=True, help='Source folder')
    parser.add_argument('--target',  required=True, help='Target folder')
    parser.add_argument('--move_to', '--to', required=True, type=str, help='Folder where the duplicates '
                                                                           'will be moved.')
    parser.add_argument('--run', action='store_true', help='Run without test mode. Default is test mode.')
    parser.add_argument('--ignore_diff', type=str, help='Comma-separated list of differences to ignore: '
                                                        'mdate, filename, checkall. Default is ignore mdate.',
                        default='mdate')
    parser.add_argument('--copy_to_all', action='store_true',
                        help='Copy file to all folders if found in multiple target folders. Default is move file to the'
                             ' first folder.', default=False)
    parser.add_argument('--whitelist_ext', type=str, help='Comma-separated list of file extensions to '
                        'whitelist (only these will be checked). IN WORK, DONT USE YET')
    parser.add_argument('--blacklist_ext', type=str, help='Comma-separated list of file extensions to '
                        'blacklist (these will not be checked). IN WORK, DONT USE YET')
    parser.add_argument('--min_size', type=str, help='Minimum file size to check. Specify with units '
                        '(B, KB, MB). IN WORK, DONT USE YET', default=None)
    parser.add_argument('--max_size', type=str, help='Maximum file size to check. Specify with units '
                        '(B, KB, MB). IN WORK, DONT USE YET', default=None)
    parser.add_argument('--keep_empty_folders', dest='delete_empty_folders', action='store_false',
                        help='Do not delete empty folders in the source folder. Default is to delete.')
    parser.add_argument('--full_hash', action='store_true', help='Use full file hash for comparison. Default is partial.')
    parser.set_defaults(delete_empty_folders=True)
    parser.add_argument('--clear_cache', action='store_true', help=argparse.SUPPRESS)  # for testing
    parser.add_argument('--extra_logging', action='store_true', help=argparse.SUPPRESS)  # for testing
    args = parser.parse_args(cust_args if cust_args else None)

    any_is_subfolder_of([args.src, args.target, args.move_to])
    if args.extra_logging:
        logger.setLevel(logging.DEBUG)
    args.ignore_diff = set(str(args.ignore_diff).split(','))
    if not args.ignore_diff.issubset({'mdate', 'filename', 'checkall'}):
        parser.error("Invalid ignore_diff setting: must be 'mdate', 'filename' or 'checkall'.")
    if 'checkall' in args.ignore_diff:
        if len(args.ignore_diff) > 1:
            parser.error("Invalid ignore_diff setting: checkall cannot be used with other settings.")
        args.ignore_diff = set()

    # Convert whitelist and blacklist to sets and check for mutual exclusivity
    args.whitelist_ext = set(str(args.whitelist_ext).split(',')) if args.whitelist_ext else None
    args.blacklist_ext = set(str(args.blacklist_ext).split(',')) if args.blacklist_ext else None

    if args.whitelist_ext and args.blacklist_ext:
        parser.error("You cannot specify both --whitelist_ext and --blacklist_ext at the same time.")

    if args.min_size:
        try:
            args.min_size = parse_size(args.min_size)
        except ValueError as e:
            parser.error(f"Invalid value for --min_size: {e}")

    if args.max_size:
        try:
            args.max_size = parse_size(args.max_size)
        except ValueError as e:
            parser.error(f"Invalid value for --max_size: {e}")

    if args.min_size and args.max_size and args.min_size > args.max_size:
        parser.error("Minimum size must be less than maximum size.")

    return args


def print_error(message):
    print(f"Error: {message}")
    logger.critical(f"{message}")
    sys.exit(1)


def output_results(args, deleted_source_folders, duplicate_source_files_moved, files_created, files_moved, hash_manager):
    summary_header = "Summary (Test Mode):" if not args.run else "Summary:"
    separator = "-" * max(len(summary_header), 40)
    cache_hits = f"Hash requests: {hash_manager.persistent_cache_requests + hash_manager.temporary_cache_requests}," + \
                 f" Cache hits: {hash_manager.persistent_cache_hits + hash_manager.temporary_cache_hits}"
    logger.info(summary_header)
    logger.info(separator)

    logger.debug(cache_hits)
    res_str = f'Move: {files_moved} files, Create: {files_created} copies'
    if duplicate_source_files_moved:
        res_str += f", Moved {duplicate_source_files_moved} duplicate files from the source folder"
    if deleted_source_folders:
        res_str += f", Deleted: {deleted_source_folders} empty folders in the source folder"
    logger.info(res_str)


def setup_hash_manager(args):
    hash_manager = HashManager(target_folder=args.target if not detect_pytest() else None, full_hash=args.full_hash)
    if args.clear_cache:
        hash_manager.clear_cache()
        hash_manager.save_data()
    return hash_manager
