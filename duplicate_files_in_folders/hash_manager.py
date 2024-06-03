import pandas as pd
import os
import hashlib
from datetime import datetime, timedelta
import logging
from threading import Lock

logger = logging.getLogger(__name__)


class HashManager:
    """Manages the storage and retrieval of file hashes."""
    _instance = None
    _lock = Lock()

    MAX_CACHE_TIME = 60 * 60 * 24 * 7 * 4  # max cache time, in seconds - 4 weeks
    AUTO_SAVE_THRESHOLD = 10000  # Number of unsaved changes before auto-saving

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.__initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise Exception("HashManager has not been initialized. Please initialize it first.")
        return cls._instance

    @classmethod
    def reset_instance(cls):
        with cls._lock:
            cls._instance = None

    def __init__(self, reference_dir: str = None, filename='hashes.pkl', full_hash=False):
        if self.__initialized:
            return
        self.__initialized = True

        self.filename = filename
        self.reference_dir = reference_dir
        self.full_hash = full_hash
        if not self.full_hash and self.filename is not None:
            self.filename = self.filename.replace('.pkl', '_partial.pkl')

        self.persistent_data = self.load_data()
        self.temporary_data = pd.DataFrame(columns=['file_path', 'hash_value', 'last_update'])
        self.unsaved_changes = 0

        # attributes for cache hits and requests
        self.persistent_cache_hits = 0
        self.persistent_cache_requests = 0
        self.temporary_cache_hits = 0
        self.temporary_cache_requests = 0

    def load_data(self) -> pd.DataFrame:
        """Load only data relevant to the ref folder from the file, or create a new DataFrame if the file doesn't
        exist."""
        if self.filename is None:  # for testing purposes
            return pd.DataFrame(columns=['file_path', 'hash_value', 'last_update'])
        if os.path.exists(self.filename):
            all_data = pd.read_pickle(self.filename)
            if self.reference_dir:
                relevant_data = all_data[all_data['file_path'].str.startswith(self.reference_dir + os.sep)]
                return relevant_data
            return all_data
        else:
            logger.info(f"No existing hash file found. Creating a new one: {self.filename}")
            return pd.DataFrame(columns=['file_path', 'hash_value', 'last_update'])

    @staticmethod
    def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Ensure the DataFrame has the expected columns."""
        expected_columns = ['file_path', 'hash_value', 'last_update']
        for col in expected_columns:
            if col not in df.columns:
                df[col] = pd.NA
        return df

    def save_data(self) -> None:
        """Save the current persistent DataFrame to a file."""
        if self.filename is None:  # for testing purposes
            return
        # Clean expired cache before saving - only for ref folder
        self.clean_expired_cache()

        if os.path.exists(self.filename):
            all_data = pd.read_pickle(self.filename)
            all_data = HashManager.ensure_columns(all_data)

            # Remove old data related to the current ref folder
            all_data = all_data[~all_data['file_path'].str.startswith(self.reference_dir + os.sep)]

            # Drop all-NA rows in all_data and self.persistent_data
            all_data = all_data.dropna(how='all')
            self.persistent_data = self.persistent_data.dropna(how='all')

            # Check if all_data or persistent_data is not empty before concatenation
            if not all_data.empty and not self.persistent_data.empty:
                all_data = pd.concat([all_data, self.persistent_data], ignore_index=True)
            elif not self.persistent_data.empty:
                all_data = self.persistent_data
        else:
            all_data = self.persistent_data if not self.persistent_data.empty else pd.DataFrame(
                columns=['file_path', 'hash_value', 'last_update'])

        all_data.to_pickle(self.filename)
        self.unsaved_changes = 0

    def add_hash(self, file_path: str, hash_value: str) -> None:
        """Add a new hash to the appropriate DataFrame."""
        current_time = datetime.now()
        new_entry = pd.DataFrame({'file_path': [file_path], 'hash_value': [hash_value], 'last_update': [current_time]})

        if self.reference_dir and file_path.startswith(self.reference_dir + os.sep):
            if not self.persistent_data.empty:
                # Remove the existing entry if it exists
                self.persistent_data = self.persistent_data[self.persistent_data.file_path != file_path]
                # Add the new entry
                self.persistent_data = pd.concat([self.persistent_data, new_entry], ignore_index=True)
            else:
                self.persistent_data = new_entry
            self.unsaved_changes += 1
            if self.unsaved_changes >= self.AUTO_SAVE_THRESHOLD:
                self.save_data()
        else:
            if not self.temporary_data.empty:
                # Remove the existing entry if it exists
                self.temporary_data = self.temporary_data[self.temporary_data.file_path != file_path]
                # Add the new entry
                self.temporary_data = pd.concat([self.temporary_data, new_entry], ignore_index=True)
            else:
                self.temporary_data = new_entry

    def get_hash(self, file_path: str) -> str:
        """Get the hash of a file, computing and storing it if necessary."""
        if self.reference_dir and file_path.startswith(self.reference_dir + os.sep):
            self.persistent_cache_requests += 1  # Increment persistent cache requests
            result = self.persistent_data[self.persistent_data.file_path == file_path]
        else:
            self.temporary_cache_requests += 1  # Increment temporary cache requests
            result = self.temporary_data[self.temporary_data.file_path == file_path]

        # Check if the hash is already stored and not expired
        if not result.empty:
            current_time = datetime.now()
            last_update = result['last_update'].values[0]
            if pd.Timestamp(last_update) > current_time - timedelta(seconds=self.MAX_CACHE_TIME):
                if self.reference_dir and file_path.startswith(self.reference_dir + os.sep):
                    self.persistent_cache_hits += 1  # Increment persistent cache hits
                else:
                    self.temporary_cache_hits += 1  # Increment temporary cache hits
                return result['hash_value'].values[0]
        hash_value = self.compute_hash(file_path)
        self.add_hash(file_path, hash_value)
        return hash_value

    def get_hashes_by_folder(self, folder_path: str) -> dict:
        """
        Get all hashes stored in the cache for a folder, checking both persistent and temporary data.
        :param folder_path: path to the folder
        :return: a dictionary with the file paths and hash values.
        """
        persistent_result = self.persistent_data[self.persistent_data.file_path.str.startswith(folder_path + os.sep)]
        temporary_result = self.temporary_data[self.temporary_data.file_path.str.startswith(folder_path + os.sep)]
        if persistent_result.empty and temporary_result.empty:
            result = pd.DataFrame(columns=['file_path', 'hash_value'])
        else:
            result = pd.concat([persistent_result, temporary_result])
        return result[['file_path', 'hash_value']].to_dict(orient='records')

    def clear_cache(self) -> None:
        """Clean all cache files."""
        self.persistent_data = pd.DataFrame(columns=['file_path', 'hash_value', 'last_update'])
        self.temporary_data = pd.DataFrame(columns=['file_path', 'hash_value', 'last_update'])
        logger.info("Cache cleaned. All data removed.")

    def clean_expired_cache(self) -> None:
        """
        Clean the cache of expired items. Only cleans the persistent data. It doesn't save the data to the file.
        """
        current_time = datetime.now()
        expired_files = self.persistent_data[
            (self.persistent_data.last_update < current_time - timedelta(seconds=self.MAX_CACHE_TIME))
        ]
        expired_files_count = len(expired_files)
        self.persistent_data = self.persistent_data.drop(expired_files.index)
        if expired_files_count > 0:
            logger.info(f"{expired_files_count} expired cache items cleaned.")

    def compute_hash(self, file_path: str, buffer_size=8*1024*1024) -> str:
        """
        Compute the hash of a file by reading it in chunks. User should not call this method directly but use get_hash()
        :param file_path: path to the file
        :param buffer_size: size of the buffer to read the file
        :return: the hash of the file
        :raises: Exception if there is an error hashing the file. Should not happen in normal circumstances.
        """
        if not self.full_hash:
            return HashManager.compute_partial_hash(file_path)
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
            raise

    @staticmethod
    def compute_partial_hash(file_path: str, initial_bytes=2 * 1024 * 1024) -> str:
        """
        Compute the hash of the first initial_bytes of a file.
        :param file_path: path to the file
        :param initial_bytes: number of bytes to read from the file
        :return: the hash of the file based on the initial_bytes
        """
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as file:
                buffer = file.read(initial_bytes)
                hasher.update(buffer)
            file_hash = hasher.hexdigest()
            return file_hash
        except Exception as e:
            logger.error(f"Error hashing {file_path}: {e}")
            raise

    def print_state(self):
        """Print the state of the HashManager. For debugging purposes."""
        logger.info(f"Persistent data:\n{self.persistent_data}")
        logger.info(f"Temporary data:\n{self.temporary_data}")
        logger.info(f"Persistent cache hits: {self.persistent_cache_hits}")
        logger.info(f"Persistent cache requests: {self.persistent_cache_requests}")
        logger.info(f"Temporary cache hits: {self.temporary_cache_hits}")
        logger.info(f"Temporary cache requests: {self.temporary_cache_requests}")
