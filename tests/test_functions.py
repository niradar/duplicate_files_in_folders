from df_finder3 import parse_arguments, check_and_update_filename, \
    clean_source_duplications, delete_empty_folders_in_tree, validate_duplicate_files_destination, validate_folder, \
    compare_files, collect_source_files, get_file_key, any_is_subfolder_of
from tests.helpers_testing import *


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

    # Test case 3: All arguments provided
    args = parse_arguments(['--src', source_folder, '--target', target_folder, '--move_to', move_to_folder,
                            '--run', '--extra_logging', '--ignore_diff', 'mdate,filename', '--copy_to_all',
                            '--delete_empty_folders'])
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
    assert excinfo.value.code == 1

    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(['--src', source_folder, '--target', target_folder, '--move_to', move_to_folder,
                         '--ignore_diff', 'mdate,invalid'])
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

    with pytest.raises(SystemExit) as excinfo:
        parse_arguments(['--src', source_folder, '--target', target_folder, '--move_to', move_to_folder,
                         '--ignore_diff', 'mdate,checkall'])
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

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


def test_clean_source_duplications(setup_teardown):
    source_dir, _, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the source and target directories
    os.makedirs(os.path.join(source_dir, "sub1"))

    # Setup the files in the source directory
    copy_files(range(1, 6), source_dir)
    copy_files(range(1, 6), os.path.join(source_dir, "sub1"))

    args = parse_arguments(common_args)
    unique_duplicate_files_found, duplicate_files_moved = clean_source_duplications(args)

    # Check if all files from source subdirectory are now in base folder of move_to
    source_sub_files = set(os.listdir(os.path.join(source_dir, "sub1")))
    assert not source_sub_files, "Source subdirectory is not empty"

    # Check source folder has files 1-5 and sub1 folder is empty
    source_files = set(os.listdir(source_dir))
    assert source_files == set([f"{i}.jpg" for i in range(1, 6)] + ['sub1']), "Source directory files not correct"

    # Check move_to folder has files 1-5 under move_to/source_dups/sub1 folder
    move_to_files = set(os.listdir(os.path.join(move_to_dir, "source_dups", "sub1")))
    assert move_to_files == set([f"{i}.jpg" for i in range(1, 6)]), "Not all files have been moved to move_to directory"

    assert unique_duplicate_files_found == 5, "Unique duplicate files found"
    assert duplicate_files_moved == 5, "Not all duplicate files have been moved to move_to directory"


def test_clean_source_duplications_several_subfolders(setup_teardown):
    source_dir, _, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the source and target directories
    os.makedirs(os.path.join(source_dir, "sub1"))
    os.makedirs(os.path.join(source_dir, "sub2"))

    # Setup the files in the source directory
    copy_files(range(1, 6), source_dir)
    copy_files(range(1, 6), os.path.join(source_dir, "sub1"))
    copy_files(range(1, 6), os.path.join(source_dir, "sub2"))

    args = parse_arguments(common_args)
    unique_duplicate_files_found, duplicate_files_moved = clean_source_duplications(args)

    # Check if all files from source subdirectory are now in base folder of move_to
    source_sub_files = set(os.listdir(os.path.join(source_dir, "sub1")))
    assert not source_sub_files, "Source subdirectory is not empty"
    source_sub_files = set(os.listdir(os.path.join(source_dir, "sub2")))
    assert not source_sub_files, "Source subdirectory is not empty"

    # Check source folder has files 1-5 and sub1, sub2 folders are empty
    source_files = set(os.listdir(source_dir))
    assert source_files == set([f"{i}.jpg" for i in range(1, 6)] + ['sub1', 'sub2']), "Source files not correct"

    # Check move_to folder has files 1-5 under move_to/source_dups/sub1 and sub2 folders
    move_to_files = set(os.listdir(os.path.join(move_to_dir, "source_dups", "sub1")))
    assert move_to_files == set([f"{i}.jpg" for i in range(1, 6)]), "Not all files have been moved to move_to directory"
    move_to_files = set(os.listdir(os.path.join(move_to_dir, "source_dups", "sub2")))
    assert move_to_files == set([f"{i}.jpg" for i in range(1, 6)]), "Not all files have been moved to move_to directory"

    assert unique_duplicate_files_found == 5, "Unique duplicate files found"
    assert duplicate_files_moved == 10, "Not all duplicate files have been moved to move_to directory"


