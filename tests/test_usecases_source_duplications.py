from df_finder3 import main
from duplicate_files_in_folders.utils import parse_arguments
from tests.helpers_testing import *


# Test 12 - files 1 to 6 in scan_dir subfolder sub1, files 1 to 2 and also 6 in scan_dir subfolder sub2,
# sub3 in scan_dir will contain files 1, 2, 3
# files 1 to 3 in reference base folder, files 3 and 5 in reference subfolder sub1
def test12(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the scan_dir and ref directories
    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(scan_dir, "sub2"))
    os.makedirs(os.path.join(scan_dir, "sub3"))
    os.makedirs(os.path.join(reference_dir, "sub1"))

    # Setup the files in the scan_dir subdirectories and reference directory
    copy_files(range(1, 7), os.path.join(scan_dir, "sub1"))
    copy_files([1, 2, 6], os.path.join(scan_dir, "sub2"))
    copy_files(range(1, 4), os.path.join(scan_dir, "sub3"))

    copy_files(range(1, 4), reference_dir)
    copy_files([3, 5], os.path.join(reference_dir, "sub1"))

    # scan_dir content:
    #   sub1: 1.jpg, 2.jpg, 3.jpg, 4.jpg, 5.jpg, 6.jpg
    #   sub2: 1.jpg, 2.jpg, 6.jpg
    #   sub3: 1.jpg, 2.jpg, 3.jpg

    # reference content:
    #   1.jpg, 2.jpg, 3.jpg
    #   sub1: 3.jpg, 5.jpg

    # after running the script:
    # scan_dir should contain:
    #   sub1: 4.jpg, 6.jpg
    #   sub2: 6.jpg
    # reference should contain:
    #   1.jpg, 2.jpg, 3.jpg
    #   sub1: 3.jpg, 5.jpg
    # move_to should contain:
    #   1.jpg, 2.jpg, 3.jpg
    #   sub1: 3.jpg, 5.jpg
    #   scan_dups: sub2, sub3
    #       sub2: 1.jpg, 2.jpg
    #       sub3: 1.jpg, 2.jpg

    common_args.append("--copy_to_all")
    args = parse_arguments(common_args)
    main(args)

    # scan_dir should contain only sub1
    scan_files = set(os.listdir(scan_dir))
    assert scan_files == {"sub1", "sub2"}, "Scan directory files not correct"

    # scan_dir sub1 should contain files 4, 6 only
    scan_sub1_files = set(os.listdir(os.path.join(scan_dir, "sub1")))
    assert scan_sub1_files == {f"{i}.jpg" for i in [4, 6]}, "Source sub1 directory files not correct"

    # ref should contain files 1-3 and sub1
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == {f"{i}.jpg" for i in range(1, 4)} | {'sub1'}, "Reference directory files not correct"

    # ref/sub1 should contain file 3 and 5
    ref_sub1_files = set(os.listdir(os.path.join(reference_dir, "sub1")))
    assert ref_sub1_files == {'3.jpg', '5.jpg'}, "ref sub1 directory files not correct"

    # move_to should contain sub2, scan_dups should contain files 1, 2, 3
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == {f'{SCAN_DIR_NAME}_dups', 'sub1'} | {f"{i}.jpg" for i in range(1, 4)}, \
        "Move_to directory files not correct"

    conditions = [
        {
            'type': 'subdirs_count',
            'parent_folder': f'{SCAN_DIR_NAME}_dups',
            'required_subdirs': {'sub1', 'sub2', 'sub3'},
            'expected_count': 2
        },
        {
            'type': 'file_count',
            'folders': {f'{SCAN_DIR_NAME}_dups' + os.sep + 'sub1', f'{SCAN_DIR_NAME}_dups' + os.sep + 'sub2',
                        f'{SCAN_DIR_NAME}_dups' + os.sep + 'sub3'},
            'file': '1.jpg',
            'count': 2,
            'include_subfolders': False
        },
        {
            'type': 'file_count',
            'folders': {f'{SCAN_DIR_NAME}_dups' + os.sep + 'sub1', f'{SCAN_DIR_NAME}_dups' + os.sep + 'sub2',
                        f'{SCAN_DIR_NAME}_dups' + os.sep + 'sub3'},
            'file': '2.jpg',
            'count': 2,
            'include_subfolders': False
        },

    ]
    check_folder_conditions(move_to_dir, conditions)
    # move_to/scan_dups/sub1, move_to/scan_dups/sub2, move_to/scan_dups/sub3 should contain files:
    #   1.jpg, 2.jpg exactly 2 times

    # move_to/scan_dups/sub2 should contain files 1, 2
    move_to_sub2_files = set(os.listdir(os.path.join(move_to_dir, f"{SCAN_DIR_NAME}_dups", "sub2")))
    assert move_to_sub2_files == {f"{i}.jpg" for i in [1, 2]}, "Move_to sub2 directory files not correct"

    # move_to/sub1 should contain file 3, 5
    move_to_sub1_files = set(os.listdir(os.path.join(move_to_dir, "sub1")))
    assert move_to_sub1_files == {'3.jpg', '5.jpg'}, "Move_to sub1 directory files not correct"


