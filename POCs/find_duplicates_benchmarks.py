import concurrent.futures
import timeit
from collections import defaultdict
from pprint import pprint

from probables import BloomFilter

from duplicate_files_in_folders.hash_manager import HashManager
from duplicate_files_in_folders.file_manager import FileManager
from duplicate_files_in_folders.utils import parse_arguments, get_file_key
from typing import Dict, List
import pandas as pd

target_directory = '/path/to/target/folder'
source_directory = '/path/to/source/folder'

hash_manager = HashManager(target_directory)


def reset_hash_manager(target_folder, no_reset_target=False):
    global hash_manager
    if not no_reset_target:
        hash_manager.reset_instance()
    hash_manager = HashManager(target_folder, None)
    # hash_manager.target_folder = target_folder

    # clear temporary data anyway
    hash_manager.temporary_data = pd.DataFrame(columns=['file_path', 'hash_value', 'last_update'])


def find_potential_duplicates(dir1_stats, dir2_stats, ignore_diff):
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


def filter_files_by_args(args, files_stats: List[Dict]) -> List[Dict]:
    min_size = args.min_size if args.min_size is not None else 0
    max_size = args.max_size if args.max_size is not None else float('inf')
    filtered_files = [file_info for file_info in files_stats
                      if min_size <= int(file_info['size']) <= max_size and
                      (args.whitelist_ext is None or file_info['name'].split('.')[-1] in args.whitelist_ext) and
                      (args.blacklist_ext is None or file_info['name'].split('.')[-1] not in args.blacklist_ext)]
    return filtered_files


def find_duplicates_files(args, source, target, no_reset=False):
    reset_hash_manager(target_directory, no_reset)
    source_stats = filter_files_by_args(args, FileManager.get_files_and_stats(source))
    target_stats = filter_files_by_args(args, FileManager.get_files_and_stats(target))

    print(f"Found {len(source_stats)} files in source directory")
    print(f"Found {len(target_stats)} files in target directory")

    potential_source_duplicates = find_potential_duplicates(target_stats, source_stats, args.ignore_diff)
    potential_target_duplicates = find_potential_duplicates(source_stats, target_stats, args.ignore_diff)

    combined = defaultdict(defaultdict)
    for file_info in potential_source_duplicates:
        file_info_key = get_file_key(args, file_info['path'])
        if 'source' not in combined[file_info_key]:
            combined[file_info_key]['source'] = []
        combined[file_info_key]['source'].append(file_info)

    for file_info in potential_target_duplicates:
        file_info_key = get_file_key(args, file_info['path'])
        if 'target' not in combined[file_info_key]:
            combined[file_info_key]['target'] = []
        combined[file_info_key]['target'].append(file_info)

    # filter out combined items that don't have both source and target - ie size = 2
    combined = {k: v for k, v in combined.items() if len(v) == 2}
    return combined


def get_file_key_parallel(args, file_infos):
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


def process_potential_duplicates(potential_duplicates, combined, key, args):
    parallel_results = get_file_key_parallel(args, potential_duplicates)
    for file_info_key, file_infos in parallel_results.items():
        if key not in combined[file_info_key]:
            combined[file_info_key][key] = []
        for file_info in file_infos:
            combined[file_info_key][key].append(file_info)
    return combined


def find_duplicates_files_v2(args, source, target, no_reset=False):
    reset_hash_manager(target_directory, no_reset)
    source_stats = filter_files_by_args(args, FileManager.get_files_and_stats(source))
    target_stats = filter_files_by_args(args, FileManager.get_files_and_stats(target))

    print(f"Found {len(source_stats)} files in source directory")
    print(f"Found {len(target_stats)} files in target directory")

    potential_source_duplicates = find_potential_duplicates(target_stats, source_stats, args.ignore_diff)
    potential_target_duplicates = find_potential_duplicates(source_stats, target_stats, args.ignore_diff)

    combined = defaultdict(defaultdict)
    combined = process_potential_duplicates(potential_source_duplicates, combined, 'source', args)
    combined = process_potential_duplicates(potential_target_duplicates, combined, 'target', args)

    # Filter out combined items that don't have both source and target - ie size = 2
    combined = {k: v for k, v in combined.items() if len(v) == 2}
    return combined


def process_potential_duplicates_v3(potential_duplicates, combined, key, args, key_func=get_file_key_parallel):
    parallel_results = key_func(args, potential_duplicates)
    for file_info_key, file_infos in parallel_results.items():
        if key not in combined[file_info_key]:
            combined[file_info_key][key] = []
        for file_info in file_infos:
            combined[file_info_key][key].append(file_info)
    return combined


def find_duplicates_files_v3(args, source, target, no_reset=False):
    reset_hash_manager(target_directory, no_reset)
    source_stats = filter_files_by_args(args, FileManager.get_files_and_stats(source))
    target_stats = filter_files_by_args(args, FileManager.get_files_and_stats(target))

    print(f"Found {len(source_stats)} files in source directory")
    print(f"Found {len(target_stats)} files in target directory")

    potential_source_duplicates = find_potential_duplicates(target_stats, source_stats, args.ignore_diff)
    potential_target_duplicates = find_potential_duplicates(source_stats, target_stats, args.ignore_diff)

    combined = defaultdict(defaultdict)
    combined = process_potential_duplicates_v3(potential_source_duplicates, combined, 'source', args)
    get_keys_function = get_file_key_parallel \
        if (len(hash_manager.get_hashes_by_folder(target)) > len(target_stats) / 2) else get_files_keys
    combined = process_potential_duplicates_v3(potential_target_duplicates, combined, 'target', args, get_keys_function)

    # Filter out combined items that don't have both source and target - ie size = 2
    combined = {k: v for k, v in combined.items() if len(v) == 2}
    return combined