def test_clean_source_duplications_test_mode(setup_teardown):
    source_dir, _, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the source and target directories
    os.makedirs(os.path.join(source_dir, "sub1"))

    # Setup the files in the source directory
    copy_files(range(1, 6), source_dir)
    copy_files(range(1, 6), os.path.join(source_dir, "sub1"))

    common_args.remove("--run")

    args = parse_arguments(common_args)
    unique_duplicate_files_found, duplicate_files_moved = clean_source_duplications(args)

    # Check if all files from source subdirectory are still there
    source_sub_files = set(os.listdir(os.path.join(source_dir, "sub1")))
    assert source_sub_files == set([f"{i}.jpg" for i in range(1, 6)]), "Source subdirectory files have been moved"

    # Check source folder has files 1-5 and sub1 folder
    source_files = set(os.listdir(source_dir))
    assert source_files == set([f"{i}.jpg" for i in range(1, 6)] + ['sub1']), "Source directory files not correct"

    # Check that os.path.join(move_to_dir, "source_dups") does not exist
    assert not os.path.exists(os.path.join(move_to_dir, "source_dups")), "move_to directory exists"

    # Check move_to folder is empty
    move_to_files = set(os.listdir(move_to_dir))
    assert not move_to_files, "move_to directory is not empty"

    assert unique_duplicate_files_found == 5, "Unique duplicate files found"
    assert duplicate_files_moved == 5, "Wrong calculation of files to be moved to move_to directory"


def test_clean_source_duplications_same_name_different_files(setup_teardown):
    source_dir, _, move_to_dir, common_args = setup_teardown

    os.makedirs(os.path.join(source_dir, "sub1"))
    os.makedirs(os.path.join(source_dir, "sub2"))

    # Setup the files in the source directory
    copy_files(range(1, 3), os.path.join(source_dir, "sub1"))

    # copy files 3 and 4 to sub2 folder but call them 1.jpg and 2.jpg
    for file_number in range(3, 5):
        src_file = os.path.join(IMG_DIR, f"{file_number}.jpg")
        dst_file = os.path.join(source_dir, "sub2", f"{file_number - 2}.jpg")
        shutil.copy(src_file, dst_file)

    # copy file 5 to both sub1 and sub2 folders
    src_file = os.path.join(IMG_DIR, "5.jpg")
    shutil.copy(src_file, os.path.join(source_dir, "sub1", "5.jpg"))
    shutil.copy(src_file, os.path.join(source_dir, "sub2", "5.jpg"))

    common_args.append("--extra_logging")

    args = parse_arguments(common_args)
    unique_duplicate_files_found, duplicate_files_moved = clean_source_duplications(args)

    # sub1 folder should be the same - files 1, 2 and 5
    source_sub_files = set(os.listdir(os.path.join(source_dir, "sub1")))
    assert source_sub_files == set([f"{i}.jpg" for i in range(1, 3)] + ['5.jpg']), "Source sub1 files have been moved"

    # sub2 folder should be - files 1 and 2
    source_sub_files = set(os.listdir(os.path.join(source_dir, "sub2")))
    assert source_sub_files == set([f"{i}.jpg" for i in range(1, 3)]), "Source sub2 files is not correct"

    assert unique_duplicate_files_found == 1, "Unique duplicate files found"
    assert duplicate_files_moved == 1, "Wrong calculation of files to be moved to move_to directory"


def test_clean_source_duplications_same_name_different_files_ignore_filename(setup_teardown):
    source_dir, _, move_to_dir, common_args = setup_teardown

    os.makedirs(os.path.join(source_dir, "sub1"))
    os.makedirs(os.path.join(source_dir, "sub2"))

    # Setup the files in the source directory
    copy_files(range(1, 3), os.path.join(source_dir, "sub1"))

    # copy files 3 and 4 to sub2 folder but call them 1.jpg and 2.jpg
    for file_number in range(3, 5):
        src_file = os.path.join(IMG_DIR, f"{file_number}.jpg")
        dst_file = os.path.join(source_dir, "sub2", f"{file_number - 2}.jpg")
        shutil.copy(src_file, dst_file)

    # copy file 5 to both sub1 and sub2 folders
    src_file = os.path.join(IMG_DIR, "5.jpg")
    shutil.copy(src_file, os.path.join(source_dir, "sub1", "5.jpg"))
    shutil.copy(src_file, os.path.join(source_dir, "sub2", "5.jpg"))

    common_args.append("--extra_logging")
    common_args.append("--ignore_diff")
    common_args.append("filename,mdate")

    # source content:
    # sub1: 1.jpg, 2.jpg, 5.jpg
    # sub2: 1.jpg (different file), 2.jpg (different file), 5.jpg

    args = parse_arguments(common_args)
    unique_duplicate_files_found, duplicate_files_moved = clean_source_duplications(args)

    # sub1 folder should be the same - files 1, 2 and 5
    source_sub_files = set(os.listdir(os.path.join(source_dir, "sub1")))
    assert source_sub_files == set([f"{i}.jpg" for i in range(1, 3)] + ['5.jpg']), "Source sub1 files have been moved"

    # sub2 folder should be - files 1 and 2
    source_sub_files = set(os.listdir(os.path.join(source_dir, "sub2")))
    assert source_sub_files == set([f"{i}.jpg" for i in range(1, 3)]), "Source sub2 files is not correct"

    assert unique_duplicate_files_found == 1, "Unique duplicate files found"
    assert duplicate_files_moved == 1, "Wrong calculation of files to be moved to move_to directory"


