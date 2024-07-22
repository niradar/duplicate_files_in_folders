import logging
import sys
from argparse import Namespace

from duplicate_files_in_folders.duplicates_finder import get_csv_file_path
from duplicate_files_in_folders.hash_manager import HashManager
from duplicate_files_in_folders.utils import detect_pytest

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
        config_items["Empty Folders"] = "Do not delete empty folders in Scan folder"

    if args.copy_to_all:
        config_items["Additional Settings"] = "Copy duplicate files to all folders"

    config_items["Script Mode"] = (
        "Create CSV File" if args.action == 'create_csv' else
        "Run Mode" if args.run else
        "Test Mode"
    )

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

    files_left = len(scan_stats) - files_moved - duplicate_scan_files_moved
    # Detailed summary
    summary_lines = {
        'Scan Folder Files': f"{format_number_with_commas(len(scan_stats)) if scan_stats else 'N/A'} files",
        'Reference Folder Files': f"{format_number_with_commas(len(ref_stats)) if ref_stats else 'N/A'} files",
        'Files Moved': f"{format_number_with_commas(files_moved)} files",
        'Files Created': f"{format_number_with_commas(files_created)} copies",
        'Left in Scan Folder': f"{format_number_with_commas(files_left)} files",
    }

    if duplicate_scan_files_moved:
        summary_lines['Duplicate Files Moved'] = \
            f"{duplicate_scan_files_moved} duplicate files from the scan folder"
    if deleted_scan_folders:
        summary_lines['Empty Folders Deleted'] = f"{deleted_scan_folders} empty folders in the scan folder"

    common_output_results(summary_header, summary_lines)


def output_csv_file_creation_results(args: Namespace, combined_duplicates: dict, scan_stats=None, ref_stats=None):
    """ Output the results of the CSV file creation.
    :param args: The parsed arguments
    :param combined_duplicates: The combined duplicates dictionary
    :param scan_stats: Output of get_files_and_stats() for the scan folder
    :param ref_stats: Output of get_files_and_stats() for the reference folder
    """
    summary_header = "CSV File Creation Summary:"

    # Detailed summary
    summary_lines = {
        'CSV File Path': get_csv_file_path(args),
        'Scan Folder Files': f"{format_number_with_commas(len(scan_stats)) if scan_stats else 'N/A'} files",
        'Reference Folder Files': f"{format_number_with_commas(len(ref_stats)) if ref_stats else 'N/A'} files",
        'Total Duplicate Files': len(combined_duplicates),
    }

    common_output_results(summary_header, summary_lines)


def common_output_results(title: str, summary_lines: dict):
    """ Output the common results of the script execution.
    :param title: The title of the summary.
    :param summary_lines: Summary lines to output.
    """
    summary_header = f"{title}:"
    separator = "-" * max(len(summary_header), 40)
    fixed_width = 25

    # Header
    log_and_print("")
    log_and_print(summary_header)
    log_and_print(separator)

    # Detailed summary
    for key, value in summary_lines.items():
        log_and_print(f"{key.ljust(fixed_width)}: {value}")

    # Footer
    log_and_print(separator)
    log_and_print("")


def confirm_script_execution(args: Namespace):
    """ Confirm the script execution if not run by pytest. """
    if not detect_pytest():
        if args.action == 'move_duplicates':
            if not args.run:
                print("This script is currently in test mode. No files will be moved.")
                print(f"In run mode, duplicate files will be moved from {args.scan_dir} to {args.move_to}.")
            else:
                print(f"This script will move duplicate files from {args.scan_dir}. "
                      f"No additional confirmation will be asked.")
        elif args.action == 'create_csv':
            print(f"This script will create a CSV file in {args.move_to}. The folder will be created if it doesn't "
                  f"exist.")

        print("Do you want to continue? (y/n): ")
        # while loop until the user enters 'y' or 'n'
        while True:
            user_input = input().lower()
            if user_input == 'y':
                break
            elif user_input == 'n':
                print("Exiting the script.")
                sys.exit(0)
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
