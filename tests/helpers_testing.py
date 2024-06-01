import logging

import pytest
import os
import shutil

from duplicate_files_in_folders.hash_manager import HashManager
from duplicate_files_in_folders.logging_config import setup_logging
from duplicate_files_in_folders import file_manager

logger = logging.getLogger(__name__)

# Define the base directory for the tests
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the directory containing the image files
IMG_DIR = os.path.join(BASE_DIR, "imgs")

# Define a temporary directory for the tests
TEMP_DIR = os.path.join(BASE_DIR, "temp")

img_files = {1: {'extension': 'jpg', 'original_name': '20220517_155135.jpg'},
             2: {'extension': 'jpg', 'original_name': '20220517_210649.jpg'},
             3: {'extension': 'jpg', 'original_name': '20220518_131321.jpg'},
             4: {'extension': 'jpg', 'original_name': '20220518_134457.jpg'},
             5: {'extension': 'jpg', 'original_name': '20220519_173242.jpg'},
             6: {'extension': 'jpg', 'original_name': '20220520_101634.jpg'},
             7: {'extension': 'jpg', 'original_name': '20220520_121350.jpg'},
             8: {'extension': 'jpg', 'original_name': '20220521_151948.jpg'},
             9: {'extension': 'jpg', 'original_name': '20220522_100459.jpg'},
             10: {'extension': 'jpg', 'original_name': '20220522_112904.jpg'},
             11: {'extension': 'jpg', 'original_name': '20220522_122209.jpg'},
             12: {'extension': 'jpg', 'original_name': '20220522_190921.jpg'},
             13: {'extension': 'jpg', 'original_name': '20220523_163609.jpg'},
             14: {'extension': 'jpg', 'original_name': '20220523_171239.jpg'},
             15: {'extension': 'jpg', 'original_name': '20220524_130612.jpg'},
             16: {'extension': 'jpg', 'original_name': '20220524_140930.jpg'},
             17: {'extension': 'jpg', 'original_name': '20220526_095346.jpg'},
             18: {'extension': 'jpg', 'original_name': '20220526_110008.jpg'},
             19: {'extension': 'jpg', 'original_name': '20220526_110219.jpg'},
             20: {'extension': 'jpg', 'original_name': '20220526_114651.jpg'}}


# get fake folder path based on the os. It can accept subfolders as well in the format 'folder/subfolder'
def get_folder_path(folder):
    subfolder = folder.split('/')
    res = 'C:\\Users\\user\\Desktop\\' if os.name == 'nt' else '/path/to/'

    for i in range(len(subfolder)):
        res += subfolder[i] + os.sep
    return res[:-1]


def copy_files(file_numbers, src_dir):
    for file_number in file_numbers:
        src_file = os.path.join(IMG_DIR, f"{file_number}.jpg")
        dst_file = os.path.join(src_dir, f"{file_number}.jpg")
        shutil.copy(src_file, dst_file)


@pytest.fixture
def setup_teardown():
    setup_logging()
    # Setup: Create the temporary directories
    source_dir = os.path.join(TEMP_DIR, "source")
    target_dir = os.path.join(TEMP_DIR, "target")
    move_to_dir = os.path.join(TEMP_DIR, "move_to")
    hash_file = os.path.join(TEMP_DIR, "hashes.pkl")
    common_args = ["--src", source_dir, "--target", target_dir, "--move_to", move_to_dir, "--run"]
    # Reset the singleton instance
    HashManager.reset_instance()
    HashManager(target_folder=target_dir, filename=hash_file)

    # change file_manager.FileManager.reset_file_manager() to the new arguments
    file_manager.FileManager.reset_file_manager([target_dir], [source_dir, move_to_dir], True)

    os.makedirs(source_dir)
    os.makedirs(target_dir)
    os.makedirs(move_to_dir)

    yield source_dir, target_dir, move_to_dir, common_args

    # Teardown: Delete the temporary directories
    shutil.rmtree(TEMP_DIR)


