import logging

from duplicate_files_in_folders.duplicates_finder import clean_source_duplications, find_duplicates_files_v3, \
    process_duplicates
from duplicate_files_in_folders.file_manager import FileManager
from duplicate_files_in_folders.utils import parse_arguments, any_is_subfolder_of, validate_folder, parse_size, \
    check_and_update_filename

from tests.helpers_testing import *

logger = logging.getLogger(__name__)

# Pytest test cases for parse_arguments function
def test_parse_arguments():
    # Test case 1: No arguments provided - will fail as src and target are required
    try:
        parse_arguments([])
        assert False
    except SystemExit:
        assert True

    # Test case 2: Only source and target provided - the test make sure the folders fits to the os folder style
    source_folder = get_folder_path('source')
    target_folder = get_folder_path('target')
    move_to_folder = get_folder_path('move_to')

    args = parse_arguments(['--src', source_folder, '--target', target_folder, '--move_to', move_to_folder])
    assert args.src == get_folder_path('source')
    assert args.target == get_folder_path('target')
    assert args.move_to == get_folder_path('move_to')
    assert args.run is False
    assert args.extra_logging is False
    assert args.copy_to_all is False
    assert args.ignore_diff == {'mdate'}
    assert args.delete_empty_folders is True
    assert args.max_size is None
    assert args.min_size is None
    assert args.whitelist_ext is None
    assert args.blacklist_ext is None
    assert args.full_hash is False

    # Test case 3: Many arguments provided
    args = parse_arguments(['--src', source_folder, '--target', target_folder, '--move_to', move_to_folder,
                            '--run', '--extra_logging', '--ignore_diff', 'mdate,filename', '--copy_to_all'])
    assert args.src == get_folder_path('source')
    assert args.target == get_folder_path('target')
    assert args.move_to == get_folder_path('move_to')
    assert args.run is True
    assert args.extra_logging is True
    assert args.ignore_diff == {'mdate', 'filename'}
    assert args.copy_to_all is True
    assert args.delete_empty_folders is True

    # Test case 4: --ignore_diff argument with invalid values
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(['--src', source_folder, '--target', target_folder, '--move_to', move_to_folder, '--ignore_diff',
                         'invalid'])
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2

    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(['--src', source_folder, '--target', target_folder, '--move_to', move_to_folder,
                         '--ignore_diff', 'mdate,invalid'])
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2

    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(['--src', source_folder, '--target', target_folder, '--move_to', move_to_folder,
                         '--ignore_diff', 'mdate,checkall'])
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2

    args = parse_arguments(['--src', source_folder, '--target', target_folder, '--move_to', move_to_folder,
                            '--ignore_diff', 'checkall'])
    assert args.ignore_diff == set()


# Pytest test cases for check_and_update_filename function
def test_check_and_update_filename():
    # Test case 1: Test for a file that does not exist
    non_exist_file = 'tests/non_exist_file.txt'
    assert check_and_update_filename(non_exist_file) == non_exist_file

    # Test case 2: Test for a file that exists
    exist_file = 'tests/imgs/5.jpg'
    assert check_and_update_filename(exist_file) != exist_file


def test_validate_folder(setup_teardown):
    source_dir, _, _, _ = setup_teardown

    # test case 1: folder not existing
    with pytest.raises(SystemExit) as excinfo:
        validate_folder(os.path.join(source_dir, "sub1"), "sub1")
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

    # test case 2: folder existing but empty
    os.makedirs(os.path.join(source_dir, "sub1"))
    with pytest.raises(SystemExit) as excinfo:
        validate_folder(os.path.join(source_dir, "sub1"), "sub1")
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

    # test case 3: folder existing and not empty
    copy_files(range(1, 6), os.path.join(source_dir, "sub1"))
    assert validate_folder(os.path.join(source_dir, "sub1"), "sub1") is True


