import csv
import os
import concurrent.futures
from datetime import datetime

import tqdm
from probables import BloomFilter
from duplicate_files_in_folders.hash_manager import HashManager
from duplicate_files_in_folders.file_manager import FileManager
from typing import Dict, List, Set
from duplicate_files_in_folders.utils import copy_or_move_file, get_file_key
from argparse import Namespace


def get_files_keys(args: Namespace, file_infos: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Generate keys for a list of files.
    :param args: Parsed arguments
    :param file_infos: List of file stats to generate keys for
    :return: Dictionary of file keys to file stats - each key maps to a list of file stats
    """
    results = {}
    for file_info in file_infos:
        file_info_key = get_file_key(args, file_info['path'])
        if file_info_key not in results:
            results[file_info_key] = []
        results[file_info_key].append(file_info)
    return results


def get_files_keys_parallel(args: Namespace, file_infos: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Generate keys for a list of files using threads.
    :param args: Parsed arguments
    :param file_infos: List of file stats to generate keys for
    :return: Dictionary of file keys to file stats - each key maps to a list of file stats
    """
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


def filter_files_by_args(args: Namespace, files_stats: List[Dict]) -> List[Dict]:
    """
    Filter files based on size and extensions criteria.
    :param args: Parsed arguments
    :param files_stats: List of file stats to filter (the output of FileManager.get_files_and_stats())
    :return: Filtered list of file stats based on the arguments
    """
    min_size = args.min_size if args.min_size is not None else 0
    max_size = args.max_size if args.max_size is not None else float('inf')
    filtered_files = [file_info for file_info in files_stats
                      if min_size <= int(file_info['size']) <= max_size and
                      (args.whitelist_ext is None or file_info['name'].split('.')[-1] in args.whitelist_ext) and
                      (args.blacklist_ext is None or file_info['name'].split('.')[-1] not in args.blacklist_ext)]
    return filtered_files


def find_potential_duplicates(dir1_stats: List[Dict], dir2_stats: List[Dict], ignore_diff: Set[str]) -> List[Dict]:
    """
    Find potential duplicates between two directories based on file size, name, and modified time.
    :param dir1_stats: file stats for the first directory
    :param dir2_stats: file stats for the second directory
    :param ignore_diff: set of differences to ignore when comparing files
    :return: List of potential duplicates, where each element is a dictionary of file stats
    """
    size_bloom = BloomFilter(est_elements=len(dir1_stats), false_positive_rate=0.05)
    name_bloom = BloomFilter(est_elements=len(dir1_stats), false_positive_rate=0.05)
    modified_time_bloom = BloomFilter(est_elements=len(dir1_stats), false_positive_rate=0.05)
    check_name = 'filename' not in ignore_diff
    check_mdate = 'mdate' not in ignore_diff
    check_size = 'size' not in ignore_diff  # for now, size is always checked but can be ignored in the future

    # Add the file sizes, names, and modified times of the first directory to the bloom filters
    for file_info in dir1_stats:
        if check_size:
            size_bloom.add(str(file_info['size']))
        if check_name:
            name_bloom.add(file_info['name'])
        if check_mdate:
            modified_time_bloom.add(str(file_info['modified_time']))

    # Find potential duplicates in the second directory based on the bloom filters
    potential_duplicates = []
    for file_info in dir2_stats:
        if (
                (not check_size or size_bloom.check(str(file_info['size']))) and
                (not check_name or name_bloom.check(file_info['name'])) and
                (not check_mdate or modified_time_bloom.check(str(file_info['modified_time'])))):
            potential_duplicates.append(file_info)

    # Return the potential duplicates
    return potential_duplicates


def aggregate_duplicate_candidates(potential_duplicates: List[Dict], combined: Dict, key: str, args: Namespace,
                                   key_func=get_files_keys_parallel) -> Dict:
    """
    Aggregate potential duplicates into a dictionary.
    :param potential_duplicates:
    :param combined: Dictionary to store the combined results as a list under the given key
    :param key: A key to store the results under
    :param args: Parsed arguments
    :param key_func: Function to generate keys for the files
    :return: Dictionary of results
    """
    parallel_results = key_func(args, potential_duplicates)
    for file_info_key, file_infos in parallel_results.items():
        if file_info_key not in combined:
            combined[file_info_key] = {}
        if key not in combined[file_info_key]:
            combined[file_info_key][key] = []
        for file_info in file_infos:
            combined[file_info_key][key].append(file_info)
    return combined


def find_duplicates_files_v3(args: Namespace, scan_dir: str, ref_dir: str) -> (Dict, List[Dict], List[Dict]):
    """
     Find duplicate files between scan_dir and ref directories.
     Returns a dictionary of duplicates and the file stats for both directories.
    """
    hash_manager = HashManager.get_instance()

    # Get the file stats for both directories and filter them based on the arguments
    scan_stats = filter_files_by_args(args, FileManager.get_files_and_stats(scan_dir))
    ref_stats = filter_files_by_args(args, FileManager.get_files_and_stats(ref_dir))

    # Use bloom filters to find potential duplicates between the two directories
    potential_scan_duplicates = find_potential_duplicates(ref_stats, scan_stats, args.ignore_diff)
    potential_ref_duplicates = find_potential_duplicates(scan_stats, ref_stats, args.ignore_diff)

    # Aggregate the potential duplicates into one dictionary
    combined = {}
    combined = aggregate_duplicate_candidates(potential_scan_duplicates, combined, 'scan', args)
    get_keys_function = get_files_keys_parallel \
        if (len(hash_manager.get_hashes_by_folder(ref_dir)) > len(ref_stats) / 2) else get_files_keys
    combined = aggregate_duplicate_candidates(potential_ref_duplicates, combined, 'ref', args,
                                              get_keys_function)

    # Filter out combined items that don't appear in both scan dir and reference dir - ie size = 2
    combined = {file_key: file_locations for file_key, file_locations in combined.items() if len(file_locations) == 2}

    # Sort the lists for both 'scan' and 'ref' lexicographically by their path
    for value in combined.values():
        value['scan'] = sorted(value['scan'], key=lambda x: x['path'])
        value['ref'] = sorted(value['ref'], key=lambda x: x['path'])

    return combined, scan_stats, ref_stats


def process_duplicates(combined: Dict, args: Namespace) -> (int, int):
    """
    Process the duplicates from source by moving or copying the files to the move_to folder.
    :param combined: the dictionary of duplicates returned by find_duplicates_files_v3
    :param args: parsed arguments
    :return: number of files moved, number of files created
    """
    files_created = files_moved = 0

    # Process each file key in the combined dictionary - it contains the scan and ref locations of the duplicates
    for file_key, locations in tqdm.tqdm(combined.items(), desc='Processing duplicates'):
        scan_files = locations.get('scan', [])
        ref_files = locations.get('ref', [])

        src_filepath = scan_files[0]['path']
        srcs_to_move = [(file['path'], 0) for file in scan_files]

        # Copy or move files to reference locations
        if not args.copy_to_all:
            copy_or_move_file(src_filepath, args.move_to, ref_files[0]['path'], args.reference_dir, move=True)
            files_moved += 1
        else:
            num_to_copy = max(0, len(ref_files) - len(srcs_to_move))
            for i in range(num_to_copy):
                copy_or_move_file(src_filepath, args.move_to, ref_files[i]['path'], args.reference_dir, False)
                files_created += 1

            for (src, _), tgt in zip(srcs_to_move, ref_files[num_to_copy:]):
                copy_or_move_file(src, args.move_to, tgt['path'], args.reference_dir, move=True)
                files_moved += 1

    return files_moved, files_created


def create_csv_file(args: Namespace, combined: Dict) -> None:
    """
    Create a CSV file with the duplicate files' information.
    :param args: parsed arguments
    :param combined: the dictionary of duplicates returned by find_duplicates_files_v3
    :return: number of files moved
    """
    csv_file = os.path.join(args.move_to, os.path.basename(args.scan_dir) + "_dups.csv")
    if not os.path.exists(args.move_to):
        FileManager.get_instance().make_dirs(args.move_to)

    # Every line in the CSV file will contain a single duplicate file. The first line will contain the header.
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["key", "path", "size", "modified_time"])
        key = 1
        for file_key, locations in combined.items():
            for category, files in locations.items():
                for file in files:
                    writer.writerow([key, file['path'], file['size'], datetime.fromtimestamp(file['modified_time'])])
            key += 1



def clean_scan_dir_duplications(args: Namespace, combined: Dict) -> int:
    """
    Clean up the scan_dir duplications after moving files to the move_to folder.
    :param args: parsed arguments
    :param combined: a dictionary which all the files under 'scan' (for all keys) are moved to the move_to folder
    :return: number of files moved
    """
    scan_paths = [file_info['path'] for key, locations in combined.items() if 'scan' in locations for file_info in
                  locations['scan'] if os.path.exists(file_info['path'])]
    scan_dups_move_to: str = str(os.path.join(args.move_to, os.path.basename(args.scan_dir) + "_dups"))
    for src_path in scan_paths:
        copy_or_move_file(src_path, scan_dups_move_to, src_path, args.scan_dir, move=True)
    return len(scan_paths)