def setup_test_files(source_files, target_files):
    copy_files(source_files, os.path.join(TEMP_DIR, "source"))
    copy_files(target_files, os.path.join(TEMP_DIR, "target"))


def get_folder_structure_include_subfolders(folder):
    folder = os.path.abspath(folder)
    tree = []

    def recurse_folder(current_folder, indent=""):
        for item in os.listdir(current_folder):
            item_path = os.path.join(current_folder, item)
            if os.path.isdir(item_path):
                tree.append(f"{indent}├── {item}/")
                recurse_folder(item_path, indent + "│   ")
            else:
                tree.append(f"{indent}├── {item}")

    tree.append(f"{folder}/")
    recurse_folder(folder)
    return "\n" + "\n".join(tree)


def print_all_folders(source_dir, target_dir, move_to_dir):
    logger.info(f"Source directory structure: {get_folder_structure_include_subfolders(source_dir)}")
    logger.info(f"Target directory structure: {get_folder_structure_include_subfolders(target_dir)}")
    logger.info(f"Move_to directory structure: {get_folder_structure_include_subfolders(move_to_dir)}")


def simple_usecase_test(source_dir, target_dir, move_to_dir, max_files=3):
    # Check if all files from source are now in base folder of move_to
    source_files = set(os.listdir(source_dir))
    assert not source_files, "Source directory is not empty"
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == set(
        [f"{i}.jpg" for i in range(1, max_files+1)]), "Not all files have been moved to move_to directory"

    # Check no change to target
    target_files = set(os.listdir(target_dir))
    assert target_files == set([f"{i}.jpg" for i in range(1, max_files+1)]), "Target directory files have changed"


