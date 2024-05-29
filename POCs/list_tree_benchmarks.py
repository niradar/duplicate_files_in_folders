import os
import time
import concurrent.futures
from pathlib import Path
import timeit
from collections import deque


class FileInformation:
    def __init__(self, path, size, modified_time, created_time):
        self.path = path
        self.size = size
        self.modified_time = modified_time
        self.created_time = created_time

    def __repr__(self):
        return (f"FileInformation(path={self.path}, size={self.size}, modified_time={self.modified_time}, "
                f"created_time={self.created_time})")


def get_files_and_stats(file_path):
    files_stats = []
    for root, dirs, files in os.walk(file_path):
        for f in files:
            file_path = os.path.join(root, f)
            stats = os.stat(file_path)
            file_info = {
                'path': file_path,
                'size': stats.st_size,
                'modified_time': stats.st_mtime,  # time.ctime(stats.st_mtime) if you want to convert to string
                'created_time': stats.st_ctime  # time.ctime(stats.st_ctime) if you want to convert to string
            }
            files_stats.append(file_info)
    return files_stats


def get_file_info_generic(file_path):
    stats = os.stat(file_path)
    return {
        'path': file_path,
        'size': stats.st_size,
        'modified_time': stats.st_mtime,  # time.ctime(stats.st_mtime) if you want to convert to string
        'created_time': stats.st_ctime  # time.ctime(stats.st_ctime) if you want to convert to string
    }


def get_file_info_as_class(file_path):
    stats = os.stat(file_path)
    return FileInformation(
        path=file_path,
        size=stats.st_size,
        modified_time=time.ctime(stats.st_mtime),
        created_time=time.ctime(stats.st_ctime)
    )


def get_files_and_stats_v2_oswalk_tpe_generic(directory):
    files_stats = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                futures.append(executor.submit(get_file_info_generic, file_path))

        for future in concurrent.futures.as_completed(futures):
            files_stats.append(future.result())

    return files_stats


def get_files_and_stats_v3_oswalk_tpe_class(directory):
    files_stats = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                futures.append(executor.submit(get_file_info_as_class, file_path))

        for future in concurrent.futures.as_completed(futures):
            files_stats.append(future.result())

    return files_stats


def get_files_and_stats_v4_oswalk_ppe_class(directory):
    files_stats = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                futures.append(executor.submit(get_file_info_as_class, file_path))

        for future in concurrent.futures.as_completed(futures):
            files_stats.append(future.result())

    return files_stats


def get_files_and_stats_v5_oswalk_tpe_workers_class(directory, max_workers=16):
    files_stats = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers if max_workers else None) as executor:
        futures = []
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                futures.append(executor.submit(get_file_info_as_class, file_path))

        for future in concurrent.futures.as_completed(futures):
            files_stats.append(future.result())

    return files_stats


def get_files_and_stats_v6_scandir_tpe_stack_class(directory):
    def list_tree_os_scandir(directory):
        stack = [directory]
        while stack:
            current_dir = stack.pop()
            try:
                with os.scandir(current_dir) as it:
                    for entry in it:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        else:
                            yield entry.path
            except PermissionError:
                continue

    files_stats = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for file_path in list_tree_os_scandir(directory):
            futures.append(executor.submit(get_file_info_as_class, file_path))

        for future in concurrent.futures.as_completed(futures):
            files_stats.append(future.result())

    return files_stats


def get_files_and_stats_v7_scandir_tpe_stack_generic(directory, max_workers=8):
    def list_tree_os_scandir(directory):
        stack = [directory]
        while stack:
            current_dir = stack.pop()
            try:
                with os.scandir(current_dir) as it:
                    for entry in it:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        else:
                            yield entry.path
            except PermissionError:
                continue

    files_stats = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for file_path in list_tree_os_scandir(directory):
            futures.append(executor.submit(get_file_info_generic, file_path))

        for future in concurrent.futures.as_completed(futures):
            files_stats.append(future.result())

    return files_stats


