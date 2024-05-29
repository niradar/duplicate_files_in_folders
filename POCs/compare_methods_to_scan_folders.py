import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import timeit


def list_tree_os_walk(directory):
    res = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            res.append(os.path.join(root, name))
    return res


def list_tree_os_scandir(directory):
    stack = [directory]
    files = []
    while stack:
        current_dir = stack.pop()
        with os.scandir(current_dir) as it:
            for entry in it:
                if entry.is_dir(follow_symlinks=False):
                    stack.append(entry.path)
                files.append(entry.path)
    return files


def list_tree_pathlib(directory):
    return [str(path) for path in Path(directory).rglob('*')]


def list_tree_concurrent(directory):
    def scan_dir(path):
        entries = []
        with os.scandir(path) as it:
            for entry in it:
                entries.append(entry.path)
        return entries

    all_files = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(scan_dir, directory)]
        while futures:
            future = futures.pop()
            for entry in future.result():
                all_files.append(entry)
                if os.path.isdir(entry):
                    futures.append(executor.submit(scan_dir, entry))

    return all_files


# Define the directory to be scanned - change to a directory with many files
directory = 'c:\\temp'
runs = 2
# Measure performance
time_os_walk = timeit.timeit(lambda: list_tree_os_walk(directory), number=runs)
time_os_scandir = timeit.timeit(lambda: list_tree_os_scandir(directory), number=runs)
time_pathlib = timeit.timeit(lambda: list_tree_pathlib(directory), number=runs)
time_concurrent = timeit.timeit(lambda: list_tree_concurrent(directory), number=runs)

# Print results
print(f"os.walk: {time_os_walk} seconds")
print(f"os.scandir: {time_os_scandir} seconds")
print(f"pathlib.Path.rglob: {time_pathlib} seconds")
print(f"concurrent.futures: {time_concurrent} seconds")

# Sample output:
# os.walk: 0.4717858000076376 seconds
# os.scandir: 0.21429039997747168 seconds
# pathlib.Path.rglob: 0.7339643999875989 seconds
# concurrent.futures: 1.269670200010296 seconds