# test 15 - both scan_dir and ref have 1.jpg in the main folder, and also in subfolder sub1
def test15(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the scan_dir and ref directories
    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(reference_dir, "sub1"))

    # Setup the files in the scan_dir subdirectories and reference directory
    copy_files([1], scan_dir)
    copy_files([1], reference_dir)
    copy_files([1], os.path.join(scan_dir, "sub1"))
    copy_files([1], os.path.join(reference_dir, "sub1"))

    common_args.append("--copy_to_all")

    args = parse_arguments(common_args)
    main(args)

    # Check if all files from scan_dir are now in base folder of move_to
    scan_files = set(os.listdir(scan_dir))
    assert not scan_files, "Scan directory is not empty"

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == {"1.jpg", "sub1"}, "Reference directory files have changed"

    # Check no change to reference subfolder
    ref_sub_files = set(os.listdir(os.path.join(reference_dir, "sub1")))
    assert ref_sub_files == {"1.jpg"}, "Reference sub directory files have changed"

    # Move all function to use Conditions
    conditions = [  # Check move_to folder
        {
            'type': 'items_in_folder',
            'folder': '',
            'items': {"1.jpg", "sub1"}
        },
        {
            'type': 'items_in_folder',
            'folder': 'sub1',
            'items': {"1.jpg"}
        }
    ]
    check_folder_conditions(move_to_dir, conditions)


# test 16 - both scan_dir and ref have 1.jpg in the main folder, and also in subfolder sub1, no copy_to_all
def test16(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the scan_dir and ref directories
    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(reference_dir, "sub1"))

    # Setup the files in the scan_dir subdirectories and reference directory
    copy_files([1], scan_dir)
    copy_files([1], reference_dir)
    copy_files([1], os.path.join(scan_dir, "sub1"))
    copy_files([1], os.path.join(reference_dir, "sub1"))

    args = parse_arguments(common_args)
    main(args)

    # Check if all files from scan_dir are now in base folder of move_to
    scan_files = set(os.listdir(scan_dir))
    assert not scan_files, "Scan directory is not empty"

    # Check move_to folder has files 1 or sub1
    move_to_files = set(os.listdir(move_to_dir))
    move_to_has_1 = "1.jpg" in move_to_files
    move_to_has_sub1 = "sub1" in move_to_files
    assert move_to_has_1 or move_to_has_sub1, "Not all files have been moved to move_to directory"
    assert "scan_dups" in move_to_files, "scan_dups not in move_to directory"

    # check that sub1 has file 1
    if move_to_has_sub1:
        move_to_sub_files = set(os.listdir(os.path.join(move_to_dir, "sub1")))
        assert move_to_sub_files == {"1.jpg"}, "Not all files have been moved to move_to subdirectory"

    scan_dup_sub_files = set(os.listdir(os.path.join(move_to_dir, "scan_dups")))

    # scan_dups should have sub1 or 1.jpg
    scan_dups_has_sub1 = "sub1" in scan_dup_sub_files
    scan_dups_has_1 = "1.jpg" in scan_dup_sub_files

    assert scan_dups_has_sub1 or scan_dups_has_1, "Not all files have been moved to move_to subdirectory"

    if scan_dups_has_sub1:
        assert len(scan_dup_sub_files) == 1, "wrong number of files in scan_dups"
        # check that sub1 has file 1
        scan_dup_sub1_files = set(os.listdir(os.path.join(move_to_dir, "scan_dups", "sub1")))
        assert scan_dup_sub1_files == {"1.jpg"}, "Not all files have been moved to move_to subdirectory"

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == {"1.jpg", "sub1"}, "Reference directory files have changed"

    # Check no change to reference subfolder
    ref_sub_files = set(os.listdir(os.path.join(reference_dir, "sub1")))
    assert ref_sub_files == {"1.jpg"}, "Reference sub directory files have changed"


