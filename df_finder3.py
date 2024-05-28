# Identifies and processes duplicate files between a source and target directory.
# https://github.com/niradar/duplicate_files_in_folders

import os
import sys
from collections import defaultdict
import argparse
import time
import logging
import tqdm
import file_manager
from hash_manager import HashManager
from logging_config import setup_logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def get_file_hash(file_path) -> str:
    hash_manager = HashManager.get_instance()
    return hash_manager.get_hash(file_path)


def print_error(message):
    print(f"Error: {message}")
    logger.critical(f"{message}")
    sys.exit(1)


def validate_folder(folder, name):
    """ Validate if a folder exists and is not empty. """
    if not os.path.isdir(folder) or not os.path.exists(folder):
        print_error(f"{name} folder does not exist.")
    if not os.listdir(folder):
        print_error(f"{name} folder is empty.")
    return True


def check_and_update_filename(new_filename):
    if os.path.exists(new_filename):
        original_filename = new_filename
        timestamp = int(time.time())  # Get current Unix timestamp
        base, ext = os.path.splitext(new_filename)
        new_filename = f"{base}_{timestamp}{ext}"  # Append timestamp to the filename
        logger.info(f"Renaming of {original_filename} to {new_filename} is needed to avoid overwrite.")
    return new_filename


def copy_or_move_file(tgt_filepath: str, move_to: str, src_filepath: str, target: str, test_mode, move=True):
    new_src_path = os.path.join(move_to, os.path.relpath(tgt_filepath, target))
    new_src_dir = os.path.dirname(new_src_path)
    fm = file_manager.FileManager(not test_mode)
    if not os.path.exists(new_src_dir):
        fm.make_dirs(new_src_dir)
    new_filename = check_and_update_filename(new_src_path)
    if move:
        fm.move_file(src_filepath, new_filename)
    else:
        fm.copy_file(src_filepath, new_filename)
    return new_filename


def compare_files(src_filepath, tgt_filepath, ignore_diffs):
    ignore_diffs = ignore_diffs if ignore_diffs else set('mdate')
    if 'filename' not in ignore_diffs and os.path.basename(src_filepath) != os.path.basename(tgt_filepath):
        return False
    if 'mdate' not in ignore_diffs and not os.path.getmtime(src_filepath) == os.path.getmtime(tgt_filepath):
        return False
    if os.path.getsize(src_filepath) != os.path.getsize(tgt_filepath):
        return False
    return get_file_hash(src_filepath) == get_file_hash(tgt_filepath)


def clean_source_duplications(args, keys_to_clean=None, given_duplicates: Dict[str, List[Tuple[str, int]]] = None):
    """
    Clean the source folder from duplicate files. Move the duplicates to a new folder under the move_to folder.
    :param given_duplicates: if not None, use this dictionary of duplicates instead of finding them again.
    :param args:
    :param keys_to_clean: List of key to clean. If None, clean all duplicates but the first one from each group. \
    If not None, clean only the duplicates with the hashes in the list but clean all the duplicates from the group.

    :return:
    """
    source_duplicates = given_duplicates if given_duplicates else {
        src_key: src_filepaths for src_key, src_filepaths in collect_source_files(args).items()
        if len(src_filepaths) > 1
    }
    source: str = args.src
    source_dups_move_to = os.path.join(args.move_to, os.path.basename(source) + "_dups")
    unique_duplicate_files_found = duplicate_files_moved = 0

    for group_key, group in source_duplicates.items():
        if keys_to_clean and group_key not in keys_to_clean:
            continue
        logger.debug(f"Found {len(group)} duplicate files for {group[0][0]}")

        # Sort the files by their depth, then by their modification time or name
        group.sort(key=lambda x: (x[1], x[0] if 'mdate' in args.ignore_diff else os.path.getmtime(x[0])))

        unique_duplicate_files_found += 1
        start_index = 1 if not keys_to_clean else 0
        fm = file_manager.FileManager(args.run)
        # Move all the other files to a new folder under the move_to folder
        for src_filepath, _ in group[start_index:]:
            new_src_path = os.path.join(source_dups_move_to, os.path.relpath(src_filepath, source))
            new_src_dir = os.path.dirname(new_src_path)
            if not os.path.exists(new_src_dir):
                fm.make_dirs(new_src_dir)
            new_filename = check_and_update_filename(new_src_path)
            fm.move_file(src_filepath, new_filename)
            duplicate_files_moved += 1

    if unique_duplicate_files_found:
        logger.info(
            f"Cleaning source folder: Found {unique_duplicate_files_found} unique duplicate files in the source folder,"
            f" moved {duplicate_files_moved} files to {source_dups_move_to}")
    return unique_duplicate_files_found, duplicate_files_moved


