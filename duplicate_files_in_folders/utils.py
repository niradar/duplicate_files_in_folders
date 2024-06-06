import argparse
import logging
import os
import sys
import time
from typing import List
from argparse import Namespace

from duplicate_files_in_folders.file_manager import FileManager
from duplicate_files_in_folders.hash_manager import HashManager

logger = logging.getLogger(__name__)


def log_and_print(message: str):
    """ Log and print a message. """
    print(message)
    logger.info(message)


def display_initial_config(args: Namespace):
    """ Display the initial configuration of the script. """
    header = "=== Script Configuration ==="
    separator = "-" * 50
    blank_line = ""
    fixed_width = 25

    config_items = {
        "Scan Folder": args.scan_dir,
        "Reference Folder": args.reference_dir,
        "\"Move to\" Folder": args.move_to,
        "Ignoring Settings": get_ignore_diff_string(args.ignore_diff),
        "Files Content": "Full Content Check (Slower)" if args.full_hash else "Partial Content Check (Faster)",
        "Size Constraints": get_size_constraints_string(min_size=args.min_size, max_size=args.max_size),
    }
    # args.whitelist_ext is a set
    if args.whitelist_ext:
        config_items["File Types (Whitelist)"] = ', '.join(args.whitelist_ext)
    elif args.blacklist_ext:
        config_items["File Types (Blacklist)"] = ', '.join(args.blacklist_ext)

    if not args.delete_empty_folders:
        config_items["Empty Folders"] = "Do Not Delete Empty Folders in Scan Folder"

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


def get_ignore_diff_string(ignore_diff_set: set[str]) -> str:
    """ Get the ignore_diff human-readable string. """
    ignore_options = {
        'size': 'File Size',
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

    result = f"Ignore: {ignored_str}. Check: {checked_parts_str}."
    return result


def format_number_with_commas(number: int) -> str:
    """ Format a number with commas. """
    return f"{number:,}"


def get_size_constraints_string(min_size=None, max_size=None) -> str:
    """ Get the size constraints string."""
    size_constraints = [
        f"Minimum Size: {min_size:,} bytes" if min_size is not None else None,
        f"Maximum Size: {max_size:,} bytes" if max_size is not None else None
    ]
    size_constraints = [constraint for constraint in size_constraints if constraint]
    return f"{', '.join(size_constraints)}." if size_constraints else "No Size Constraints"


def confirm_script_execution(args: Namespace):
    """ Confirm the script execution if not run by pytest. """
    if not detect_pytest():
        print(f"This script will move duplicate files from {args.scan_dir}. No additional confirmation will be asked.")
        print("Do you want to continue? (y/n): ")
        if input().lower() != 'y':
            print("Exiting the script.")
            sys.exit(0)


def detect_pytest():
    """ Detect if the script is run by pytest. """
    return 'PYTEST_CURRENT_TEST' in os.environ


def any_is_subfolder_of(folders: List[str]) -> bool:
    """
    Check if any folder is a subfolder of another folder.
    :param folders: list of folder paths
    :return: False if no folder is a subfolder of another folder, otherwise exit the script
    """
    for i in range(len(folders)):
        for j in range(len(folders)):
            if i != j and folders[i].startswith(folders[j]):
                logger.error(f"{folders[i]} is a subfolder of {folders[j]}")
                sys.exit(1)
    return False


def parse_size(size_str: str | int) -> int:
    """
    Parse a size string with units (B, KB, MB) to an integer size in bytes.
    :param size_str: the size string (or integer)
    :return: the size in bytes
    :raises ValueError: if the size string is invalid or negative
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


def parse_arguments(cust_args=None, check_folders=True):
    """
    Parse command line arguments and validate them.
    :param cust_args: if not None, use these arguments instead of command line arguments
    :param check_folders: for testing - if False, skip folder validation
    :return: the parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Identify duplicate files between scan and reference folders, "
                    "move duplicates from scan folder to a separate folder.")
    parser.add_argument('--scan_dir', '--scan', '--s', dest='scan_dir', required=True,
                        help='Path - folder to scan for duplicates.')
    parser.add_argument('--reference_dir', '--reference', '--r', required=True,
                        help='Path - folder to compare with scan_dir.')
    parser.add_argument('--move_to', '--to', required=True, type=str,
                        help='Path - duplicate files from scan_dir will be moved to this folder.')
    parser.add_argument('--run', action='store_true', help='Run without test mode. Default is test mode.')
    parser.add_argument('--ignore_diff', type=str, help='Comma-separated list of differences to ignore: '
                                                        'mdate, filename, checkall. Default is ignore mdate.',
                        default='mdate')
    parser.add_argument('--copy_to_all', action='store_true',
                        help='Copy file to all folders if found in multiple ref folders. Default is move file to the'
                             ' first folder.', default=False)
    parser.add_argument('--whitelist_ext', type=str, help='Comma-separated list of file extensions to '
                        'whitelist (only these will be checked).')
    parser.add_argument('--blacklist_ext', type=str, help='Comma-separated list of file extensions to '
                        'blacklist (these will not be checked).')
    parser.add_argument('--min_size', type=str, help='Minimum file size to check. Specify with units '
                        '(B, KB, MB).', default=None)
    parser.add_argument('--max_size', type=str, help='Maximum file size to check. Specify with units '
                        '(B, KB, MB).', default=None)
    parser.add_argument('--keep_empty_folders', dest='delete_empty_folders', action='store_false',
                        help='Do not delete empty folders in the scan_dir folder. Default is to delete.')
    parser.add_argument('--full_hash', action='store_true',
                        help='Use full file hash for comparison. Default is partial.')
    parser.set_defaults(delete_empty_folders=True)
    parser.add_argument('--clear_cache', action='store_true', help=argparse.SUPPRESS)  # for testing
    parser.add_argument('--extra_logging', action='store_true', help=argparse.SUPPRESS)  # for testing
    parser.add_argument('--old_script', action='store_true', help=argparse.SUPPRESS)  # for testing
    args = parser.parse_args(cust_args if cust_args else None)

    if check_folders:
        folders = [(args.scan_dir, "Scan Folder"), (args.reference_dir, "Reference Folder")]
        for folder, name in folders:
            if not os.path.exists(folder) or not os.path.isdir(folder):
                parser.error(f"{name} folder does not exist.")
            if not os.listdir(folder):
                parser.error(f"{name} folder is empty.")

    any_is_subfolder_of([args.scan_dir, args.reference_dir, args.move_to])

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