# different names, same content, copy_to_all, different folders in scan_dir and ref, duplicates in scan_dir and ref
def test17(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the scan_dir and ref directories
    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(scan_dir, "sub2"))
    os.makedirs(os.path.join(reference_dir, "sub1"))

    src_file = os.path.join(IMG_DIR, "1.jpg")
    dst1_file = os.path.join(reference_dir, "hw10.jpg")
    dst2_file = os.path.join(reference_dir, "hw11.jpg")
    dst3_file = os.path.join(reference_dir, "sub1", "HW10.jpg")
    dst4_file = os.path.join(reference_dir, "sub1", "Hw11.jpg")

    # reference content:
    # hw10.jpg, hw11.jpg
    # sub1: HW10.jpg, Hw11.jpg

    shutil.copy(src_file, dst1_file)
    shutil.copy(src_file, dst2_file)
    shutil.copy(src_file, dst3_file)
    shutil.copy(src_file, dst4_file)

    shutil.copy(src_file, os.path.join(scan_dir, "sub1", "hw10.jpg"))
    shutil.copy(src_file, os.path.join(scan_dir, "hw10.jpg"))
    shutil.copy(src_file, os.path.join(scan_dir, "sub2", "HW10.jpg"))

    # scan_dir content:
    # sub1: hw10.jpg
    # hw10.jpg
    # sub2: HW10.jpg

    common_args.append("--copy_to_all")
    common_args.append("--ignore_diff")
    common_args.append("filename,mdate")

    args = parse_arguments(common_args)
    main(args)

    # Check if all files from scan_dir are now in base folder of move_to
    scan_files = set(os.listdir(scan_dir))
    assert not scan_files, "Scan directory is not empty"

    # check that move_to has files hw10.jpg, hw11.jpg, sub1
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == {"hw10.jpg", "hw11.jpg", "sub1"}, "wrong files in move_to"

    # check that sub1 has files HW10.jpg, Hw11.jpg
    move_to_sub_files = set(os.listdir(os.path.join(move_to_dir, "sub1")))
    assert move_to_sub_files == {"HW10.jpg", "Hw11.jpg"}, "Not all files have been moved to move_to subdirectory"


# all the tests with the same file content - 1.jpg
# 2 duplicates in source, same name, different folders
# 2 duplicates in the same name but different folders as in source, 8 more duplicates in ref with different name
def setup_for_few_scans_many_refs_tests(scan_dir, reference_dir):
    # Create the necessary subdirectories in the scan_dir and ref directories
    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(reference_dir, "sub1"))

    src_file = os.path.join(IMG_DIR, "1.jpg")

    shutil.copy(src_file, os.path.join(scan_dir, "sub1", "main.jpg"))
    shutil.copy(src_file, os.path.join(scan_dir, "main.jpg"))
    shutil.copy(src_file, os.path.join(reference_dir, "main.jpg"))
    shutil.copy(src_file, os.path.join(reference_dir, "sub1", "main.jpg"))

    for i in range(2, 11):
        shutil.copy(src_file, os.path.join(reference_dir, f"hw{i}.jpg"))

    # scan_dir content:
    # sub1: main.jpg
    # main.jpg

    # reference content:
    # main.jpg
    # sub1: main.jpg
    # hw2.jpg - hw10.jpg


