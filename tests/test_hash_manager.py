import pytest
import os
import shutil
import pandas as pd
from datetime import datetime, timedelta
from duplicate_files_in_folders.hash_manager import HashManager
import logging

TEMP_DIR = "temp_test_dir"

logger = logging.getLogger(__name__)

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
    hash_manager.persistent_data.at[0, 'last_update'] = (datetime.now() -
                                                        timedelta(seconds=hash_manager.MAX_CACHE_TIME + 1))
    hash_manager.clean_expired_cache()
    assert hash_manager.persistent_data.empty


def test_clean_expired_cache_mixed_data(setup_teardown_hash_manager):
    hash_manager, target_dir, _ = setup_teardown_hash_manager
    file_path1 = os.path.join(target_dir, "file1.txt")
    file_path2 = os.path.join(target_dir, "file2.txt")
    with open(file_path1, 'w') as f:
        f.write("test content")
    with open(file_path2, 'w') as f:
        f.write("test content")
    hash_manager.add_hash(file_path1, hash_manager.compute_hash(file_path1))
    hash_manager.add_hash(file_path2, hash_manager.compute_hash(file_path2))
    hash_manager.persistent_data.at[0, 'last_update'] = (datetime.now() -
                                                         timedelta(seconds=hash_manager.MAX_CACHE_TIME + 1))
    hash_manager.clean_expired_cache()
    assert len(hash_manager.temporary_data) == 0
    assert len(hash_manager.persistent_data) == 1
    assert hash_manager.persistent_data.at[1, 'file_path'] == file_path2


# when saving to file, the script should clear expired data but only in the target folder.
# run once with target folder. put 2 files there. run second time with target2 folder, put 2 files there -
# one expired and one not. Save to file. Load from file. Make sure only the non-expired file is in the data and
# also that target folder is in the file
def test_clean_expired_cache_mixed_data_2_targets(setup_teardown_hash_manager):

    # create target content
    hash_manager, target_dir, _ = setup_teardown_hash_manager
    file_path1 = os.path.join(target_dir, "file1.txt")
    file_path2 = os.path.join(target_dir, "file2.txt")
    with open(file_path1, 'w') as f:
        f.write("test content1")
    with open(file_path2, 'w') as f:
        f.write("test content2")

    # create target2 content
    target2_dir = os.path.join(TEMP_DIR, "target2")
    os.makedirs(target2_dir, exist_ok=True)
    file_path3 = os.path.join(target2_dir, "file3.txt")
    file_path4 = os.path.join(target2_dir, "file4.txt")
    with open(file_path3, 'w') as f:
        f.write("test content3")
    with open(file_path4, 'w') as f:
        f.write("test content4")

    # save target to file using default hash_manager
    hash_manager.add_hash(file_path1, hash_manager.compute_hash(file_path1))
    hash_manager.add_hash(file_path2, hash_manager.compute_hash(file_path2))
    hash_manager.save_data()

    # new hash_manager with target2
    HashManager.reset_instance()
    hash_file = os.path.join(TEMP_DIR, "hashes.pkl")
    hash_manager2 = HashManager(target_folder=target2_dir, filename=hash_file)
    assert len(hash_manager2.persistent_data) == 0, "Should not have any data - target2 is empty"

    # test loading target again
    HashManager.reset_instance()
    hash_manager = HashManager(target_folder=target_dir, filename=hash_file)
    assert len(hash_manager.persistent_data) == 2, f"hm.persistent_data: {hash_manager.persistent_data}"

    # back to new hash_manager with target2
    HashManager.reset_instance()
    hash_file = os.path.join(TEMP_DIR, "hashes.pkl")
    hash_manager2 = HashManager(target_folder=target2_dir, filename=hash_file)
    assert len(hash_manager2.persistent_data) == 0, "Should not have any data - target2 is empty"

    hash_manager2.add_hash(file_path3, hash_manager2.compute_hash(file_path3))
    hash_manager2.add_hash(file_path4, hash_manager2.compute_hash(file_path4))

    for item in hash_manager2.persistent_data['file_path']:
        if item == file_path3:
            hash_manager2.persistent_data.at[0, 'last_update'] = (datetime.now() -
                                                                 timedelta(seconds=hash_manager2.MAX_CACHE_TIME + 1))

    hash_manager2.save_data()
    assert len(hash_manager2.persistent_data) == 1, f"hm.persistent_data: {hash_manager.persistent_data}"

    HashManager.reset_instance()
    hash_manager2 = HashManager(target_folder=target2_dir, filename=hash_file)
    assert len(hash_manager2.persistent_data) == 1
    assert file_path4 in hash_manager2.persistent_data['file_path'].values

    # make sure the target folder is in the file
    HashManager.reset_instance()
    hash_manager = HashManager(target_folder=target_dir, filename=hash_file)
    assert len(hash_manager.persistent_data) == 2


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


# make sure the script don't use expired cache
def test_clean_expired_cache_with_data(setup_teardown_hash_manager):
    hash_manager, target_dir, _ = setup_teardown_hash_manager
    file_path = os.path.join(target_dir, "file1.txt")
    with open(file_path, 'w') as f:
        f.write("test content")
    hash_manager.add_hash(file_path, 'fake_hash_value')
    hash_manager.persistent_data.at[0, 'last_update'] = (datetime.now() -
                                                         timedelta(seconds=hash_manager.MAX_CACHE_TIME + 1))
    assert hash_manager.persistent_data.at[0, 'last_update'] < datetime.now() - timedelta(seconds=hash_manager.MAX_CACHE_TIME)

    # make sure the script don't use expired cache and compute the hash again
    assert hash_manager.get_hash(file_path) != 'fake_hash_value'


# save 4 data items in pd, save to file. second time load from file, then touch 2 items, save to file, load from file
# make sure 4 items are in the file
def test_save_load_data(setup_teardown_hash_manager):
    hash_manager, target_dir, hash_file = setup_teardown_hash_manager
    file_path1 = os.path.join(target_dir, "file1.txt")
    file_path2 = os.path.join(target_dir, "file2.txt")
    file_path3 = os.path.join(target_dir, "file3.txt")
    file_path4 = os.path.join(target_dir, "file4.txt")
    with open(file_path1, 'w') as f:
        f.write("test content")
    with open(file_path2, 'w') as f:
        f.write("test content2")
    with open(file_path3, 'w') as f:
        f.write("test content3")
    with open(file_path4, 'w') as f:
        f.write("test content4")
    hash_manager.add_hash(file_path1, hash_manager.compute_hash(file_path1))
    hash_manager.add_hash(file_path2, hash_manager.compute_hash(file_path2))
    hash_manager.add_hash(file_path3, hash_manager.compute_hash(file_path3))
    hash_manager.add_hash(file_path4, hash_manager.compute_hash(file_path4))
    hash_manager.save_data()

    # load from file
    HashManager.reset_instance()
    hash_manager = HashManager(target_folder=target_dir, filename=hash_file)
    assert len(hash_manager.persistent_data) == 4

    # touch 2 items
    hash_manager.add_hash(file_path1, hash_manager.compute_hash(file_path1))
    hash_manager.add_hash(file_path2, hash_manager.compute_hash(file_path2))
    hash_manager.save_data()

    # load from file
    HashManager.reset_instance()
    hash_manager = HashManager(target_folder=target_dir, filename=hash_file)
    assert len(hash_manager.persistent_data) == 4


if __name__ == "__main__":
    pytest.main()
