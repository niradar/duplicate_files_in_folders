from pathlib import Path
import shutil
import os


class FileManagerError(Exception):
    pass


class ProtectedPathError(FileManagerError):
    def __init__(self, message):
        super().__init__(message)


class FileManager:
    _instance = None
    protected_dirs = set()
    allowed_dirs = set()  # If set, only operations in these directories are allowed. Acts as a whitelist

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FileManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def add_protected_dir(self, dir_path):
        protected_dir = Path(dir_path).resolve()

        # raise an error if the directory is already in the allowed_dirs
        if self.allowed_dirs and protected_dir in self.allowed_dirs:
            raise FileManagerError(f"Attempt to protect a directory that is also in the allowed_dirs: {dir_path}")

        if protected_dir not in self.protected_dirs:
            self.protected_dirs.add(protected_dir)

    def add_allowed_dir(self, dir_path):
        allowed_dir = Path(dir_path).resolve()

        # raise an error if the directory is already in the protected_dirs
        if self.protected_dirs and allowed_dir in self.protected_dirs:
            raise FileManagerError(f"Attempt to allow a directory that is also in the protected_dirs: {dir_path}")

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

        shutil.move(src_path, dst_path)
        return True

    def copy_file(self, src, dst):
        src_path = Path(src).resolve()
        dst_path = Path(dst).resolve()

        if self.is_protected_path(dst_path):
            raise ProtectedPathError(
                f"Operation not allowed: Attempt to copy file to protected directory: {src} -> {dst}")

        shutil.copy2(src_path, dst_path)
        return True

    def delete_file(self, file_path):
        file_path = Path(file_path).resolve()

        if self.is_protected_path(file_path):
            raise ProtectedPathError(f"Operation not allowed: Attempt to delete protected file: {file_path}")

        os.remove(file_path)
        return True

    def make_dirs(self, dir_path):
        dir_path = Path(dir_path).resolve()

        if self.is_protected_path(dir_path):
            raise ProtectedPathError(f"Operation not allowed: Attempt to create directory in protected path: "
                                     f"{dir_path}")

        os.makedirs(dir_path)
        return True

    def rmdir(self, dir_path):
        dir_path = Path(dir_path).resolve()

        if self.is_protected_path(dir_path):
            raise ProtectedPathError(f"Operation not allowed: Attempt to delete protected directory: {dir_path}")

        os.rmdir(dir_path)
        return True

    def reset_protected_dirs(self):
        self.protected_dirs = set()
        return self

    def reset_allowed_dirs(self):
        self.allowed_dirs = set()
        return self

    def reset_all(self):
        self.reset_protected_dirs()
        self.reset_allowed_dirs()
        return self
