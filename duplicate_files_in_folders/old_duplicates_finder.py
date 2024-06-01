import logging
import os
from collections import defaultdict
from typing import Dict, List, Tuple

import tqdm

from duplicate_files_in_folders.file_manager import FileManager
from duplicate_files_in_folders.hash_manager import HashManager
from duplicate_files_in_folders.utils import check_and_update_filename, copy_or_move_file, get_file_key

logger = logging.getLogger(__name__)


def compare_files(src_filepath, tgt_filepath, ignore_diffs):
    ignore_diffs = ignore_diffs if ignore_diffs else set('mdate')
    if 'filename' not in ignore_diffs and src_filepath[src_filepath.rfind(os.sep) + 1:] != tgt_filepath[tgt_filepath.rfind(os.sep) + 1:]:
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
        fm = FileManager.get_instance()
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
        target_key = get_file_hash(src_filepath) if 'filename' in args.ignore_diff else src_filepath[src_filepath.rfind(os.sep) + 1:]
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

    return files_moved, files_created, unique_source_duplicate_files_found, duplicate_source_files_moved


def move_to_target_paths(args, src_filepath, target_paths_to_copy, source_duplicates, files_created, files_moved):
    # future improvement: smarter move - we might have same folder structure between copies in source and target
    if not source_duplicates:  # If source_duplicates is empty, use src_filepath for copying and moving
        source_duplicates = [(src_filepath, 0)]
    source_duplicates.sort(key=lambda x: x[0], reverse=True)  # sort by path name reverse for easier testing

    if not args.copy_to_all:
        copy_or_move_file(target_paths_to_copy[0], args.move_to, src_filepath, args.target)
        return files_created, files_moved + 1

    num_to_copy = max(0, len(target_paths_to_copy) - len(source_duplicates))
    if num_to_copy:  # Copy first source to make up for fewer source duplicates
        for i in range(num_to_copy):
            copy_or_move_file(target_paths_to_copy[i], args.move_to, src_filepath, args.target, False)
            files_created += 1

    # Move each source duplicate to the corresponding target path
    for (src, _), tgt in zip(source_duplicates, target_paths_to_copy[num_to_copy:]):
        copy_or_move_file(tgt, args.move_to, src, args.target, move=True)
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


def get_file_hash(file_path: str) -> str:
    """Retrieve the hash of the given file."""
    hash_manager = HashManager.get_instance()
    return hash_manager.get_hash(file_path)
