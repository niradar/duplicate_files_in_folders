import pandas as pd
import os
import hashlib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class HashManager:
    """Manages the storage and retrieval of file hashes."""

    MAX_CACHE_TIME = 60 * 60 * 24 * 14  # max cache time, in seconds - 2 weeks
    AUTO_SAVE_THRESHOLD = 10  # Number of unsaved changes before auto-saving

    def __init__(self, target_folder: str = None, filename: str = 'hashes.pkl'):
        """Initialize HashManager with the filename to store hashes."""
        self.filename = filename
        self.target_folder = target_folder
        self.persistent_data = self.load_data()
        self.temporary_data = pd.DataFrame(columns=['file_path', 'hash_value', 'last_update'])
        self.unsaved_changes = 0

    def load_data(self) -> pd.DataFrame:
        """Load data from the file, or create a new DataFrame if the file doesn't exist."""
        if os.path.exists(self.filename):
            return pd.read_pickle(self.filename)
        else:
            logger.info(f"No existing hash file found. Creating a new one: {self.filename}")
            return pd.DataFrame(columns=['file_path', 'hash_value', 'last_update'])

    def save_data(self) -> None:
        """Save the current persistent DataFrame to a file."""
        self.persistent_data.to_pickle(self.filename)
        self.unsaved_changes = 0

    def add_hash(self, file_path: str, hash_value: str) -> None:
        """Add a new hash to the appropriate DataFrame."""
        current_time = datetime.now()
        new_entry = pd.DataFrame({'file_path': [file_path], 'hash_value': [hash_value], 'last_update': [current_time]})

        if self.target_folder and file_path.startswith(self.target_folder):
            if not self.persistent_data.empty:
                self.persistent_data = pd.concat([self.persistent_data[self.persistent_data.file_path != file_path],
                                                  new_entry], ignore_index=True)
            else:
                self.persistent_data = new_entry
            self.unsaved_changes += 1
            if self.unsaved_changes >= self.AUTO_SAVE_THRESHOLD:
                self.save_data()
        else:
            if not self.temporary_data.empty:
                self.temporary_data = pd.concat([self.temporary_data[self.temporary_data.file_path != file_path],
                                                 new_entry], ignore_index=True)
            else:
                self.temporary_data = new_entry

    def get_hash(self, file_path: str) -> str:
        """Get the hash of a file, computing and storing it if necessary."""
        if self.target_folder and file_path.startswith(self.target_folder):
            result = self.persistent_data[self.persistent_data.file_path == file_path]
        else:
            result = self.temporary_data[self.temporary_data.file_path == file_path]

        if not result.empty:
            return result['hash_value'].values[0]
        else:
            hash_value = self.compute_hash(file_path)
            self.add_hash(file_path, hash_value)
            return hash_value

    def get_hashes_by_folder(self, folder_path: str) -> dict:
        """Get all hashes for files in a specific folder, checking both persistent and temporary data."""
        persistent_result = self.persistent_data[self.persistent_data.file_path.str.startswith(folder_path)]
        temporary_result = self.temporary_data[self.temporary_data.file_path.str.startswith(folder_path)]
        if persistent_result.empty and temporary_result.empty:
            result = pd.DataFrame(columns=['file_path', 'hash_value'])
        else:
            result = pd.concat([persistent_result, temporary_result])
        return result[['file_path', 'hash_value']].to_dict(orient='records')

    def clean_cache(self) -> None:
        """Clean all cache files."""
        self.persistent_data = pd.DataFrame(columns=['file_path', 'hash_value', 'last_update'])
        self.temporary_data = pd.DataFrame(columns=['file_path', 'hash_value', 'last_update'])
        logger.info("Cache cleaned. All data removed.")

    def clean_expired_cache(self) -> None:
        """Clean cache files that have expired."""
        current_time = datetime.now()
        expired_files = self.temporary_data[
            (self.temporary_data.last_update < current_time - timedelta(seconds=self.MAX_CACHE_TIME))
        ]
        self.temporary_data = self.temporary_data.drop(expired_files.index)
        logger.info("Expired cache cleaned.")

    @staticmethod
    def compute_hash(file_path: str, buffer_size=8*1024*1024) -> str:
        """Method to compute the hash of a file."""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as file:
                buffer = file.read(buffer_size)
                while buffer:
                    hasher.update(buffer)
                    buffer = file.read(buffer_size)
            file_hash = hasher.hexdigest()
            return file_hash
        except Exception as e:
            logger.error(f"Error hashing {file_path}: {e}")
            return ""


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = HashManager(target_folder='/path/to/target')
    manager.add_hash('/path/to/target/file1.txt', 'hash1')
    manager.add_hash('/path/to/temp/file2.txt', 'hash2')
    print(manager.get_hash('/path/to/target/file1.txt'))
    manager.clean_cache()
    manager.clean_expired_cache()
    manager.save_data()
