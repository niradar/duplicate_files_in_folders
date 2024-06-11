from duplicate_files_in_folders.duplicates_finder import clean_scan_dir_duplications, find_duplicates_files_v3, \
    process_duplicates
from duplicate_files_in_folders.file_manager import FileManager
from duplicate_files_in_folders.utils import parse_arguments, any_is_subfolder_of, parse_size, \
    check_and_update_filename, setup_file_manager

from tests.helpers_testing import *

logger = logging.getLogger(__name__)


# Pytest test cases for parse_arguments function
def test_parse_arguments():
    # Test case 1: No arguments provided - will fail as src and ref are required
    try:
        parse_arguments([])
        assert False
    except SystemExit:
        assert True

    # Test case 2: Only scan_dir and ref provided - the test make sure the folders fits to the os folder style
    scan_dir = get_folder_path(SCAN_DIR_NAME)
    reference_dir = get_folder_path(REF_DIR_NAME)
    move_to_folder = get_folder_path('move_to')

    args = parse_arguments(['--scan', scan_dir, '--reference_dir', reference_dir, '--move_to', move_to_folder], False)
    assert args.scan_dir == get_folder_path(SCAN_DIR_NAME)
    assert args.reference_dir == get_folder_path(REF_DIR_NAME)
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
    args = parse_arguments(['--scan', scan_dir, '--reference_dir', reference_dir, '--move_to', move_to_folder,
                            '--run', '--extra_logging', '--ignore_diff', 'mdate,filename', '--copy_to_all'], False)
    assert args.scan_dir == get_folder_path(SCAN_DIR_NAME)
    assert args.reference_dir == get_folder_path(REF_DIR_NAME)
    assert args.move_to == get_folder_path('move_to')
    assert args.run is True
    assert args.extra_logging is True
    assert args.ignore_diff == {'mdate', 'filename'}
    assert args.copy_to_all is True
    assert args.delete_empty_folders is True

    # Test case 4: Many arguments provided
    args = parse_arguments(['--scan', scan_dir, '--reference_dir', reference_dir, '--move_to', move_to_folder,
                            '--run', '--ignore_diff', 'mdate,filename', '--min_size', '1KB', '--max_size', '1MB',
                            '--whitelist_ext', 'jpg'], False)
    assert args.scan_dir == get_folder_path(SCAN_DIR_NAME)
    assert args.reference_dir == get_folder_path(REF_DIR_NAME)
    assert args.move_to == get_folder_path('move_to')
    assert args.run is True
    assert args.extra_logging is False
    assert args.ignore_diff == {'mdate', 'filename'}
    assert args.copy_to_all is False
    assert args.delete_empty_folders is True
    assert args.min_size == 1024
    assert args.max_size == 1048576
    assert args.whitelist_ext == {'jpg'}

    # Test case 5: --ignore_diff argument with invalid values
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(['--scan', scan_dir, '--reference_dir', reference_dir, '--move_to', move_to_folder,
                         '--ignore_diff', 'invalid'], False)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2

    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(['--scan', scan_dir, '--reference_dir', reference_dir, '--move_to', move_to_folder,
                         '--ignore_diff', 'mdate,invalid'], False)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2

    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(['--scan', scan_dir, '--reference_dir', reference_dir, '--move_to', move_to_folder,
                         '--ignore_diff', 'mdate,checkall'], False)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2

    args = parse_arguments(['--scan', scan_dir, '--reference_dir', reference_dir, '--move_to', move_to_folder,
                            '--ignore_diff', 'checkall'], False)
    assert args.ignore_diff == set()

    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(['--scan', scan_dir, '--reference_dir', reference_dir, '--move_to', move_to_folder,
                         '--min_size', 'invalid'], False)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2

    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(['--scan', scan_dir, '--reference_dir', reference_dir, '--move_to', move_to_folder,
                         '--max_size', 'invalid'], False)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2

    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(['--scan', scan_dir, '--reference_dir', reference_dir, '--move_to', move_to_folder,
                         '--min_size', '-10'], False)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2


# Pytest test cases for check_and_update_filename function
def test_check_and_update_filename():
    # Test case 1: Test for a file that does not exist
    non_exist_file = 'tests/non_exist_file.txt'
    assert check_and_update_filename(non_exist_file) == non_exist_file

    # Test case 2: Test for a file that exists
    exist_file = 'tests/imgs/5.jpg'
    assert check_and_update_filename(exist_file) != exist_file


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
        any_is_subfolder_of(["C:\\Users\\user\\Desktop\\folder1", "C:\\Users\\user\\Desktop\\folder2",
                             "C:\\Users\\user\\Desktop\\folder2\\subfolder"])
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

    # Test case 8: 3 folders, no folder is subfolder of another
    assert any_is_subfolder_of(["C:\\Users\\user\\Desktop\\folder1", "C:\\Users\\user\\Desktop\\folder2",
                                "C:\\Users\\user\\Desktop\\folder3"]) is False


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
    scan_dir, reference_dir, move_to_dir, _ = setup_teardown

    # Create the necessary subdirectories in the scan_dir and ref directories
    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(scan_dir, "sub2"))
    os.makedirs(os.path.join(scan_dir, "sub2", "sub2_2"))

    os.makedirs(os.path.join(reference_dir, "sub1"))

    # Setup the files in the scan_dir directory
    copy_files(range(1, 6), scan_dir)
    copy_files(range(1, 6), os.path.join(scan_dir, "sub1"))
    copy_files(range(1, 6), os.path.join(scan_dir, "sub2"))
    copy_files(range(1, 6), os.path.join(scan_dir, "sub2", "sub2_2"))

    copy_files(range(1, 6), reference_dir)
    copy_files(range(1, 6), os.path.join(reference_dir, "sub1"))

    # run in test mode, no files will be moved
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--copy_to_all"]
    test_args = common_args.copy()

    args = parse_arguments(test_args)
    setup_file_manager(args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    process_duplicates(duplicates, args)
    clean_scan_dir_duplications(args, duplicates)
    fm = FileManager.get_instance()
    fm.delete_empty_folders_in_tree(scan_dir)

    assert os.path.exists(os.path.join(scan_dir, "sub1")), "sub1 folder does not exist"
    assert os.path.exists(os.path.join(scan_dir, "sub2")), "sub2 folder does not exist"
    assert os.path.exists(os.path.join(scan_dir, "sub2", "sub2_2")), "sub2_2 folder does not exist"
    assert os.path.exists(os.path.join(reference_dir, "sub1")), "ref sub1 folder does not exist"

    # run in run mode, files will be moved
    run_args = common_args.copy()
    run_args.append("--run")

    args = parse_arguments(run_args)
    setup_file_manager(args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    process_duplicates(duplicates, args)
    clean_scan_dir_duplications(args, duplicates)
    fm = FileManager.get_instance()
    fm.delete_empty_folders_in_tree(scan_dir)
    logger.debug(get_folder_structure_include_subfolders(scan_dir))
    logger.debug(get_folder_structure_include_subfolders(reference_dir))
    logger.debug(get_folder_structure_include_subfolders(move_to_dir))

    # check if all empty folders have been deleted
    assert not os.path.exists(os.path.join(scan_dir, "sub1")), "sub1 folder exists"
    assert not os.path.exists(os.path.join(scan_dir, "sub2")), "sub2 folder exists"  # no need to check sub2_2
    assert os.path.exists(os.path.join(reference_dir, "sub1")), "reference sub1 folder does not exist"