def find_and_process_duplicates(args):
    source_files = collect_source_files(args)
    total_source_files = sum(len(paths) for paths in source_files.values())
    logger.info(f"Source folder: Found {total_source_files} files ({len(source_files)} unique files) in {args.src}")

    target_files = collect_target_files(args)  # key is hash or filename, value is list of file paths
    total_files = sum(len(paths) for paths in target_files.values())
    key_type = "filenames" if 'filename' not in args.ignore_diff else "hashes"
    logger.info(f"Found {total_files} files ({len(target_files)} unique {key_type}) in {args.target}")

    # Store the source duplicates before processing
    source_duplicates: Dict[str, List[Tuple[str, int]]] = \
        {src_key: src_filepaths for src_key, src_filepaths in source_files.items() if len(src_filepaths) > 1}

    files_moved = files_created = 0
    source_duplicates_to_process = {}

    for src_key, src_filepaths in tqdm.tqdm(source_files.items(), desc="Finding duplicate files"):
        src_filepath, _ = src_filepaths[0]
        target_key = get_file_hash(src_filepath) if 'filename' in args.ignore_diff else os.path.basename(src_filepath)
        if target_key not in target_files:  # if the file is not found in the target folder, no need to process it
            continue
        target_paths = target_files[target_key]  # all possible target paths for the source file
        target_paths_to_copy = []
        try:
            for tgt_filepath in target_paths:
                if compare_files(src_filepath, tgt_filepath, args.ignore_diff):
                    target_paths_to_copy.append(tgt_filepath)
            if target_paths_to_copy:
                srcs_to_move = source_duplicates[src_key].copy() if src_key in source_duplicates else []
                files_created, files_moved = move_to_target_paths(args, src_filepath, target_paths_to_copy,
                                                                  srcs_to_move, files_created, files_moved)
                filtered_group = [(src_path, depth) for src_path, depth in srcs_to_move if os.path.exists(src_path)]
                if filtered_group:
                    source_duplicates_to_process[src_key] = filtered_group
        except Exception as e:
            logger.exception(f"Error handling {src_filepath}: {e}")
            raise

    # clean source duplicates of files moved to the move_to folder
    unique_source_duplicate_files_found, duplicate_source_files_moved = (
        clean_source_duplications(args, source_duplicates_to_process.keys(), source_duplicates_to_process)) \
        if source_duplicates_to_process else (0, 0)

    deleted_source_folders = delete_empty_folders_in_tree(args.src, args.run) if args.run and args.delete_empty_folders else 0
    return files_moved, files_created, deleted_source_folders, unique_source_duplicate_files_found, duplicate_source_files_moved


def move_to_target_paths(args, src_filepath, target_paths_to_copy, source_duplicates, files_created, files_moved):
    # future improvement: smarter move - we might have same folder structure between copies in source and target
    if not source_duplicates:  # If source_duplicates is empty, use src_filepath for copying and moving
        source_duplicates = [(src_filepath, 0)]
    source_duplicates.sort(key=lambda x: x[0], reverse=True)  # sort by path name reverse for easier testing

    if not args.copy_to_all:
        copy_or_move_file(target_paths_to_copy[0], args.move_to, src_filepath, args.target, not args.run)
        return files_created, files_moved + 1

    num_to_copy = max(0, len(target_paths_to_copy) - len(source_duplicates))
    if num_to_copy:  # Copy first source to make up for fewer source duplicates
        for i in range(num_to_copy):
            copy_or_move_file(target_paths_to_copy[i], args.move_to, src_filepath, args.target, not args.run, False)
            files_created += 1

    # Move each source duplicate to the corresponding target path
    for (src, _), tgt in zip(source_duplicates, target_paths_to_copy[num_to_copy:]):
        copy_or_move_file(tgt, args.move_to, src, args.target, not args.run, move=True)
        files_moved += 1

    return files_created, files_moved


def collect_target_files(args):
    target_files = defaultdict(list)
    # list so it won't be lazy
    walk = list(os.walk(args.target))
    for root, dirs, files in tqdm.tqdm(walk, desc="Scanning target folders"):
        for f in files:
            full_path = os.path.join(root, f)
            key = f if 'filename' not in args.ignore_diff else get_file_hash(full_path)
            target_files[key].append(full_path)
    if args.extra_logging:
        for key, paths in target_files.items():
            logger.debug(f"{key}: {paths}")
    return target_files


