import os
import timeit
from collections import deque


def list_directories_bottom_up(directory, raise_on_permission_error=False):
    stack = []
    queue = deque([directory])

    # Breadth-first search to collect all directories
    while queue:
        current_dir = queue.popleft()
        try:
            with os.scandir(current_dir) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        queue.append(entry.path)
                        stack.append(entry.path)
        except PermissionError:
            if raise_on_permission_error:
                raise
            else:
                continue

    # Return directories in bottom-up order
    # while stack:
    #     yield stack.pop()
    return stack


def list_directories_bottom_up_walk(base_path):
    folders_by_depth = {}  # collect all folders in the source folder by depth
    for root, dirs, files in os.walk(base_path, topdown=False):
        if base_path == root:
            continue
        depth = root.count(os.sep) - base_path.count(os.sep)
        if depth not in folders_by_depth:
            folders_by_depth[depth] = []
        folders_by_depth[depth].append(root)
    return folders_by_depth

dir = 'c:\\temp'
num = 1000
scan_time = timeit.timeit(lambda: list_directories_bottom_up(dir), number=num)
walk_time = timeit.timeit(lambda: list_directories_bottom_up_walk(dir), number=num)

print(f"list_directories_bottom_up: {scan_time:.6f} seconds")
print(f"list_directories_bottom_up_walk: {walk_time:.6f} seconds")

# Sample output:
#  list_directories_bottom_up: 104.569966 seconds
#  list_directories_bottom_up_walk: 113.394339 seconds