def output_results(args: Namespace, files_moved: int, files_created: int, deleted_scan_folders: int,
                   duplicate_scan_files_moved: int, scan_stats=None, ref_stats=None):
    """
    Output the results of the script execution.
    :param args: The parsed arguments
    :param files_moved: Number of files moved
    :param files_created: Number of files created
    :param deleted_scan_folders: Number of empty folders deleted
    :param duplicate_scan_files_moved: Number of duplicate files moved from the scan folder
    :param scan_stats: Output of get_files_and_stats() for the scan folder
    :param ref_stats: Output of get_files_and_stats() for the reference folder
    :return: None
    """
    summary_header = "Summary (Test Mode):" if not args.run else "Summary:"
    separator = "-" * max(len(summary_header), 40)
    fixed_width = 25

    # Header
    log_and_print("")
    log_and_print(summary_header)
    log_and_print(separator)
    hash_manager = HashManager.get_instance()
    # Cache hits information
    cache_hits = f"Hash requests: {hash_manager.persistent_cache_requests + hash_manager.temporary_cache_requests}, " \
                 f"Cache hits: {hash_manager.persistent_cache_hits + hash_manager.temporary_cache_hits}"
    logger.debug(cache_hits)

    # Detailed summary
    summary_lines = {
        'Scan Folder Files': f"{format_number_with_commas(len(scan_stats)) if scan_stats else 'N/A'} files",
        'Reference Folder Files': f"{format_number_with_commas(len(ref_stats)) if ref_stats else 'N/A'} files",
        'Files Moved': f"{format_number_with_commas(files_moved)} files",
        'Files Created': f"{format_number_with_commas(files_created)} copies",
    }

    if duplicate_scan_files_moved:
        summary_lines['Duplicate Files Moved'] = \
            f"{duplicate_scan_files_moved} duplicate files from the scan folder"
    if deleted_scan_folders:
        summary_lines['Empty Folders Deleted'] = f"{deleted_scan_folders} empty folders in the scan folder"

    for key, value in summary_lines.items():
        log_and_print(f"{key.ljust(fixed_width)}: {value}")

    # Footer
    log_and_print(separator)
    log_and_print("")


def setup_hash_manager(args: Namespace):
    """
    Setup the hash manager with the reference directory and full hash setting from the arguments.
    :param args: the parsed arguments
    :return: the hash manager instance
    """
    hash_manager = HashManager(reference_dir=args.reference_dir if not detect_pytest() else None,
                               full_hash=args.full_hash)
    if args.clear_cache:
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


def copy_or_move_file(ref_file_path: str, destination_base_path: str, scan_file_path: str, base_ref_path: str,
                      move: bool = True) -> str:
    """
    Copy or move a file from the source to the reference directory.
    :param ref_file_path:
    :param destination_base_path:
    :param scan_file_path:
    :param base_ref_path:
    :param move: True to move the file, False to copy it
    :return: the final destination path
    """
    destination_path = os.path.join(destination_base_path, os.path.relpath(ref_file_path, base_ref_path))
    destination_dir = os.path.dirname(destination_path)
    file_manager = FileManager.get_instance()
    if not os.path.exists(destination_dir):
        file_manager.make_dirs(destination_dir)
    final_destination_path = check_and_update_filename(destination_path)
    if move:
        file_manager.move_file(scan_file_path, final_destination_path)
    else:
        file_manager.copy_file(scan_file_path, final_destination_path)
    return final_destination_path


def check_and_update_filename(original_filename: str) -> str:
    """
    Check if the filename already exists and rename it to avoid overwriting.
    :param original_filename:
    :return:
    """
    new_filename = original_filename
    if os.path.exists(original_filename):
        timestamp = int(time.time())  # Get current Unix timestamp
        base, ext = os.path.splitext(original_filename)
        new_filename = f"{base}_{timestamp}{ext}"  # Append timestamp to the filename
        logger.info(f"Renaming of {original_filename} to {new_filename} is needed to avoid overwrite.")
    return new_filename


def get_file_key(args: Namespace, file_path: str) -> str:
    """
    Generate a unique key for the file based on hash, filename, and modified date. Ignores components based on args.
    Example: 'hash_key_filename_mdate' or 'hash_key_mdate' or 'hash_key_filename' or 'hash_key'
    """
    hash_key: str = HashManager.get_instance().get_hash(file_path)
    file_key: str = file_path[file_path.rfind(os.sep) + 1:] if 'filename' not in args.ignore_diff else None
    mdate_key: str = str(os.path.getmtime(file_path)) if 'mdate' not in args.ignore_diff else None
    return '_'.join(filter(None, [hash_key, file_key, mdate_key]))
