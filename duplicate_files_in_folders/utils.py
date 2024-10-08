import argparse
import logging
import os
import time
from argparse import Namespace

from duplicate_files_in_folders.file_manager import FileManager
from duplicate_files_in_folders.hash_manager import HashManager

logger = logging.getLogger(__name__)


def detect_pytest():
    """ Detect if the script is run by pytest.
    :return: True if the script is run by pytest, False otherwise"""
    return 'PYTEST_CURRENT_TEST' in os.environ


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


def initialize_arguments():
    """
    Initialize and return the argument parser.
    :return: the argument parser
    """
    parser = argparse.ArgumentParser(
        description="Identify duplicate files between scan and reference folders, "
                    "move duplicates from scan folder to a separate folder.")
    parser.add_argument('--run', action='store_true', help='Run without test mode. Default is test mode.')
    parser.add_argument('--ignore_diff', type=str, help='Comma-separated list of differences to ignore: '
                                                        'mdate, filename, none. Default is ignore mdate.',
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
    parser.add_argument('--keep_structure', action='store_true',
                        help='Keep the original scan folder structure in the destination folder.')
    parser.set_defaults(delete_empty_folders=True)
    parser.add_argument('--clear_cache', action='store_true', help=argparse.SUPPRESS)  # for testing
    parser.add_argument('--extra_logging', action='store_true', help=argparse.SUPPRESS)  # for testing

    parser.add_argument('--action', type=str, choices=['move_duplicates', 'create_csv'],
                        help='Action to perform: move_duplicates, create_csv', default='move_duplicates')

    parser.add_argument('--scan_dir', '--scan', '--s', dest='scan_dir', required=True,
                        help='Path - folder to scan for duplicates.')
    parser.add_argument('--reference_dir', '--reference', '--r', required=True,
                        help='Path - folder to compare with scan_dir.')
    parser.add_argument('--move_to', '--to', required=True, type=str,
                        help='Path - duplicate files from scan_dir will be moved to this folder.')
    return parser


def validate_arguments(args, parser, check_folders=True):
    """
    Validate the parsed command line arguments.
    :param args: the parsed arguments
    :param parser: the argument parser
    :param check_folders: for testing - if False, skip folder validation
    """
    # Validate the folders given in the arguments
    if check_folders:
        folders = [(args.scan_dir, "Scan Folder"), (args.reference_dir, "Reference Folder")]
        for folder, name in folders:
            if not os.path.exists(folder) or not os.path.isdir(folder):
                parser.error(f"{name} folder does not exist.")
            if not os.listdir(folder):
                parser.error(f"{name} folder is empty.")

    is_subfolder, relationships = FileManager.any_is_subfolder_of([args.scan_dir, args.reference_dir, args.move_to])
    if is_subfolder:
        for subfolder, parent in relationships:
            if subfolder != parent:
                parser.error(f"{subfolder} is a subfolder of {parent}")
            else:
                parser.error(f"Several arguments are the same folder: {subfolder}")

    # for testing, barely used
    if args.extra_logging:
        logger.setLevel(logging.DEBUG)

    # Validate the ignore_diff setting
    args.ignore_diff = set(str(args.ignore_diff).split(','))
    if not args.ignore_diff.issubset({'mdate', 'filename', 'none'}):
        parser.error("Invalid ignore_diff setting: must be 'mdate', 'filename' or 'none'.")
    if 'none' in args.ignore_diff:
        if len(args.ignore_diff) > 1:
            parser.error("Invalid ignore_diff setting: none cannot be used with other settings.")
        args.ignore_diff = set()

    # Convert whitelist and blacklist to sets and check for mutual exclusivity
    args.whitelist_ext = set(str(args.whitelist_ext).split(',')) if args.whitelist_ext else None
    args.blacklist_ext = set(str(args.blacklist_ext).split(',')) if args.blacklist_ext else None
    if args.whitelist_ext and args.blacklist_ext:
        parser.error("You cannot specify both --whitelist_ext and --blacklist_ext at the same time.")

    # Validate the size constraints
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


def parse_arguments(cust_args=None, check_folders=True):
    """
    Parse and validate command line arguments.
    :param cust_args: if not None, use these arguments instead of command line arguments
    :param check_folders: for testing - if False, skip folder validation
    :return: the parsed and validated arguments
    """
    parser = initialize_arguments()
    args = parser.parse_args(cust_args if cust_args else None)
    validate_arguments(args, parser, check_folders)
    return args


def copy_or_move_file(scan_file_path: str, destination_base_path: str, ref_file_path: str, base_ref_path: str,
                      move: bool = True, keep_structure: bool = False, scan_base_path: str = None) -> str:
    """
    Copy or move a file from the scan directory to the destination directory based on the reference file path.
    :param scan_base_path: The base path of the scan directory. Required if keep_structure is True.
    :param scan_file_path: Full path of the file we want to copy/move
    :param ref_file_path: The full path to the reference file within the base reference directory.
                          This path is used to determine the relative path for the destination.
    :param destination_base_path: The base path where the file should be copied or moved to.
    :param base_ref_path: The base directory path of the reference files.
                          This is used to calculate the relative path of the ref_file_path.
    :param move: True to move the file, False to copy it
    :param keep_structure: True to keep the original scan folder structure in the destination folder, False otherwise
    :return: the final destination path
    """
    if keep_structure:
        if scan_base_path is None:
            raise ValueError("scan_base_path must be provided if keep_structure is True.")
        sub_path = os.path.relpath(scan_file_path, scan_base_path)
        destination_path = os.path.join(destination_base_path, sub_path)
    else:
        destination_path = os.path.join(destination_base_path, os.path.relpath(ref_file_path, base_ref_path))
    logger.debug(f"Copying {scan_file_path} to {destination_path}")
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


def default_renaming_function(original_filename: str) -> str:
    """
    Default renaming function that appends the current timestamp to the filename.
    :param original_filename: the original filename
    :return: the new filename with the timestamp appended
    """
    return f"{os.path.splitext(original_filename)[0]}_{int(time.time())}{os.path.splitext(original_filename)[1]}"


def check_and_update_filename(original_filename: str, renaming_function=None) -> str:
    """
    Check if the filename already exists and rename it to avoid overwriting.
    :param original_filename: the original filename
    :param renaming_function: function that receives the original filename and returns the new filename
    :return: the new filename if the original filename exists, otherwise the original filename
    """
    if renaming_function is None:
        renaming_function = default_renaming_function

    new_filename = original_filename
    if os.path.exists(original_filename):
        new_filename = renaming_function(original_filename)
        logger.info(f"Renaming of {original_filename} to {new_filename} is needed to avoid overwrite.")
    return new_filename


def get_file_key(args: Namespace, file_path: str) -> str:
    """
    Generate a unique key for the file based on hash, filename, and modified date. Ignores components based on args.
    Example: 'hash_key_filename_mdate' or 'hash_key_mdate' or 'hash_key_filename' or 'hash_key'
    :param args: the parsed arguments
    :param file_path: the full path of the file
    :return: the unique key for the file
    """
    hash_key: str = HashManager.get_instance().get_hash(file_path)
    file_key: str = file_path[file_path.rfind(os.sep) + 1:] if 'filename' not in args.ignore_diff else None
    mdate_key: str = str(os.path.getmtime(file_path)) if 'mdate' not in args.ignore_diff else None
    return '_'.join(filter(None, [hash_key, file_key, mdate_key]))