def find_duplicates_files_v4(args, source, target, no_reset=False):
    reset_hash_manager(target_directory, no_reset)
    source_stats = filter_files_by_args(args, FileManager.get_files_and_stats(source))
    target_stats = filter_files_by_args(args, FileManager.get_files_and_stats(target))

    print(f"Found {len(source_stats)} files in source directory")
    print(f"Found {len(target_stats)} files in target directory")

    potential_source_duplicates = find_potential_duplicates(target_stats, source_stats, args.ignore_diff)
    potential_target_duplicates = find_potential_duplicates(source_stats, target_stats, args.ignore_diff)

    combined = defaultdict(defaultdict)
    combined = process_potential_duplicates(potential_source_duplicates, combined, 'source', args)
    should_use_parallel = len(hash_manager.get_hashes_by_folder(target)) > len(target_stats) / 2
    if should_use_parallel:
        combined = process_potential_duplicates(potential_target_duplicates, combined, 'target', args)
    else:
        for file_info in potential_target_duplicates:
            file_info_key = get_file_key(args, file_info['path'])
            if 'target' not in combined[file_info_key]:
                combined[file_info_key]['target'] = []
            combined[file_info_key]['target'].append(file_info)

    # Filter out combined items that don't have both source and target - ie size = 2
    combined = {k: v for k, v in combined.items() if len(v) == 2}
    return combined


def get_files_keys(args, file_infos):
    results = {}
    for file_info in file_infos:
        file_info_key = get_file_key(args, file_info['path'])
        if file_info_key not in results:
            results[file_info_key] = []
        results[file_info_key].append(file_info)
    return results


if __name__ == "__main__":
    custom_args = [
        '--src', source_directory,
        '--target', target_directory,
        '--move_to', 'c:\\temp\\',
        '--min_size', '1',
        # '--max_size', '20KB',
        '--ignore_diff', 'mdate,filename',
        # '--whitelist_ext', 'txt,docx,pdf,doc',
        # '--blacklist_ext', 'gif,jpg,png,jpe'
    ]
    final_args = parse_arguments(custom_args)
    pprint(final_args)

    # PERFORMANCE TEST:

    num = 2

    time2 = timeit.timeit(lambda: find_duplicates_files_v2(final_args, source_directory, target_directory), number=num)
    time2_2 = timeit.timeit(lambda: find_duplicates_files_v2(final_args, source_directory, target_directory, True),
                            number=num)
    time1 = timeit.timeit(lambda: find_duplicates_files(final_args, source_directory, target_directory), number=num)
    time1_2 = timeit.timeit(lambda: find_duplicates_files(final_args, source_directory, target_directory, True),
                            number=num)

    time3 = timeit.timeit(lambda: find_duplicates_files_v3(final_args, source_directory, target_directory), number=num)
    time3_2 = timeit.timeit(lambda: find_duplicates_files_v3(final_args, source_directory, target_directory, True),
                            number=num)

    time4 = timeit.timeit(lambda: find_duplicates_files_v4(final_args, source_directory, target_directory), number=num)
    time4_2 = timeit.timeit(lambda: find_duplicates_files_v4(final_args, source_directory, target_directory, True),
                            number=num)

    print(f"find_duplicates_files: {time1:.6f} seconds")
    print(f"find_duplicates_files_v2: {time2:.6f} seconds")
    print(f"find_duplicates_files_v3: {time3:.6f} seconds")
    print(f"find_duplicates_files_v4: {time4:.6f} seconds")

    print(f"find_duplicates_files_no_reset: {time1_2:.6f} seconds")
    print(f"find_duplicates_files_v2_no_reset: {time2_2:.6f} seconds")
    print(f"find_duplicates_files_v3_no_reset: {time3_2:.6f} seconds")
    print(f"find_duplicates_files_v4_no_reset: {time4_2:.6f} seconds")

    # CHECK CORRECTNESS:

    # verified_duplicates = find_duplicates_files(final_args, source_directory, target_directory)
    #
    # count_source = 0
    # count_target = 0
    # for k, v in verified_duplicates.items():
    #     if len(v) == 2:
    #         count_source += len(v['source'])
    #         count_target += len(v['target'])
    # print(f"Found {len(verified_duplicates)} unique duplicates files in {source_directory}")
    # print(f"Total of {count_source} files from source are duplicates of files in {target_directory}")
    # print(f"Those files are {count_target} files in {target_directory}")
    #
    # verified_duplicates2 = find_duplicates_files_v2(final_args, source_directory, target_directory)
    # count_source = 0
    # count_target = 0
    # for k, v in verified_duplicates2.items():
    #     if len(v) == 2:
    #         count_source += len(v['source'])
    #         count_target += len(v['target'])
    # print(f"V2 found {len(verified_duplicates2)} unique duplicates files in {source_directory}")
    # print(f"Total of {count_source} files from source are duplicates of files in {target_directory}")
    # print(f"Those files are {count_target} files in {target_directory}")
