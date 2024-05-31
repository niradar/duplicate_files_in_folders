from duplicate_files_in_folders.duplicates_finder import get_file_key
from duplicate_files_in_folders.file_manager import FileManager
from duplicate_files_in_folders.utils import parse_arguments
from tests.helpers_testing import *


def test_get_file_key(setup_teardown):
    source_dir, target_dir, move_to_dir, _ = setup_teardown
    setup_test_files(range(1, 6), range(1, 6))

    file_info = FileManager.get_file_info(os.path.join(source_dir, "1.jpg"))

    # default args are to ignore mdate
    common_args = ["--src", source_dir, "--target", target_dir, "--move_to", move_to_dir, "--run"]
    args = parse_arguments(common_args)
    key = get_file_key(args, file_info['path'])
    assert key == 'edb36987f4e3526039ff5c174bcebb9513d95dbc235fb093806c8387dc9ffa91_1.jpg'

    # ignore filename
    common_args = ["--src", source_dir, "--target", target_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "filename"]
    args = parse_arguments(common_args)
    key = get_file_key(args, file_info['path'])
    # split key to hash and the rest
    key_parts = key.split('_')
    assert key_parts[0] == 'edb36987f4e3526039ff5c174bcebb9513d95dbc235fb093806c8387dc9ffa91'
    # assert second part is str(os.path.getmtime(file_path)) which is the modified date
    assert key_parts[1] is not None
    assert key_parts[1] == str(os.path.getmtime(file_info['path']))

    # ignore mdate, filename
    common_args = ["--src", source_dir, "--target", target_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "filename,mdate"]
    args = parse_arguments(common_args)
    key = get_file_key(args, file_info['path'])  # suppose to be only the hash
    assert key == 'edb36987f4e3526039ff5c174bcebb9513d95dbc235fb093806c8387dc9ffa91'

    # ignore none
    common_args = ["--src", source_dir, "--target", target_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "checkall"]
    args = parse_arguments(common_args)
    key = get_file_key(args, file_info['path'])
    # split key to hash and the rest
    key_parts = key.split('_')
    assert key_parts[0] == 'edb36987f4e3526039ff5c174bcebb9513d95dbc235fb093806c8387dc9ffa91'
    assert key_parts[1] == file_info['name']
    assert key_parts[2] == str(os.path.getmtime(file_info['path']))
