import logging
import os
import concurrent.futures
from collections import defaultdict
from probables import BloomFilter
from duplicate_files_in_folders.hash_manager import HashManager
from duplicate_files_in_folders.file_manager import FileManager
from typing import Dict, List, Set
from duplicate_files_in_folders.utils import copy_or_move_file, get_file_key

logger = logging.getLogger(__name__)


def get_files_keys(args, file_infos: List[Dict]) -> Dict[str, List[Dict]]:
    """Generate keys for a list of files."""
    results = {}
    for file_info in file_infos:
        file_info_key = get_file_key(args, file_info['path'])
        if file_info_key not in results:
            results[file_info_key] = []
        results[file_info_key].append(file_info)
    return results


def get_files_keys_parallel(args, file_infos: List[Dict]) -> Dict[str, List[Dict]]:
    """Generate keys for a list of files using parallel processing."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(get_file_key, args, file_info['path']): file_info for file_info in file_infos}
        results = {}
        for future in concurrent.futures.as_completed(future_to_file):
            file_info = future_to_file[future]
            try:
                file_info_key = future.result()
                if file_info_key not in results:
                    results[file_info_key] = []
                results[file_info_key].append(file_info)
            except Exception as exc:
                print(f'File {file_info["path"]} generated an exception: {exc}')
                raise exc
        return results


def filter_files_by_args(args, files_stats: List[Dict]) -> List[Dict]:
    """Filter files based on size and extensions criteria."""
    min_size = args.min_size if args.min_size is not None else 0
    max_size = args.max_size if args.max_size is not None else float('inf')
    filtered_files = [file_info for file_info in files_stats
                      if min_size <= int(file_info['size']) <= max_size and
                      (args.whitelist_ext is None or file_info['name'].split('.')[-1] in args.whitelist_ext) and
                      (args.blacklist_ext is None or file_info['name'].split('.')[-1] not in args.blacklist_ext)]
    return filtered_files


def find_potential_duplicates(dir1_stats: List[Dict], dir2_stats: List[Dict], ignore_diff: Set[str]) -> List[Dict]:
    """Identify potential duplicates between two directories."""
    size_bloom = BloomFilter(est_elements=len(dir1_stats), false_positive_rate=0.05)
    name_bloom = BloomFilter(est_elements=len(dir1_stats), false_positive_rate=0.05)
    modified_time_bloom = BloomFilter(est_elements=len(dir1_stats), false_positive_rate=0.05)
    check_name = 'filename' not in ignore_diff
    check_mdate = 'mdate' not in ignore_diff

    for file_info in dir1_stats:
        size_bloom.add(str(file_info['size']))
        if check_name:
            name_bloom.add(file_info['name'])
        if check_mdate:
            modified_time_bloom.add(str(file_info['modified_time']))

    potential_duplicates = []
    for file_info in dir2_stats:
        if (size_bloom.check(str(file_info['size'])) and
                (not check_name or name_bloom.check(file_info['name'])) and
                (not check_mdate or modified_time_bloom.check(str(file_info['modified_time'])))):
            potential_duplicates.append(file_info)

    return potential_duplicates


def process_potential_duplicates(potential_duplicates: List[Dict], combined: Dict, key: str, args,
                                 key_func=get_files_keys_parallel) -> Dict:
    """Process potential duplicates to populate the combined dictionary."""
    parallel_results = key_func(args, potential_duplicates)
    for file_info_key, file_infos in parallel_results.items():
        if key not in combined[file_info_key]:
            combined[file_info_key][key] = []
        for file_info in file_infos:
            combined[file_info_key][key].append(file_info)
    return combined


def find_duplicates_files_v3(args, source: str, target: str) -> (Dict, List[Dict], List[Dict]):
    """
     Find duplicate files between source and target directories.
     Returns a dictionary of duplicates and the file stats for both directories.
    """
    hash_manager = HashManager.get_instance()
    source_stats = filter_files_by_args(args, FileManager.get_files_and_stats(source))
    target_stats = filter_files_by_args(args, FileManager.get_files_and_stats(target))

    potential_source_duplicates = find_potential_duplicates(target_stats, source_stats, args.ignore_diff)
    potential_target_duplicates = find_potential_duplicates(source_stats, target_stats, args.ignore_diff)

    combined = defaultdict(defaultdict)
    combined = process_potential_duplicates(potential_source_duplicates, combined, 'source', args)
    get_keys_function = get_files_keys_parallel \
        if (len(hash_manager.get_hashes_by_folder(target)) > len(target_stats) / 2) else get_files_keys
    combined = process_potential_duplicates(potential_target_duplicates, combined, 'target', args, get_keys_function)

    # Filter out combined items that don't have both source and target - ie size = 2
    combined = {k: v for k, v in combined.items() if len(v) == 2}

    # Sort the lists for both 'source' and 'target' lexicographically by their path
    for value in combined.values():
        value['source'] = sorted(value['source'], key=lambda x: x['path'])
        value['target'] = sorted(value['target'], key=lambda x: x['path'])

    return combined, source_stats, target_stats


def process_duplicates(combined: Dict, args) -> (int, int):
    """Process the duplicates found by find_duplicates_files_v3 and move/copy it."""
    files_created = files_moved = 0

    for file_key, locations in combined.items():
        source_files = locations.get('source', [])
        target_files = locations.get('target', [])

        src_filepath = source_files[0]['path']
        srcs_to_move = [(file['path'], 0) for file in source_files]

        # Copy or move files to target locations
        if not args.copy_to_all:
            copy_or_move_file(target_files[0]['path'], args.move_to, src_filepath, args.target, move=True)
            files_moved += 1
        else:
            num_to_copy = max(0, len(target_files) - len(srcs_to_move))
            for i in range(num_to_copy):
                copy_or_move_file(target_files[i]['path'], args.move_to, src_filepath, args.target, False)
                files_created += 1

            for (src, _), tgt in zip(srcs_to_move, target_files[num_to_copy:]):
                copy_or_move_file(tgt['path'], args.move_to, src, args.target, move=True)
                files_moved += 1

    return files_moved, files_created


def clean_source_duplications(args, combined):
    """
    Clean up the source duplications after moving files to the move_to folder.
    Assuming all existing files in the combined dictionary at 'source' key needs to be moved.
    """
    source_paths = [file_info['path'] for key, locations in combined.items() if 'source' in locations for file_info in
                    locations['source'] if os.path.exists(file_info['path'])]
    source_dups_move_to: str = str(os.path.join(args.move_to, os.path.basename(args.src) + "_dups"))
    for src_path in source_paths:
        copy_or_move_file(src_path, source_dups_move_to, src_path, args.src, move=True)
    return len(source_paths)
