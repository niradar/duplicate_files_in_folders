import pytest
import os
import shutil

from hash_manager import HashManager
from logging_config import setup_logging
import file_manager

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
