import os
import concurrent.futures
from collections import defaultdict
from probables import BloomFilter
from duplicate_files_in_folders.hash_manager import HashManager
from duplicate_files_in_folders.file_manager import FileManager
from typing import Dict, List, Set


def get_file_hash(file_path: str) -> str:
    """Retrieve the hash of the given file."""
    hash_manager = HashManager.get_instance()
    return hash_manager.get_hash(file_path)


def get_file_key(args, file_path: str) -> str:
    """
    Generate a unique key for the file based on hash, filename, and modified date.
    Ignores components based on args.
    """
    hash_key: str = get_file_hash(file_path)
    file_key: str = file_path[file_path.rfind(os.sep) + 1:] if 'filename' not in args.ignore_diff else None
    mdate_key: str = str(os.path.getmtime(file_path)) if 'mdate' not in args.ignore_diff else None
    return '_'.join(filter(None, [hash_key, file_key, mdate_key]))


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
    check_name = 'name' not in ignore_diff
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
    get_keys_function = get_files_keys_parallel if (len(hash_manager.get_hashes_by_folder(target)) > len(target_stats) / 2) else get_files_keys
    combined = process_potential_duplicates(potential_target_duplicates, combined, 'target', args, get_keys_function)

    # Filter out combined items that don't have both source and target - ie size = 2
    combined = {k: v for k, v in combined.items() if len(v) == 2}
    return combined, source_stats, target_stats