def get_files_and_stats_v8_scandir_tpe_deque_generic(directory, max_workers=8):
    def list_tree_os_scandir_bfs(directory):
        queue = deque([directory])
        while queue:
            current_dir = queue.popleft()
            try:
                with os.scandir(current_dir) as it:
                    for entry in it:
                        if entry.is_dir(follow_symlinks=False):
                            queue.append(entry.path)
                        else:
                            yield entry.path
            except PermissionError:
                # print(f"Access is denied: '{current_dir}'")
                continue

    files_stats = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for file_path in list_tree_os_scandir_bfs(directory):
            futures.append(executor.submit(get_file_info_generic, file_path))

        for future in concurrent.futures.as_completed(futures):
            files_stats.append(future.result())

    return files_stats


def get_files_and_stats_v9_scandir_deque_generic(directory):
    files_stats = []
    queue = deque([directory])
    while queue:
        current_dir = queue.popleft()
        try:
            with os.scandir(current_dir) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        queue.append(entry.path)
                    else:
                        stats = entry.stat()
                        files_stats.append({'path': entry.path, 'size': stats.st_size, 'name': entry.name,
                                            'modified_time': stats.st_mtime, 'created_time': stats.st_ctime})
        except PermissionError:
            continue
    return files_stats

def compare_performance(directory, iterations=5):
    durations_v2 = []
    durations_v3 = []
    durations_v6 = []
    durations_v7 = []
    durations_v8 = []
    durations_v9 = []
    original_durations = []

    for _ in range(iterations):
        original_durations.append(timeit.timeit(lambda: get_files_and_stats(directory), number=1))
        durations_v2.append(timeit.timeit(lambda: get_files_and_stats_v2_oswalk_tpe_generic(directory), number=1))
        durations_v3.append(timeit.timeit(lambda: get_files_and_stats_v3_oswalk_tpe_class(directory), number=1))
        durations_v6.append(timeit.timeit(lambda: get_files_and_stats_v6_scandir_tpe_stack_class(directory), number=1))
        durations_v7.append(timeit.timeit(lambda: get_files_and_stats_v7_scandir_tpe_stack_generic(directory), number=1))
        durations_v8.append(timeit.timeit(lambda: get_files_and_stats_v8_scandir_tpe_deque_generic(directory), number=1))
        durations_v9.append(timeit.timeit(lambda: get_files_and_stats_v9_scandir_deque_generic(directory), number=1))

    # Candidate for the best result
    avg_original_duration = sum(original_durations) / iterations
    avg_optimized_duration_v2 = sum(durations_v2) / iterations
    avg_optimized_duration_v3 = sum(durations_v3) / iterations
    avg_optimized_duration_v6 = sum(durations_v6) / iterations
    avg_optimized_duration_v7 = sum(durations_v7) / iterations
    avg_optimized_duration_v8 = sum(durations_v8) / iterations
    avg_optimized_duration_v9 = sum(durations_v9) / iterations

    print(f"Average original function duration: {avg_original_duration:.2f} seconds")
    print(f"Average function v2 (oswalk, tpe, generic) duration: {avg_optimized_duration_v2:.2f} seconds")
    print(f"Average function v3 (oswalk, tpe, class) duration: {avg_optimized_duration_v3:.2f} seconds")
    print(f"Average function v6 (scandir, tpe, stack, class) duration: {avg_optimized_duration_v6:.2f} seconds")
    print(f"Average function v7 (scandir, tpe, stack, generic) duration: {avg_optimized_duration_v7:.2f} seconds")
    print(f"Average function v8 (scandir, tpe, deque, generic) duration: {avg_optimized_duration_v8:.2f} seconds")
    print(f"Average function v9 (scandir, deque, generic) duration: {avg_optimized_duration_v9:.2f} seconds")


if __name__ == "__main__":
    test_directory = "DEFINE DIRECTORY_FOR_TESTING"
    compare_performance(test_directory, 3)

    sample_output = False
    if sample_output:
        res = get_files_and_stats_v9_scandir_deque_generic(test_directory)
        for file_res in res:
            print(file_res)

# Sample output:
# Average original function duration: 5.09 seconds
# Average function v2 (oswalk, tpe, generic) duration: 3.28 seconds
# Average function v3 (oswalk, tpe, class) duration: 3.91 seconds
# Average function v6 (scandir, tpe, stack, class) duration: 3.66 seconds
# Average function v7 (scandir, tpe, stack, generic) duration: 3.15 seconds
# Average function v8 (scandir, tpe, deque, generic) duration: 3.11 seconds
# Average function v9 (scandir, deque, generic) duration: 0.40 seconds