# ignore_diff is set to mdate.
def test_few_scans_many_refs_ignore_diff_mdate(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    setup_for_few_scans_many_refs_tests(scan_dir, reference_dir)

    common_args.append("--ignore_diff")
    common_args.append("mdate")
    common_args.append("--copy_to_all")

    args = parse_arguments(common_args)
    main(args)

    # Check if all files from scan_dir are now in base folder of move_to
    scan_files = set(os.listdir(scan_dir))
    assert not scan_files, "Scan directory is not empty"

    # check that move_to has files main.jpg, sub1
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == {"main.jpg", "sub1"}, "wrong files in move_to"


def test_few_scans_many_refs_ignore_diff_mdate_filename(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    setup_for_few_scans_many_refs_tests(scan_dir, reference_dir)

    common_args.append("--ignore_diff")
    common_args.append("mdate,filename")
    common_args.append("--copy_to_all")

    args = parse_arguments(common_args)
    main(args)

    # Check if all files from scan_dir are now in base folder of move_to
    scan_files = set(os.listdir(scan_dir))
    assert not scan_files, "Scan directory is not empty"

    # check that move_to has files main.jpg, sub1 and hw2.jpg to hw10.jpg
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == {"main.jpg", "sub1"} | {f"hw{i}.jpg" for i in range(2, 11)}, "wrong files in move_to"


def setup_for_many_scans_few_refs_tests(scan_dir, reference_dir):
    # Create the necessary subdirectories in the scan_dir and ref directories
    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(reference_dir, "sub1"))

    src_file = os.path.join(IMG_DIR, "1.jpg")

    shutil.copy(src_file, os.path.join(scan_dir, "sub1", "main.jpg"))
    shutil.copy(src_file, os.path.join(scan_dir, "main.jpg"))
    shutil.copy(src_file, os.path.join(reference_dir, "main.jpg"))
    shutil.copy(src_file, os.path.join(reference_dir, "sub1", "main.jpg"))

    for i in range(2, 11):
        shutil.copy(src_file, os.path.join(scan_dir, f"hw{i}.jpg"))

    # scan_dir content:
    # sub1: main.jpg
    # main.jpg
    # hw2.jpg, hw3.jpg, hw4.jpg, hw5.jpg, hw6.jpg, hw7.jpg, hw8.jpg, hw9.jpg, hw10.jpg

    # reference content:
    # main.jpg
    # sub1: main.jpg


def test_many_scans_few_refs_ignore_diff_mdate(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    setup_for_many_scans_few_refs_tests(scan_dir, reference_dir)

    common_args.append("--ignore_diff")
    common_args.append("mdate")
    common_args.append("--copy_to_all")

    args = parse_arguments(common_args)
    main(args)

    scan_files = set(os.listdir(scan_dir))
    assert scan_files == {f"hw{i}.jpg" for i in range(2, 11)}, "Wrong files in source"

    # check that move_to has files main.jpg, sub1
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == {"main.jpg", "sub1"}, "wrong files in move_to"


def test_many_scans_few_refs_ignore_diff_mdate_extended(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    setup_for_many_scans_few_refs_tests(scan_dir, reference_dir)

    src_file = os.path.join(IMG_DIR, "1.jpg")

    shutil.copy(src_file, os.path.join(scan_dir, "sub1", "main2.jpg"))
    shutil.copy(src_file, os.path.join(scan_dir, "main2.jpg"))
    shutil.copy(src_file, os.path.join(reference_dir, "main2.jpg"))
    shutil.copy(src_file, os.path.join(reference_dir, "sub1", "main2.jpg"))

    common_args.append("--ignore_diff")
    common_args.append("mdate")
    common_args.append("--copy_to_all")

    args = parse_arguments(common_args)
    main(args)

    scan_files = set(os.listdir(scan_dir))
    assert scan_files == {f"hw{i}.jpg" for i in range(2, 11)}, "Wrong files in source"

    # check that move_to has files main.jpg, sub1
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == {"main.jpg", "main2.jpg", "sub1"}, "wrong files in move_to"

    # check that sub1 has files main2.jpg
    move_to_sub_files = set(os.listdir(os.path.join(move_to_dir, "sub1")))
    assert move_to_sub_files == {"main.jpg", "main2.jpg"}, "Not all files have been moved to move_to subdirectory"


def test_many_scans_few_refs_ignore_diff_mdate_filename(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    setup_for_many_scans_few_refs_tests(scan_dir, reference_dir)
    print_all_folders(scan_dir, reference_dir, move_to_dir)

    common_args.append("--ignore_diff")
    common_args.append("mdate,filename")
    common_args.append("--copy_to_all")

    args = parse_arguments(common_args)
    main(args)

    # Check if all files from scan_dir are now in base folder of move_to
    scan_files = set(os.listdir(scan_dir))
    assert not scan_files, "Scan directory is not empty"

    # scans_dups should contain 9 files, in root and maybe in sub1 (if exists)
    conditions = [
        {
            'type': 'files_count_including_subfolders',
            'folder': 'scan_dups',
            'expected_count': 9
        },
        {
            'type': 'items_in_folder',
            'folder': '',
            'items': {"main.jpg", "sub1", "scan_dups"}
        }
    ]
    check_folder_conditions(move_to_dir, conditions)
