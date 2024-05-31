from pathlib import Path
import shutil
import os
import logging
from collections import deque
from typing import Dict, List
import tqdm

logger = logging.getLogger(__name__)


class FileManagerError(Exception):
    pass


class ProtectedPathError(FileManagerError):
    def __init__(self, message):
        super().__init__(message)


class FileManager:
    _instance = None
    protected_dirs = set()
    allowed_dirs = set()  # If set, only operations in these directories are allowed. Acts as a whitelist
    run_mode = False

    def __new__(cls, run_mode, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FileManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.run_mode = run_mode
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            # create a new instance if it doesn't exist - run_mode is False by default. Should not happen in real life
            cls._instance = cls(False)
        return cls._instance

    def add_protected_dir(self, dir_path):
        protected_dir = Path(dir_path).resolve()

        # raise an error if the directory is already in the allowed_dirs
        if self.allowed_dirs and protected_dir in self.allowed_dirs:
            raise FileManagerError(f"Cannot add a directory to both protected and allowed directories list: {dir_path}")

        if protected_dir not in self.protected_dirs:
            self.protected_dirs.add(protected_dir)

    def add_allowed_dir(self, dir_path):
        allowed_dir = Path(dir_path).resolve()

        # raise an error if the directory is already in the protected_dirs
        if self.protected_dirs and allowed_dir in self.protected_dirs:
            raise FileManagerError(f"Cannot add a directory to both protected and allowed directories list: {dir_path}")

        if allowed_dir not in self.allowed_dirs:
            self.allowed_dirs.add(allowed_dir)

    def is_protected_path(self, path):
        path = Path(path).resolve()
        if self.protected_dirs is None:  # This should never happen in real life
            raise FileManagerError("Protected directories not set")

        # True if the path is in any of the protected directories or if it is not in any of the allowed directories
        return any(path == protected_dir or protected_dir in path.parents for protected_dir in self.protected_dirs) or \
                  (self.allowed_dirs and not any(path == allowed_dir or allowed_dir in path.parents for allowed_dir
                                                 in self.allowed_dirs))

    def move_file(self, src, dst):
        src_path = Path(src).resolve()
        dst_path = Path(dst).resolve()

        if self.is_protected_path(src_path) or self.is_protected_path(dst_path):
            raise ProtectedPathError(
                f"Operation not allowed: Attempt to move protected file or to protected directory: {src} -> {dst}")

        src_to_dst = f"{src_path} to {dst_path}"
        if self.run_mode:
            shutil.move(src_path, dst_path)
            logger.info(f"Moved {src_to_dst}")
        else:
            logger.info(f"Would have moved {src_to_dst}")

        return True

    def copy_file(self, src, dst):
        src_path = Path(src).resolve()
        dst_path = Path(dst).resolve()

        if self.is_protected_path(dst_path):
            raise ProtectedPathError(
                f"Operation not allowed: Attempt to copy file to protected directory: {src} -> {dst}")

        src_to_dst = f"{src_path} to {dst_path}"
        if self.run_mode:
            shutil.copy2(src_path, dst_path)
            logger.info(f"Copied {src_to_dst}")
        else:
            logger.info(f"Would have copied {src_to_dst}")
        return True

    def delete_file(self, file_path):
        file_path = Path(file_path).resolve()

        if self.is_protected_path(file_path):
            raise ProtectedPathError(f"Operation not allowed: Attempt to delete protected file: {file_path}")

        if self.run_mode:
            os.remove(file_path)
            logger.info(f"Deleted {file_path}")
        else:
            logger.info(f"Would have deleted {file_path}")
        return True

    def make_dirs(self, dir_path):
        dir_path = Path(dir_path).resolve()

        if self.is_protected_path(dir_path):
            raise ProtectedPathError(f"Operation not allowed: Attempt to create directory in protected path: "
                                     f"{dir_path}")
        if self.run_mode:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory {dir_path}")
        else:
            logger.info(f"Would have created directory {dir_path}")
        return True

    def rmdir(self, dir_path):
        dir_path = Path(dir_path).resolve()

        if self.is_protected_path(dir_path):
            raise ProtectedPathError(f"Operation not allowed: Attempt to delete protected directory: {dir_path}")

        if self.run_mode:
            shutil.rmtree(dir_path)
            logger.info(f"Deleted directory {dir_path}")
        else:
            logger.info(f"Would have deleted directory {dir_path}")
        return True

    @staticmethod
    def get_file_info(file_path):
        stats = os.stat(file_path)
        return {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': stats.st_size,
            'modified_time': stats.st_mtime,
            'created_time': stats.st_ctime
        }

    @staticmethod
    def list_tree_os_scandir_bfs(directory, raise_on_permission_error=False):
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
                if raise_on_permission_error:
                    raise
                else:
                    continue

    @staticmethod
    def get_files_and_stats(directory, raise_on_permission_error=False) -> List[Dict]:
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
                            files_stats.append(
                                {'path': entry.path, 'size': stats.st_size, 'name': entry.name,
                                 'modified_time': stats.st_mtime, 'created_time': stats.st_ctime})
            except PermissionError:
                if raise_on_permission_error:
                    raise
                continue
        return files_stats

    def delete_empty_folders_in_tree(self, base_path, show_progress=False, progress_desc="Deleting empty folders"):
        if self.is_protected_path(base_path):
            raise ProtectedPathError(f"Operation not allowed: Attempt to delete empty folders in protected path: "
                                     f"{base_path}")
        if not self.run_mode:
            logger.info(f"Would have deleted empty folders in {base_path}")
            return 0
        folders_by_depth = {}  # collect all folders in the source folder by depth
        for root, dirs, files in os.walk(base_path, topdown=False):
            if base_path == root:
                continue
            depth = root.count(os.sep) - base_path.count(os.sep)
            if depth not in folders_by_depth:
                folders_by_depth[depth] = []
            folders_by_depth[depth].append(root)

        # Count all folders
        total_folders = sum(len(folders) for folders in folders_by_depth.values())

        # Initialize tqdm if progress display is enabled
        progress_bar = tqdm.tqdm(total=total_folders, desc=progress_desc) if show_progress else None

        deleted_folders = 0
        # Delete empty folders starting from the deepest level excluding the base_path folder
        for depth in sorted(folders_by_depth.keys(), reverse=True):
            for folder in folders_by_depth[depth]:
                if not os.listdir(folder):
                    try:
                        os.rmdir(folder)
                        deleted_folders += 1
                    except OSError as e:
                        print(f"Error deleting folder {folder}: {e}")
                if show_progress:
                    progress_bar.update(1)

        if show_progress:
            progress_bar.close()

        return deleted_folders

    def reset_all(self):
        self.protected_dirs = set()
        self.allowed_dirs = set()
        return self

    @staticmethod
    def reset_file_manager(protected_dirs, allowed_dirs, run_mode):
        FileManager._instance = None
        fm = FileManager(run_mode).reset_all()
        for dir_path in protected_dirs:
            fm.add_protected_dir(dir_path)
        for dir_path in allowed_dirs:
            fm.add_allowed_dir(dir_path)
        return fm

    def set_run_mode(self, run_mode):
        self.run_mode = run_mode
        return self
