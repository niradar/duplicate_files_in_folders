from pathlib import Path
import shutil
import os
import logging
from collections import deque
from typing import Dict, List, Tuple
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
        """
        :return: Singleton instance of the FileManager class
        """
        if cls._instance is None:
            # create a new instance if it doesn't exist - run_mode is False by default. Should not happen in real life
            logger.warning("Creating a new instance of FileManager with run_mode=False")
            cls._instance = cls(False)
        return cls._instance

    def add_protected_dir(self, dir_path: str | Path):
        """
        Add a directory to the protected directories list
        :param dir_path: path to the directory
        :return: None
        :raises: FileManagerError if the directory is already in the allowed_dirs
        """
        protected_dir = Path(dir_path).resolve()

        # raise an error if the directory is already in the allowed_dirs
        if self.allowed_dirs and protected_dir in self.allowed_dirs:
            raise FileManagerError(f"Cannot add a directory to both protected and allowed directories list: {dir_path}")

        if protected_dir not in self.protected_dirs:
            self.protected_dirs.add(protected_dir)

    def add_allowed_dir(self, dir_path: str | Path):
        """
        Add a directory to the allowed directories list
        :param dir_path: path to the directory
        :return: None
        :raises: FileManagerError if the directory is already in the protected_dirs
        """
        allowed_dir = Path(dir_path).resolve()

        # raise an error if the directory is already in the protected_dirs
        if self.protected_dirs and allowed_dir in self.protected_dirs:
            raise FileManagerError(f"Cannot add a directory to both protected and allowed directories list: {dir_path}")

        if allowed_dir not in self.allowed_dirs:
            self.allowed_dirs.add(allowed_dir)

    def is_protected_path(self, path: str | Path) -> bool:
        """
        Check if a path is in a protected directory or in a subdirectory of a protected directory
        :param path: path to check
        :return: True if the path is in a protected directory or in a subdirectory of a protected directory
        """
        path = Path(path).resolve()
        if self.protected_dirs is None:  # This should never happen in real life
            raise FileManagerError("Protected directories not set")

        # True if the path is in any of the protected directories or if it is not in any of the allowed directories
        # use is_allowed_path instead of the second condition to avoid a circular dependency
        return any(path == protected_dir or protected_dir in path.parents for protected_dir in self.protected_dirs) \
            or not self.is_allowed_path(path)

    def is_allowed_path(self, path: str | Path) -> bool:
        """
        Check if a path is in an allowed directory or in a subdirectory of an allowed directory
        If allowed_dirs is empty, all paths are allowed
        :param path: path to check
        :return: True if the path is in an allowed directory or in a subdirectory of an allowed directory
        """
        path = Path(path).resolve()
        if not self.allowed_dirs:
            return True  # If allowed_dirs is an empty set, all paths are allowed

        # True if the path is in any of the allowed directories
        return any(path == allowed_dir or allowed_dir in path.parents for allowed_dir in self.allowed_dirs)

    def move_file(self, src: str, dst: str) -> bool:
        """
        Move a file from src to dst
        :param src: path to the source file
        :param dst: path to the destination file
        :return: True if the file was moved successfully
        :raises: ProtectedPathError if the source or destination path is in a protected directory
        """
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

    def copy_file(self, src: str, dst: str) -> bool:
        """
        Copy a file from src to dst
        :param src: path to the source file
        :param dst: path to the destination file
        :return: True if the file was copied successfully
        :raises: ProtectedPathError if the source or destination path is in a protected directory
        """
        src_path = Path(src).resolve()
        dst_path = Path(dst).resolve()

        if self.is_protected_path(dst_path):
            raise ProtectedPathError(
                f"Operation not allowed: Attempt to copy file to protected directory: {src} -> {dst}")
        if not self.is_allowed_path(src_path):
            raise ProtectedPathError(
                f"Operation not allowed: Attempt to copy file from disallowed directory: {src} -> {dst}")

        src_to_dst = f"{src_path} to {dst_path}"
        if self.run_mode:
            shutil.copy2(src_path, dst_path)
            logger.info(f"Copied {src_to_dst}")
        else:
            logger.info(f"Would have copied {src_to_dst}")
        return True

    def _perform_single_file_operation(self, path: str | Path, operation: str, operation_text: str):
        """
        Perform a single file operation (delete, make_dirs, rmdir) with error handling for protected paths.

        :param operation: The operation to perform ('delete', 'make_dirs', 'rmdir').
        :param path: Path to the file or directory.
        :raises: ProtectedPathError if the path is in a protected directory.
        :raises: ValueError if the operation is invalid.
        """
        if self.is_protected_path(path):
            raise ProtectedPathError(f"Operation not allowed: Attempt to {operation} protected path: {path}")

        if self.run_mode:
            if operation == 'delete':
                os.remove(path)
            elif operation == 'make_dirs':
                os.makedirs(path, exist_ok=True)
            elif operation == 'rmdir':
                shutil.rmtree(path)
            else:
                raise ValueError(f"Invalid operation: {operation}")
            logger.info(f"{operation_text.capitalize()} {path}")
        else:
            logger.info(f"Would have {operation_text} {path}")

    def delete_file(self, file_path: str):
        """
        Delete a file.

        :param file_path: Path to the file.
        :raises: ProtectedPathError if the file path is in a protected directory.
        """
        file_path = Path(file_path).resolve()
        self._perform_single_file_operation(file_path, 'delete', 'deleted')

    def make_dirs(self, dir_path: str):
        """
        Create a directory.

        :param dir_path: Path to the directory(s) to create.
        :raises: ProtectedPathError if the directory path is in a protected directory.
        """
        dir_path = Path(dir_path).resolve()
        self._perform_single_file_operation(dir_path, 'make_dirs', 'created directory')

    def rmdir(self, dir_path: str):
        """
        Delete a directory.

        :param dir_path: Path to the directory(s) to delete.
        :raises: ProtectedPathError if the directory path is in a protected directory.
        """
        dir_path = Path(dir_path).resolve()
        self._perform_single_file_operation(dir_path, 'rmdir', 'deleted directory')

    @staticmethod
    def get_file_info(file_path: str) -> Dict:
        """
        Get file information
        :param file_path: path to the file
        :return: dictionary with file information
        """
        file_path = Path(file_path).resolve()

        stats = os.stat(file_path)
        return {
            'path': str(file_path),
            'name': file_path.name,
            'size': stats.st_size,
            'modified_time': stats.st_mtime,
            'created_time': stats.st_ctime
        }

    @staticmethod
    def list_tree_os_scandir_bfs(directory: str | Path, raise_on_permission_error: bool = False):
        """
        List all files in a directory and its subdirectories using os.scandir and a breadth-first search algorithm.
        :param directory: path to the directory
        :param raise_on_permission_error: if True, raise a PermissionError if a directory cannot be accessed
        :return: generator of file paths
        """
        directory = str(Path(directory).resolve())  # use the absolute path, but convert it to a string to avoid issues
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
    def get_files_and_stats(directory: str | Path, raise_on_permission_error: bool = False) -> List[Dict]:
        """
        Get file information for all files in a directory and its subdirectories. Optimized for speed by not using
        generators and returning a list of dictionaries with file information.
        :param directory: path to the directory
        :param raise_on_permission_error: if True, raise a PermissionError if a directory cannot be accessed
        :return: list of dictionaries with file information
        :raises: PermissionError if a directory cannot be accessed and raise_on_permission_error is True
        """
        files_stats = []
        directory = str(Path(directory).resolve())  # use the absolute path, but convert it to a string to avoid issues
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

    def delete_empty_folders_in_tree(self, base_path: str, show_progress: bool = False,
                                     progress_desc: str = "Looking for empty folders") -> int:
        """
        Delete empty folders in a directory tree
        :param base_path: path to the directory
        :param show_progress: if True, display a progress bar
        :param progress_desc: description for the progress bar
        :return: number of deleted folders
        :raises: ProtectedPathError if the base_path is in a protected directory
        """
        if self.is_protected_path(base_path):
            raise ProtectedPathError(f"Operation not allowed: Attempt to delete empty folders in protected path: "
                                     f"{base_path}")
        if not self.run_mode:
            logger.info(f"Would have deleted empty folders in {base_path}")
            return 0
        folders_by_depth = {}  # collect all folders in the scan_dir folder by depth
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

    @staticmethod
    def any_is_subfolder_of(folders: List[str]) -> Tuple[bool, List[Tuple[str, str]]]:
        """
        Check if any folder is a subfolder of another folder.

        :param folders: list of folder paths
        :return: Tuple containing a boolean and a list of subfolder relationships
        """
        folders = [str(Path(folder).resolve()) for folder in folders]
        subfolder_pairs = []
        for i in range(len(folders)):
            for j in range(len(folders)):
                if i != j and (folders[i].startswith(folders[j] + os.sep) or folders[i] == folders[j]):
                    subfolder_pairs.append((folders[i], folders[j]))
        return bool(subfolder_pairs), subfolder_pairs

    def reset_all(self):
        """Reset the protected_dirs and allowed_dirs to empty sets."""
        self.protected_dirs = set()
        self.allowed_dirs = set()
        return self

    @staticmethod
    def reset_file_manager(protected_dirs: List[str], allowed_dirs: List[str], run_mode: bool = False):
        """
        Reset the file manager with the given protected and allowed directories and run mode.
        :param protected_dirs: List of protected directories
        :param allowed_dirs: List of allowed directories
        :param run_mode: if True, the file operations will be executed, otherwise they will be logged
        :return: FileManager instance
        """
        FileManager._instance = None
        fm = FileManager(run_mode).reset_all()
        for dir_path in protected_dirs:
            fm.add_protected_dir(dir_path)
        for dir_path in allowed_dirs:
            fm.add_allowed_dir(dir_path)
        return fm

    def with_run_mode(self, func, *args, **kwargs):
        """
        Run a function with the run_mode set to True, then reset it to its previous state.
        :param func: function to run
        :param args:
        :param kwargs:
        :return: result of the function
        """
        prev_state = self.run_mode
        self.run_mode = True
        result = func(*args, **kwargs)
        self.run_mode = prev_state
        return result