def test_any_is_subfolder_of():
    # Test case 1: one folder is subfolder of another
    with pytest.raises(SystemExit) as excinfo:
        any_is_subfolder_of(["C:\\Users\\user\\Desktop\\folder", "C:\\Users\\user\\Desktop\\folder\\subfolder"])
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

    # Test case 2: no folder is subfolder of another
    assert any_is_subfolder_of(["C:\\Users\\user\\Desktop\\folder1", "C:\\Users\\user\\Desktop\\folder2"]) is False

    # Test case 3: one folder is subfolder of another
    with pytest.raises(SystemExit) as excinfo:
        any_is_subfolder_of(["/path/to/folder", "/path/to/folder/subfolder"])
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

    # Test case 4: no folder is subfolder of another
    assert any_is_subfolder_of(["/path/to/folder1", "/path/to/folder2"]) is False

    # Test case 5: 3 folders, one is subfolder of another
    with pytest.raises(SystemExit) as excinfo:
        any_is_subfolder_of(["/path/to/folder1", "/path/to/folder2", "/path/to/folder2/subfolder"])
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

    # Test case 6: 3 folders, no folder is subfolder of another
    assert any_is_subfolder_of(["/path/to/folder1", "/path/to/folder2", "/path/to/folder3"]) is False

    # Test case 7: 3 folders, one is subfolder of another
    with pytest.raises(SystemExit) as excinfo:
        any_is_subfolder_of(["C:\\Users\\user\\Desktop\\folder1", "C:\\Users\\user\\Desktop\\folder2", "C:\\Users\\user\\Desktop\\folder2\\subfolder"])
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

    # Test case 8: 3 folders, no folder is subfolder of another
    assert any_is_subfolder_of(["C:\\Users\\user\\Desktop\\folder1", "C:\\Users\\user\\Desktop\\folder2", "C:\\Users\\user\\Desktop\\folder3"]) is False


def test_parse_size():
    # Test case 1: valid size string
    assert parse_size("10KB") == 10240
    assert parse_size("10MB") == 10485760
    assert parse_size("10GB") == 10737418240
    assert parse_size("10B") == 10

    # Test case 2: invalid size string
    with pytest.raises(ValueError) as excinfo:
        parse_size("10KBs")
    assert str(excinfo.value) == "Invalid size format"

    # Test case 3: negative size
    with pytest.raises(ValueError) as excinfo:
        parse_size("-10KB")
    assert str(excinfo.value) == "Size cannot be negative"

    # Test case 4: invalid size string
    with pytest.raises(ValueError) as excinfo:
        parse_size("KB10")
    assert str(excinfo.value) == "Invalid size format"

    # Test case 5: only number, should be treated as bytes
    assert parse_size("10") == 10

    # Test case 6: negative number, should be treated as bytes but still raise an error
    with pytest.raises(ValueError) as excinfo:
        parse_size("-10")
    assert str(excinfo.value) == "Size cannot be negative"

    # Test case 7: invalid string
    with pytest.raises(ValueError) as excinfo:
        parse_size("invalid")
    assert str(excinfo.value) == "Invalid size format"

    # Test case 8: lowercase should be ok
    assert parse_size("10kb") == 10240
    assert parse_size("10mb") == 10485760
    assert parse_size("10gb") == 10737418240

    # Test case 9: zero should be ok
    assert parse_size("0KB") == 0
    assert parse_size("0MB") == 0
    assert parse_size("0GB") == 0
    assert parse_size("0B") == 0
    assert parse_size("0") == 0


def test_delete_empty_folders_in_tree(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the source and target directories
    os.makedirs(os.path.join(source_dir, "sub1"))
    os.makedirs(os.path.join(source_dir, "sub2"))
    os.makedirs(os.path.join(source_dir, "sub2", "sub2_2"))

    os.makedirs(os.path.join(target_dir, "sub1"))

    # Setup the files in the source directory
    copy_files(range(1, 6), source_dir)
    copy_files(range(1, 6), os.path.join(source_dir, "sub1"))
    copy_files(range(1, 6), os.path.join(source_dir, "sub2"))
    copy_files(range(1, 6), os.path.join(source_dir, "sub2", "sub2_2"))

    copy_files(range(1, 6), target_dir)
    copy_files(range(1, 6), os.path.join(target_dir, "sub1"))

    common_args.append("--copy_to_all")
    args = parse_arguments(common_args)
    duplicates, source_stats, target_stats = find_duplicates_files_v3(args, source_dir, target_dir)
    process_duplicates(duplicates, args)
    clean_source_duplications(args, duplicates)
    fm = FileManager.get_instance()
    fm.delete_empty_folders_in_tree(source_dir)
    logger.debug(get_folder_structure_include_subfolders(source_dir))
    logger.debug(get_folder_structure_include_subfolders(target_dir))
    logger.debug(get_folder_structure_include_subfolders(move_to_dir))

    # check if all empty folders have been deleted
    assert not os.path.exists(os.path.join(source_dir, "sub1")), "sub1 folder is not empty"
    assert not os.path.exists(os.path.join(source_dir, "sub2")), "sub2 folder is not empty" # no need to check sub2_2
    assert os.path.exists(os.path.join(target_dir, "sub1")), "target sub1 folder is empty"