def test_delete_empty_folders_in_tree(setup_teardown):
    source_dir, _, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the source and target directories
    os.makedirs(os.path.join(source_dir, "sub1"))
    os.makedirs(os.path.join(source_dir, "sub2"))
    os.makedirs(os.path.join(source_dir, "sub2", "sub2_2"))

    # Setup the files in the source directory
    copy_files(range(1, 6), source_dir)
    copy_files(range(1, 6), os.path.join(source_dir, "sub1"))
    copy_files(range(1, 6), os.path.join(source_dir, "sub2"))
    copy_files(range(1, 6), os.path.join(source_dir, "sub2", "sub2_2"))

    args = parse_arguments(common_args)
    unique_duplicate_files_found, duplicate_files_moved = clean_source_duplications(args)
    delete_empty_folders_in_tree(source_dir)
    assert unique_duplicate_files_found == 5, "Unique duplicate files found"

    # check if all empty folders have been deleted
    assert not os.path.exists(os.path.join(source_dir, "sub1")), "sub1 folder is not empty"
    assert not os.path.exists(os.path.join(source_dir, "sub2")), "sub2 folder is not empty" # no need to check sub2_2

    # check that source folder was not deleted
    assert os.path.exists(source_dir), "source folder does not exist"


def test_validate_duplicate_files_destination(setup_teardown):
    source_dir, _, _, _ = setup_teardown

    # test case 1: folder doesn't exist but can be created under the source folder
    assert validate_duplicate_files_destination(os.path.join(source_dir, "sub1"), run_mode=True) is True

    # test case 2: folder doesn't exist and cannot be created
    with pytest.raises(SystemExit) as excinfo:
        validate_duplicate_files_destination(os.path.join(source_dir, "\"^&%#$^%&!@"), run_mode=True)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

    # test case 3: folder exist
    assert validate_duplicate_files_destination(source_dir, run_mode=True) is True

    # test case 4: same as test case 1 but with run_mode=False
    assert validate_duplicate_files_destination(os.path.join(source_dir, "sub1"), run_mode=False) is True

    # test case 5: non-existing folder but can be created, run_mode=False
    assert validate_duplicate_files_destination(os.path.join(source_dir, "sub_new"), run_mode=False) is True


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


def test_compare_files(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown

    # Setup the files in the source directory
    copy_files(range(1, 3), source_dir)
    copy_files(range(1, 3), target_dir)

    # copy file 1 also with original name to source folder
    shutil.copy(os.path.join(source_dir, "1.jpg"), os.path.join(source_dir, img_files[1]['original_name']))

    src1_file = os.path.join(source_dir, "1.jpg")
    tgt1_file = os.path.join(target_dir, "1.jpg")
    src2_file = os.path.join(source_dir, "2.jpg")
    dup1_file = os.path.join(source_dir, img_files[1]['original_name'])

    # Test case 1: same file, compare by filename True
    assert compare_files(src1_file, src1_file, None) is True

    # Test case 2: same file, compare by filename False
    assert compare_files(src1_file, src1_file, {'filename'}) is True

    # Test case 3: different files, compare by filename True
    assert compare_files(src1_file, src2_file, None) is False

    # Test case 4: different files, compare by filename False
    assert compare_files(src1_file, src2_file, {'mdate', 'filename'}) is False

    # Test case 5: same file, different folders, compare by filename True, mdate different
    assert compare_files(src1_file, tgt1_file, None) is False

    # Test case 6: same file, different folders, compare by filename False, ignore mdate
    assert compare_files(src1_file, tgt1_file, {'mdate'}) is True

    # Test case 7: same file, different folders, compare by filename True, ignore mdate
    assert compare_files(src1_file, tgt1_file, {'mdate'}) is True

    # Test case 8: same file, different name, compare by filename True, ignore mdate
    # It is by design that it won't compare the files names, it assumes it was already done
    assert compare_files(src1_file, dup1_file, {'mdate'}) is False

    # Test case 9: same file, different name, compare by filename False, ignore mdate
    assert compare_files(src1_file, dup1_file, {'mdate', 'filename'}) is True


# files 1 to 4 in root, 3 to 6 in sub1
def test_collect_source_files_simple(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown

    os.makedirs(os.path.join(source_dir, "sub1"))
    copy_files(range(1, 5), source_dir)
    copy_files(range(3, 7), os.path.join(source_dir, "sub1"))

    args = parse_arguments(common_args)
    source_files = collect_source_files(args)
    source_duplicates = {src_key: src_filepaths for src_key, src_filepaths in source_files.items()
                         if len(src_filepaths) > 1}
    assert len(source_duplicates) == 2, "Unique duplicate files found"
    assert source_duplicates == {
        get_file_key(args, os.path.join(source_dir, "3.jpg")): [(os.path.join(source_dir, "3.jpg"), 1), (os.path.join(source_dir, "sub1", "3.jpg"), 2)],
        get_file_key(args, os.path.join(source_dir, "4.jpg")): [(os.path.join(source_dir, "4.jpg"), 1), (os.path.join(source_dir, "sub1", "4.jpg"), 2)] }, "Wrong calculation of files to be moved to move_to directory"


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


