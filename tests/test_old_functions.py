import os
import shutil
import time

from duplicate_files_in_folders.file_manager import FileManager
from duplicate_files_in_folders.old_duplicates_finder import compare_files, clean_scan_duplications, \
    collect_scan_files
from duplicate_files_in_folders.utils import parse_arguments, get_file_key
from tests.helpers_testing import copy_files, img_files, IMG_DIR, setup_teardown


def test_compare_files(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    # Setup the files in the scan_dir directory
    copy_files(range(1, 3), scan_dir)

    # sleep for 0.5 second to make sure the mdate is different
    time.sleep(0.5)
    copy_files(range(1, 3), reference_dir)

    src1_file = os.path.join(scan_dir, "1.jpg")
    tgt1_file = os.path.join(reference_dir, "1.jpg")
    src2_file = os.path.join(scan_dir, "2.jpg")
    dup1_file = str(os.path.join(scan_dir, img_files[1]['original_name']))

    # copy file 1 also with original name to scan_dir folder
    shutil.copy(src1_file, dup1_file)

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


def test_clean_scan_duplications(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the scan_dir and ref directories
    os.makedirs(os.path.join(scan_dir, "sub1"))

    # Setup the files in the scan_dir directory
    copy_files(range(1, 6), scan_dir)
    copy_files(range(1, 6), os.path.join(scan_dir, "sub1"))
    copy_files([7], reference_dir)  # copy one file to ref folder to avoid argument error

    args = parse_arguments(common_args)
    unique_duplicate_files_found, duplicate_files_moved = clean_scan_duplications(args)

    # Check if all files from scan_dir subdirectory are now in base folder of move_to
    scan_sub_files = set(os.listdir(os.path.join(scan_dir, "sub1")))
    assert not scan_sub_files, "Scan subdirectory is not empty"

    # Check scan_dir folder has files 1-5 and sub1 folder is empty
    scan_files = set(os.listdir(scan_dir))
    assert scan_files == set([f"{i}.jpg" for i in range(1, 6)] + ['sub1']), "Scan directory files not correct"

    # Check move_to folder has files 1-5 under move_to/scan_dups/sub1 folder
    move_to_files = set(os.listdir(os.path.join(move_to_dir, "scan_dups", "sub1")))
    assert move_to_files == set([f"{i}.jpg" for i in range(1, 6)]), "Not all files have been moved to move_to directory"

    assert unique_duplicate_files_found == 5, "Unique duplicate files found"
    assert duplicate_files_moved == 5, "Not all duplicate files have been moved to move_to directory"


def test_clean_scan_duplications_several_subfolders(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the scan_dir and ref directories
    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(scan_dir, "sub2"))

    # Setup the files in the scan_dir directory
    copy_files(range(1, 6), scan_dir)
    copy_files(range(1, 6), os.path.join(scan_dir, "sub1"))
    copy_files(range(1, 6), os.path.join(scan_dir, "sub2"))

    copy_files([7], reference_dir)  # copy one file to ref folder to avoid argument error

    args = parse_arguments(common_args)
    unique_duplicate_files_found, duplicate_files_moved = clean_scan_duplications(args)

    # Check if all files from scan_dir subdirectory are now in base folder of move_to
    scan_sub_files = set(os.listdir(os.path.join(scan_dir, "sub1")))
    assert not scan_sub_files, "Scan subdirectory is not empty"
    scan_sub_files = set(os.listdir(os.path.join(scan_dir, "sub2")))
    assert not scan_sub_files, "Scan subdirectory is not empty"

    # Check scan_dir folder has files 1-5 and sub1, sub2 folders are empty
    scan_files = set(os.listdir(scan_dir))
    assert scan_files == set([f"{i}.jpg" for i in range(1, 6)] + ['sub1', 'sub2']), "Source files not correct"

    # Check move_to folder has files 1-5 under move_to/scan_dups/sub1 and sub2 folders
    move_to_files = set(os.listdir(os.path.join(move_to_dir, "scan_dups", "sub1")))
    assert move_to_files == set([f"{i}.jpg" for i in range(1, 6)]), "Not all files have been moved to move_to directory"
    move_to_files = set(os.listdir(os.path.join(move_to_dir, "scan_dups", "sub2")))
    assert move_to_files == set([f"{i}.jpg" for i in range(1, 6)]), "Not all files have been moved to move_to directory"

    assert unique_duplicate_files_found == 5, "Unique duplicate files found"
    assert duplicate_files_moved == 10, "Not all duplicate files have been moved to move_to directory"


def test_clean_scan_duplications_test_mode(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the scan_dir and ref directories
    os.makedirs(os.path.join(scan_dir, "sub1"))

    # Setup the files in the scan_dir directory
    copy_files(range(1, 6), scan_dir)
    copy_files(range(1, 6), os.path.join(scan_dir, "sub1"))

    copy_files([7], reference_dir)  # copy one file to ref folder to avoid argument error

    common_args.remove("--run")
    FileManager._instance = None # reset the singleton instance to make sure it is not used
    fm = FileManager(False).reset_all()

    args = parse_arguments(common_args)
    unique_duplicate_files_found, duplicate_files_moved = clean_scan_duplications(args)

    # Check if all files from scan_dir subdirectory are still there
    scan_sub_files = set(os.listdir(os.path.join(scan_dir, "sub1")))
    assert scan_sub_files == set([f"{i}.jpg" for i in range(1, 6)]), "Source subdirectory files have been moved"

    # Check scan_dir folder has files 1-5 and sub1 folder
    scan_files = set(os.listdir(scan_dir))
    assert scan_files == set([f"{i}.jpg" for i in range(1, 6)] + ['sub1']), "Scan directory files not correct"

    # Check that os.path.join(move_to_dir, "scan_dups") does not exist
    assert not os.path.exists(os.path.join(move_to_dir, "scan_dups")), "move_to directory exists"

    # Check move_to folder is empty
    move_to_files = set(os.listdir(move_to_dir))
    assert not move_to_files, "move_to directory is not empty"

    assert unique_duplicate_files_found == 5, "Unique duplicate files found"
    assert duplicate_files_moved == 5, "Wrong calculation of files to be moved to move_to directory"


def test_clean_scan_duplications_same_name_different_files(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(scan_dir, "sub2"))

    # Setup the files in the scan_dir directory
    copy_files(range(1, 3), os.path.join(scan_dir, "sub1"))

    # copy files 3 and 4 to sub2 folder but call them 1.jpg and 2.jpg
    for file_number in range(3, 5):
        src_file = os.path.join(IMG_DIR, f"{file_number}.jpg")
        dst_file = os.path.join(scan_dir, "sub2", f"{file_number - 2}.jpg")
        shutil.copy(src_file, dst_file)

    # copy file 5 to both sub1 and sub2 folders
    src_file = os.path.join(IMG_DIR, "5.jpg")
    shutil.copy(src_file, os.path.join(scan_dir, "sub1", "5.jpg"))
    shutil.copy(src_file, os.path.join(scan_dir, "sub2", "5.jpg"))

    copy_files([7], reference_dir)  # copy one file to ref folder to avoid argument error

    common_args.append("--extra_logging")

    args = parse_arguments(common_args)
    unique_duplicate_files_found, duplicate_files_moved = clean_scan_duplications(args)

    # sub1 folder should be the same - files 1, 2 and 5
    scan_sub_files = set(os.listdir(os.path.join(scan_dir, "sub1")))
    assert scan_sub_files == set([f"{i}.jpg" for i in range(1, 3)] + ['5.jpg']), "Source sub1 files have been moved"

    # sub2 folder should be - files 1 and 2
    scan_sub_files = set(os.listdir(os.path.join(scan_dir, "sub2")))
    assert scan_sub_files == set([f"{i}.jpg" for i in range(1, 3)]), "Source sub2 files is not correct"

    assert unique_duplicate_files_found == 1, "Unique duplicate files found"
    assert duplicate_files_moved == 1, "Wrong calculation of files to be moved to move_to directory"


def test_clean_scan_duplications_same_name_different_files_ignore_filename(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(scan_dir, "sub2"))

    # Setup the files in the scan_dir directory
    copy_files(range(1, 3), os.path.join(scan_dir, "sub1"))

    # copy files 3 and 4 to sub2 folder but call them 1.jpg and 2.jpg
    for file_number in range(3, 5):
        src_file = os.path.join(IMG_DIR, f"{file_number}.jpg")
        dst_file = os.path.join(scan_dir, "sub2", f"{file_number - 2}.jpg")
        shutil.copy(src_file, dst_file)

    # copy file 5 to both sub1 and sub2 folders
    src_file = os.path.join(IMG_DIR, "5.jpg")
    shutil.copy(src_file, os.path.join(scan_dir, "sub1", "5.jpg"))
    shutil.copy(src_file, os.path.join(scan_dir, "sub2", "5.jpg"))

    copy_files([7], reference_dir)  # copy one file to ref folder to avoid argument error

    common_args.append("--extra_logging")
    common_args.append("--ignore_diff")
    common_args.append("filename,mdate")

    # scan_dir content:
    # sub1: 1.jpg, 2.jpg, 5.jpg
    # sub2: 1.jpg (different file), 2.jpg (different file), 5.jpg

    args = parse_arguments(common_args)
    unique_duplicate_files_found, duplicate_files_moved = clean_scan_duplications(args)

    # sub1 folder should be the same - files 1, 2 and 5
    scan_sub_files = set(os.listdir(os.path.join(scan_dir, "sub1")))
    assert scan_sub_files == set([f"{i}.jpg" for i in range(1, 3)] + ['5.jpg']), "Scan sub1 files have been moved"

    # sub2 folder should be - files 1 and 2
    scan_sub_files = set(os.listdir(os.path.join(scan_dir, "sub2")))
    assert scan_sub_files == set([f"{i}.jpg" for i in range(1, 3)]), "Scan sub2 files is not correct"

    assert unique_duplicate_files_found == 1, "Unique duplicate files found"
    assert duplicate_files_moved == 1, "Wrong calculation of files to be moved to move_to directory"


def test_collect_scan_files_simple(setup_teardown):
    # files 1 to 4 in root, 3 to 6 in sub1
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    os.makedirs(os.path.join(scan_dir, "sub1"))
    copy_files(range(1, 5), scan_dir)
    copy_files(range(3, 7), os.path.join(scan_dir, "sub1"))

    copy_files([7], reference_dir)  # copy one file to ref folder to avoid argument error

    args = parse_arguments(common_args)
    scan_files = collect_scan_files(args)
    scan_duplicates = {src_key: src_filepaths for src_key, src_filepaths in scan_files.items()
                         if len(src_filepaths) > 1}
    assert len(scan_duplicates) == 2, "Unique duplicate files found"
    assert scan_duplicates == {
        get_file_key(args, os.path.join(scan_dir, "3.jpg")): [(os.path.join(scan_dir, "3.jpg"), 1), (os.path.join(scan_dir, "sub1", "3.jpg"), 2)],
        get_file_key(args, os.path.join(scan_dir, "4.jpg")): [(os.path.join(scan_dir, "4.jpg"), 1), (os.path.join(scan_dir, "sub1", "4.jpg"), 2)]}, "Wrong calculation of files to be moved to move_to directory"


# def test_validate_duplicate_files_destination(setup_teardown):
#     scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
#
#     # test case 1: folder doesn't exist but can be created under the scan_dir folder
#     file_manager.FileManager.reset_file_manager([reference_dir], [scan_dir, move_to_dir], True)
#     assert validate_duplicate_files_destination(os.path.join(scan_dir, "sub1"), run_mode=True) is True
#
#     # test case 2: folder doesn't exist and cannot be created
#     with pytest.raises(SystemExit) as excinfo:
#         file_manager.FileManager.reset_file_manager([reference_dir], [scan_dir, move_to_dir], True)
#         validate_duplicate_files_destination(os.path.join(scan_dir, "\"^&%/#$^\0%&!@"), run_mode=True)
#     assert excinfo.type == SystemExit
#     assert excinfo.value.code == 1
#
#     # test case 3: folder exist
#     file_manager.FileManager.reset_file_manager([reference_dir], [scan_dir, move_to_dir], True)
#     assert validate_duplicate_files_destination(scan_dir, run_mode=True) is True
#
#     # test case 4: same as test case 1 but with run_mode=False
#     file_manager.FileManager.reset_file_manager([reference_dir], [scan_dir, move_to_dir], True)
#     assert validate_duplicate_files_destination(os.path.join(scan_dir, "sub1"), run_mode=False) is True
#
#     # test case 5: non-existing folder but can be created, run_mode=False
#     file_manager.FileManager.reset_file_manager([reference_dir], [scan_dir, move_to_dir], True)
#     assert validate_duplicate_files_destination(os.path.join(scan_dir, "sub_new"), run_mode=False) is True


def test_delete_empty_folders_in_tree(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the scan_dir and ref directories
    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(scan_dir, "sub2"))
    os.makedirs(os.path.join(scan_dir, "sub2", "sub2_2"))

    # Setup the files in the scan_dir directory
    copy_files(range(1, 6), scan_dir)
    copy_files(range(1, 6), os.path.join(scan_dir, "sub1"))
    copy_files(range(1, 6), os.path.join(scan_dir, "sub2"))
    copy_files(range(1, 6), os.path.join(scan_dir, "sub2", "sub2_2"))

    copy_files([7], reference_dir)  # copy one file to ref folder to avoid argument error

    args = parse_arguments(common_args)
    unique_duplicate_files_found, duplicate_files_moved = clean_scan_duplications(args)
    fm = FileManager.get_instance()
    fm.delete_empty_folders_in_tree(scan_dir)

    assert unique_duplicate_files_found == 5, "Unique duplicate files found"

    # check if all empty folders have been deleted
    assert not os.path.exists(os.path.join(scan_dir, "sub1")), "sub1 folder is not empty"
    assert not os.path.exists(os.path.join(scan_dir, "sub2")), "sub2 folder is not empty" # no need to check sub2_2

    # check that scan_dir folder was not deleted
    assert os.path.exists(scan_dir), "scan_dir folder does not exist"


# def test_validate_folder(setup_teardown):
#     scan_dir, _, _, _ = setup_teardown
#
#     # test case 1: folder not existing
#     with pytest.raises(SystemExit) as excinfo:
#         validate_folder(os.path.join(scan_dir, "sub1"), "sub1")
#     assert excinfo.type == SystemExit
#     assert excinfo.value.code == 1
#
#     # test case 2: folder existing but empty
#     os.makedirs(os.path.join(scan_dir, "sub1"))
#     with pytest.raises(SystemExit) as excinfo:
#         validate_folder(os.path.join(scan_dir, "sub1"), "sub1")
#     assert excinfo.type == SystemExit
#     assert excinfo.value.code == 1
#
#     # test case 3: folder existing and not empty
#     copy_files(range(1, 6), os.path.join(scan_dir, "sub1"))
#     assert validate_folder(os.path.join(scan_dir, "sub1"), "sub1") is True
#
#
#
# def print_error(message):
#     print(f"Error: {message}")
#     logger.critical(f"{message}")
#     sys.exit(1)
#
#
# def validate_folder(folder, name):
#     """ Validate if a folder exists and is not empty. """
#     if not os.path.isdir(folder) or not os.path.exists(folder):
#         print_error(f"{name} folder does not exist.")
#     if not os.listdir(folder):
#         print_error(f"{name} folder is empty.")
#     return True