def check_folder_conditions(base_dir, conditions):
    def get_all_files_and_dirs(directory):
        """ Get all files and directories in a directory, including subdirectories """
        all_files = []
        all_dirs = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                all_files.append(os.path.relpath(str(os.path.join(root, file)), base_dir))
            for dir in dirs:
                all_dirs.append(os.path.relpath(str(os.path.join(root, dir)), base_dir))
        return all_files, all_dirs

    def count_occurrences(file_list, name):
        """ Count the occurrences of a file or directory in a list """
        return sum(1 for item in file_list if os.path.basename(item) == name)

    def check_required_subdirs(parent_folder, required_subdirs, expected_count):
        """ Check that exactly expected_count of required_subdirs exist in parent_folder """
        actual_subdirs = [d for d in os.listdir(str(os.path.join(base_dir, parent_folder))) if os.path.isdir(os.path.join(base_dir, parent_folder, d))]
        actual_count = sum(1 for subdir in required_subdirs if subdir in actual_subdirs)
        return actual_count == expected_count

    def check_items_in_folder(folder, items):
        """ Check that all items in the list exist in the specified folder """
        actual_items = set(os.listdir(str(os.path.join(base_dir, folder))))
        return set(items).issubset(actual_items)

    def count_files_including_subfolders(folder):
        """ Count all files in a folder including its subdirectories """
        total_files = 0
        for root, dirs, files in os.walk(os.path.join(base_dir, folder)):
            total_files += len(files)
        return total_files

    all_files, all_dirs = get_all_files_and_dirs(base_dir)

    for condition in conditions:
        if condition['type'] == 'file_count':
            folder_set = condition['folders']
            file_name = condition['file']
            expected_count = condition['count']
            include_subfolders = condition.get('include_subfolders', True)

            # Filter files based on the folder condition
            if include_subfolders:
                filtered_files = [file for file in all_files if any(file.startswith(folder) for folder in folder_set)]
            else:
                filtered_files = [file for file in all_files if
                                  any(os.path.dirname(file) == folder for folder in folder_set)]

            # Count occurrences of the file
            actual_count = count_occurrences(filtered_files, file_name)

            assert actual_count == expected_count, f"{file_name} appears {actual_count} times, expected {expected_count} times in {folder_set}"

        elif condition['type'] == 'dir_structure':
            parent_folder = condition['parent_folder']
            expected_subdirs = condition['subdirs']

            # Get actual subdirectories in the parent folder
            actual_subdirs = [os.path.relpath(os.path.join(parent_folder, d), base_dir) for d in
                              os.listdir(str(os.path.join(base_dir, parent_folder))) if
                              os.path.isdir(os.path.join(base_dir, parent_folder, d))]

            # Check if the actual subdirectories match the expected ones
            assert set(actual_subdirs) == set(
                expected_subdirs), f"Subdirectories in {parent_folder} are {actual_subdirs}, expected {expected_subdirs}"

        elif condition['type'] == 'count_files_dirs':
            folder = condition['folder']
            expected_file_count = condition['file_count']
            expected_dir_count = condition['dir_count']

            # Count files and directories in the specified folder
            actual_files = [file for file in all_files if file.startswith(folder)]
            actual_dirs = [dir for dir in all_dirs if dir.startswith(folder)]

            actual_file_count = len(actual_files)
            actual_dir_count = len(actual_dirs)

            assert actual_file_count == expected_file_count, f"File count in {folder} is {actual_file_count}, expected {expected_file_count}"
            assert actual_dir_count == expected_dir_count, f"Directory count in {folder} is {actual_dir_count}, expected {expected_dir_count}"

        elif condition['type'] == 'subdirs_count':
            parent_folder = condition['parent_folder']
            required_subdirs = condition['required_subdirs']
            expected_count = condition['expected_count']

            assert check_required_subdirs(parent_folder, required_subdirs, expected_count), f"{expected_count} out of {required_subdirs} should exist in {parent_folder}"

        elif condition['type'] == 'items_in_folder':
            folder = condition['folder']
            items = condition['items']

            assert check_items_in_folder(folder, items), f"Items {items} should exist in {folder}"

        elif condition['type'] == 'files_count_including_subfolders':
            folder = condition['folder']
            expected_count = condition['expected_count']

            actual_count = count_files_including_subfolders(folder)
            assert actual_count == expected_count, f"Total file count in {folder} including subdirectories is {actual_count}, expected {expected_count}"

    return True


def check_folder_conditions_example():
    move_to_dir = "/path/to/move_to_dir"
    conditions = [
        {
            'type': 'file_count',
            'folders': {'source_dups/sub1', 'source_dups/sub2', 'source_dups/sub3'},
            'file': 'file1.jpg',
            'count': 2,
            'include_subfolders': True
        },
        {
            'type': 'file_count',
            'folders': {'source_dups/sub1', 'source_dups/sub3'},
            'file': 'file4.jpg',
            'count': 2,
            'include_subfolders': False
        },
        {
            'type': 'file_count',
            'folders': {'Y'},
            'file': 'specific_file.jpg',
            'count': 1,
            'include_subfolders': True
        },
        {
            'type': 'dir_structure',
            'parent_folder': 'source_dups',
            'subdirs': {'sub1', 'sub2', 'sub3'}
        },
        {
            'type': 'count_files_dirs',
            'folder': 'some_folder',
            'file_count': 10,
            'dir_count': 2
        },
        {
            'type': 'subdirs_count',
            'parent_folder': 'source_dups',
            'required_subdirs': {'sub1', 'sub2', 'sub3', 'sub4'},
            'expected_count': 2
        },
        {
            'type': 'items_in_folder',
            'folder': 'some_folder',
            'items': {'file1.txt', 'file2.txt', 'subfolder1'}
        },
        {
            'type': 'files_count_including_subfolders',
            'folder': 'some_folder',
            'expected_count': 10
        }
    ]

    check_folder_conditions(os.path.join(move_to_dir, "source_dups"), conditions)