def delete_empty_folders_in_tree(base_path, run_mode):
    folders_by_depth = {}  # collect all folders in the source folder by depth
    for root, dirs, files in os.walk(base_path, topdown=False):
        if base_path == root:
            continue
        depth = root.count(os.sep) - base_path.count(os.sep)
        if depth not in folders_by_depth:
            folders_by_depth[depth] = []
        folders_by_depth[depth].append(root)

    fm = file_manager.FileManager(run_mode)
    deleted_folders = 0
    # delete empty folders starting from the deepest level excluding the base_path folder
    for depth in sorted(folders_by_depth.keys(), reverse=True):
        for folder in folders_by_depth[depth]:
            if not os.listdir(folder):
                fm.rmdir(folder)
                deleted_folders += 1
    return deleted_folders


def get_file_key(args, file_path) -> str:
    hash_key: str = get_file_hash(file_path)
    file_key: str = os.path.basename(file_path) if 'filename' not in args.ignore_diff else None
    mdate_key: str = str(os.path.getmtime(file_path)) if 'mdate' not in args.ignore_diff else None
    return '_'.join(filter(None, [hash_key, file_key, mdate_key]))


def collect_source_files(args) -> Dict[str, List[Tuple[str, int]]]:
    source_files = defaultdict(list)
    source_depth = args.src.count(os.sep)
    walk = list(os.walk(args.src))
    for root, dirs, files in tqdm.tqdm(walk, desc="Scanning source folders"):
        for f in files:
            full_path = os.path.join(root, f)
            if os.path.isfile(full_path):
                depth = full_path.count(os.sep) - source_depth
                source_files[get_file_key(args, full_path)].append((full_path, depth))
    return source_files


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
    parser.add_argument('--delete_empty_folders', dest='delete_empty_folders', action='store_true',
                        help='Delete empty folders in the source folder. Default is enabled.')
    parser.add_argument('--no-delete_empty_folders', dest='delete_empty_folders', action='store_false',
                        help='Do not delete empty folders in the source folder.')
    parser.set_defaults(delete_empty_folders=True)
    parser.add_argument('--clear_cache', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--extra_logging', action='store_true', help=argparse.SUPPRESS)  # for testing
    args = parser.parse_args(cust_args if cust_args else None)

    if args.extra_logging:
        logger.setLevel(logging.DEBUG)
    args.ignore_diff = set(str(args.ignore_diff).split(','))
    if not args.ignore_diff.issubset({'mdate', 'filename', 'checkall'}):
        print_error("Invalid ignore_diff setting: must be 'mdate', 'filename' or 'checkall'.")
    if 'checkall' in args.ignore_diff:
        if len(args.ignore_diff) > 1:
            print_error("Invalid ignore_diff setting: checkall cannot be used with other settings.")
        args.ignore_diff = set()

    return args


def validate_duplicate_files_destination(duplicate_files_destination, run_mode):
    fm = file_manager.FileManager(run_mode)
    if not os.path.isdir(duplicate_files_destination):
        try:
            fm.make_dirs(duplicate_files_destination)
        except Exception as e:
            print_error(f"Error creating destination folder {duplicate_files_destination}: {e}")
    return True


def any_is_subfolder_of(folders: List[str]) -> bool:
    for i in range(len(folders)):
        for j in range(len(folders)):
            if i != j and folders[i].startswith(folders[j]):
                print_error(f"{folders[i]} is a subfolder of {folders[j]}")
                return True
    return False


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


def main(args):
    setup_logging()
    file_manager.FileManager.reset_file_manager([args.target], [args.src, args.move_to], args.run)
    validate_folder(args.src, "Source")
    validate_folder(args.target, "Target")
    validate_duplicate_files_destination(args.move_to, args.run)
    any_is_subfolder_of([args.src, args.target, args.move_to])
    confirm_script_execution(args)
    logger.info(f"Source folder: {args.src}")
    logger.info(f"Target folder: {args.target}")
    logger.info(f"Move to folder: {args.move_to}")
    logger.info(f"Ignoring Settings: mdate={'mdate' in args.ignore_diff}, filename={'filename' in args.ignore_diff}")
    hash_manager = HashManager(target_folder=args.target if not detect_pytest() else None)
    if args.clear_cache:
        hash_manager.clear_cache()
    (files_moved, files_created, deleted_source_folders, unique_source_duplicate_files_found,
     duplicate_source_files_moved) = find_and_process_duplicates(args)
    hash_manager.save_data()
    output_results(args, deleted_source_folders, duplicate_source_files_moved, files_created, files_moved, hash_manager)


if __name__ == "__main__":
    if os.name != 'nt':
        print_error("This script was tested only on Windows. Modify and test it on other OS if needed.")
    command_line_args = parse_arguments()
    main(command_line_args)
