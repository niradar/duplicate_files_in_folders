import pytest
import os
import shutil
import pandas as pd
from datetime import datetime, timedelta
from hash_manager import HashManager  # Assuming your class is in a file named hash_manager.py

TEMP_DIR = "temp_test_dir"


@pytest.fixture
def setup_teardown_hash_manager():
    # Reset the singleton instance
    HashManager.reset_instance()

    # Setup: Create the temporary directories
    target_dir = os.path.join(TEMP_DIR, "target")
    hash_file = os.path.join(TEMP_DIR, "hashes.pkl")
    os.makedirs(target_dir, exist_ok=True)

    hm = HashManager(target_folder=target_dir, filename=hash_file)

    yield hm, target_dir, hash_file

    # Teardown: Delete the temporary directories
    shutil.rmtree(TEMP_DIR)


def test_add_and_get_hash(setup_teardown_hash_manager):
    hash_manager, _, _ = setup_teardown_hash_manager
    file_path = os.path.join(hash_manager.target_folder, "file1.txt")
    with open(file_path, 'w') as f:
        f.write("test content")
    hash_value = hash_manager.compute_hash(file_path)
    hash_manager.add_hash(file_path, hash_value)
    assert hash_manager.get_hash(file_path) == hash_value


def test_get_hash_computes_if_missing(setup_teardown_hash_manager):
    hash_manager, target_dir, _ = setup_teardown_hash_manager
    file_path = os.path.join(target_dir, "file2.txt")
    with open(file_path, 'w') as f:
        f.write("test content")
    computed_hash_value = hash_manager.compute_hash(file_path)
    assert hash_manager.get_hash(file_path) == computed_hash_value


def test_auto_save_threshold(setup_teardown_hash_manager):
    hash_manager, target_dir, hash_file = setup_teardown_hash_manager
    prev_threshold = hash_manager.AUTO_SAVE_THRESHOLD
    hash_manager.AUTO_SAVE_THRESHOLD = 5
    for i in range(hash_manager.AUTO_SAVE_THRESHOLD):
        file_path = os.path.join(target_dir, f"file{i}.txt")
        with open(file_path, 'w') as f:
            f.write(f"test content {i}")
        hash_manager.add_hash(file_path, hash_manager.compute_hash(file_path))

    # Check that the file is saved after the threshold is exceeded
    assert os.path.exists(hash_file)
    saved_data = pd.read_pickle(hash_file)
    assert len(saved_data) == hash_manager.AUTO_SAVE_THRESHOLD

    hash_manager.AUTO_SAVE_THRESHOLD = prev_threshold


def test_clean_cache(setup_teardown_hash_manager):
    hash_manager, target_dir, _ = setup_teardown_hash_manager
    file_path = os.path.join(target_dir, "file1.txt")
    with open(file_path, 'w') as f:
        f.write("test content")
    hash_manager.add_hash(file_path, hash_manager.compute_hash(file_path))
    hash_manager.clear_cache()
    assert hash_manager.persistent_data.empty
    assert hash_manager.temporary_data.empty


def test_clean_expired_cache(setup_teardown_hash_manager):
    hash_manager, target_dir, _ = setup_teardown_hash_manager
    file_path = os.path.join(target_dir, "file1.txt")
    with open(file_path, 'w') as f:
        f.write("test content")
    hash_manager.add_hash(file_path, hash_manager.compute_hash(file_path))
    hash_manager.temporary_data.at[0, 'last_update'] = (datetime.now() -
                                                        timedelta(seconds=hash_manager.MAX_CACHE_TIME + 1))
    hash_manager.clean_expired_cache()
    assert hash_manager.temporary_data.empty


def test_get_hashes_by_folder(setup_teardown_hash_manager):
    hash_manager, target_dir, _ = setup_teardown_hash_manager
    file_path1 = os.path.join(target_dir, "file1.txt")
    file_path2 = os.path.join(target_dir, "file2.txt")
    file_path3 = os.path.join(TEMP_DIR, "file3.txt")
    with open(file_path1, 'w') as f:
        f.write("test content 1")
    with open(file_path2, 'w') as f:
        f.write("test content 2")
    with open(file_path3, 'w') as f:
        f.write("test content 3")
    hash_manager.add_hash(file_path1, hash_manager.compute_hash(file_path1))
    hash_manager.add_hash(file_path2, hash_manager.compute_hash(file_path2))
    hash_manager.add_hash(file_path3, hash_manager.compute_hash(file_path3))
    hashes = hash_manager.get_hashes_by_folder(hash_manager.target_folder)
    assert len(hashes) == 2


def test_several_files_same_hash(setup_teardown_hash_manager):
    hash_manager, _, _ = setup_teardown_hash_manager
    file_path1 = os.path.join(hash_manager.target_folder, "file1.txt")
    file_path2 = os.path.join(hash_manager.target_folder, "file2.txt")
    with open(file_path1, 'w') as f:
        f.write("test content")
    with open(file_path2, 'w') as f:
        f.write("test content")
    hash_value = hash_manager.compute_hash(file_path1)
    hash_manager.add_hash(file_path1, hash_value)
    hash_manager.add_hash(file_path2, hash_value)
    assert hash_manager.get_hash(file_path1) == hash_value
    assert hash_manager.get_hash(file_path2) == hash_value


def test_file_not_found(setup_teardown_hash_manager):
    hash_manager, _, _ = setup_teardown_hash_manager
    with pytest.raises(FileNotFoundError):
        hash_manager.get_hash("non_existent_file.txt")


def test_clean_cache_with_data(setup_teardown_hash_manager):
    hash_manager, target_dir, _ = setup_teardown_hash_manager
    file_path = os.path.join(target_dir, "file1.txt")
    with open(file_path, 'w') as f:
        f.write("test content")
    hash_manager.add_hash(file_path, hash_manager.compute_hash(file_path))
    hash_manager.clear_cache()
    assert hash_manager.persistent_data.empty
    assert hash_manager.temporary_data.empty


if __name__ == "__main__":
    pytest.main()
