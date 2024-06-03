from df_finder3 import main
from duplicate_files_in_folders.utils import parse_arguments
from tests.helpers_testing import *


# Test 1 - content of scan_dir and ref is exactly the same (all duplicates, all in the same base folder)
def test1_same_content_scan_and_ref(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), range(1, 6))
    args = parse_arguments(common_args)
    main(args)

    # Check if all files from scan_dir are now in base folder of move_to
    scan_files = set(os.listdir(scan_dir))
    move_to_files = set(os.listdir(move_to_dir))
    assert not scan_files, "Scan directory is not empty"
    assert move_to_files == set([f"{i}.jpg" for i in range(1, 6)]), "Not all files have been moved to move_to directory"

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == set([f"{i}.jpg" for i in range(1, 6)]), "Reference directory files have changed"


# test 2 - content of scan_dir and ref is totally different
def test2_different_content_scan_and_ref(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 4), range(4, 7))
    args = parse_arguments(common_args)
    main(args)

    # Check that no change in source
    scan_files = set(os.listdir(scan_dir))
    assert scan_files == set([f"{i}.jpg" for i in range(1, 4)]), "Scan directory files have changed"

    # Check move_to folder is empty
    move_to_files = set(os.listdir(move_to_dir))
    assert not move_to_files, "Move_to directory is not empty"

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == set([f"{i}.jpg" for i in range(4, 7)]), "Reference directory files have changed"


# test 3 - mix of unique file in each folder
def test3_unique_and_duplicate_files(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 5), range(3, 7))
    args = parse_arguments(common_args)

    # scan_dir has files 1, 2, 3, 4
    # ref has files 3, 4, 5, 6

    main(args)

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == set([f"{i}.jpg" for i in range(3, 7)]), "Reference directory files have changed"

    # Check scan_dir has files 1, 2
    scan_files = set(os.listdir(scan_dir))
    assert scan_files == set([f"{i}.jpg" for i in range(1, 3)]), "Scan directory files not correct"

    # Check that move_to has files 3,4
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == set([f"{i}.jpg" for i in range(3, 5)]), "Not all files have been moved to move_to directory"

    args.move_to = args.move_to + "_2"
    main(args)

    # check that move_to_2 doesn't exist
    assert not os.path.exists(move_to_dir + "_2"), "Second run of main() should not create move_to_2 directory"


# test 4 - same files, different names
def test4_same_file_different_names(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    copy_files(range(1, 5), os.path.join(TEMP_DIR, SCAN_DIR_NAME))
    for file_number in range(1, 5):
        src_file = os.path.join(IMG_DIR, f"{file_number}.jpg")
        dst_file = os.path.join(TEMP_DIR, REF_DIR_NAME, img_files[file_number]['original_name'])
        shutil.copy(src_file, str(dst_file))

    args = parse_arguments(common_args)
    main(args)

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == set(
        [img_files[i]['original_name'] for i in range(1, 5)]), "Reference directory files have changed"

    # Check that no change in source
    scan_files = set(os.listdir(scan_dir))
    assert scan_files == set([f"{i}.jpg" for i in range(1, 5)]), "Scan directory files have changed"

    # Check move_to folder is empty
    move_to_files = set(os.listdir(move_to_dir))
    assert not move_to_files, "Move_to directory is not empty"

    # Execute main() with additional argument "--ignore_diff filename"
    args = parse_arguments(common_args + ["--ignore_diff", "filename,mdate"])
    main(args)

    # Check if all files from scan_dir are now in base folder of move_to -
    # it should be renamed to the same name as in target
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == set(
        [img_files[i]['original_name'] for i in range(1, 5)]), "Not all files have been moved to move_to directory"

    # check that scan_dir is empty
    scan_files = set(os.listdir(scan_dir))
    assert not scan_files, "Scan directory is not empty"


# Test 5 - scan_dir has files 1 to 5, ref has files 1-2 in its main folder, and files 3 to 5 in sub folder "sub"
def test5(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    copy_files(range(1, 6), os.path.join(TEMP_DIR, SCAN_DIR_NAME))
    copy_files(range(1, 3), os.path.join(TEMP_DIR, REF_DIR_NAME))
    os.makedirs(os.path.join(TEMP_DIR, REF_DIR_NAME, "sub"))
    copy_files(range(3, 6), os.path.join(TEMP_DIR, REF_DIR_NAME, "sub"))

    args = parse_arguments(common_args)
    main(args)

    # Check if all files from scan_dir are now in base folder of move_to
    scan_files = set(os.listdir(scan_dir))
    assert not scan_files, "Scan directory is not empty"

    # move_to should have files 1-2 in main folder and 3-5 in sub folder
    move_to_files = set(os.listdir(move_to_dir))
    # check if files 1-2 are in main folder
    assert set([f"{i}.jpg" for i in range(1, 3)]).issubset(
        move_to_files), "Not all files have been moved to move_to directory"
    # check if files 3-5 are in sub folder
    move_to_sub_files = set(os.listdir(os.path.join(move_to_dir, "sub")))
    assert move_to_sub_files == set(
        [f"{i}.jpg" for i in range(3, 6)]), "Not all files have been moved to move_to directory"

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == set([f"{i}.jpg" for i in range(1, 3)] + ['sub']), "Reference directory files have changed"

    # Check no change to reference subfolder
    ref_sub_files = set(os.listdir(os.path.join(reference_dir, "sub")))
    assert ref_sub_files == set([f"{i}.jpg" for i in range(3, 6)]), "Reference sub directory files have changed"


# Test 6 - files with the same name but different content
def test6(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    filename = "duplicate.txt"

    # Create a file with the same name but different content in the scan_dir and ref directories
    with open(os.path.join(scan_dir, filename), "w") as f:
        f.write("This is some content for the test.")

    with open(os.path.join(reference_dir, filename), "w") as f:
        f.write("Different content, but same size .")

    args = parse_arguments(common_args)
    main(args)

    # Check that no change in source
    scan_files = set(os.listdir(scan_dir))
    assert scan_files == {filename}, "Scan directory files have changed"

    # Check move_to folder is empty
    move_to_files = set(os.listdir(move_to_dir))
    assert not move_to_files, "Move_to directory is not empty"

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == {filename}, "Reference directory files have changed"


# Test 7 - check that without "--run" no action is happening
def test7(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), range(1, 6))

    # Remove the "--run" flag from the arguments
    common_args.remove("--run")
    args = parse_arguments(common_args)
    main(args)

    # Check if all files from scan_dir are still in source
    scan_files = set(os.listdir(scan_dir))
    assert scan_files == set([f"{i}.jpg" for i in range(1, 6)]), "Scan directory files have changed"

    # Check move_to folder is still empty
    move_to_files = set(os.listdir(move_to_dir))
    assert not move_to_files, "Move_to directory is not empty"

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == set([f"{i}.jpg" for i in range(1, 6)]), "Reference directory files have changed"


# Test 8 - check copy_to_all functionality
# file 1 exists only on source
# file 2 exists only on ref
# file 3 exists in scan_dir, in ref base folder and in 2 different subfolders - sub1, sub2
# file 4 exists in scan_dir, and in sub1, sub2 of target
# file 5 exists in scan_dir and ref main folder
# file 6 exists in scan_dir and ref main folder, but with 2 different names on ref
def test8(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the reference directory
    os.makedirs(os.path.join(reference_dir, "sub1"))
    os.makedirs(os.path.join(reference_dir, "sub2"))

    # Setup the files in the scan_dir and ref directories
    copy_files([1], os.path.join(TEMP_DIR, SCAN_DIR_NAME))
    copy_files([2], os.path.join(TEMP_DIR, REF_DIR_NAME))
    copy_files([3], os.path.join(TEMP_DIR, SCAN_DIR_NAME))
    copy_files([3], os.path.join(TEMP_DIR, REF_DIR_NAME))
    copy_files([3], os.path.join(TEMP_DIR, REF_DIR_NAME, "sub1"))
    copy_files([3], os.path.join(TEMP_DIR, REF_DIR_NAME, "sub2"))
    copy_files([4], os.path.join(TEMP_DIR, SCAN_DIR_NAME))
    copy_files([4], os.path.join(TEMP_DIR, REF_DIR_NAME, "sub1"))
    copy_files([4], os.path.join(TEMP_DIR, REF_DIR_NAME, "sub2"))
    copy_files([5], os.path.join(TEMP_DIR, SCAN_DIR_NAME))
    copy_files([5], os.path.join(TEMP_DIR, REF_DIR_NAME))
    copy_files([6], os.path.join(TEMP_DIR, SCAN_DIR_NAME))
    copy_files([6], os.path.join(TEMP_DIR, REF_DIR_NAME))
    src_file = os.path.join(IMG_DIR, f"6.jpg")
    dst_file = os.path.join(TEMP_DIR, REF_DIR_NAME, img_files[6]['original_name'])
    shutil.copy(src_file, str(dst_file))

    # Add the "--copy_to_all" flag to the arguments
    common_args.append("--copy_to_all")

    # Execute main() with additional argument "--ignore_diff filename" for file 6
    common_args.append("--ignore_diff")
    common_args.append("filename,mdate")

    args = parse_arguments(common_args)
    main(args)

    # Scan folder should have file 1 only
    scan_files = set(os.listdir(scan_dir))
    assert scan_files == {"1.jpg"}, "Scan directory files not correct"

    # root move_to should have files 3, 5, 6, sub1, sub2 and original name of file 6
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == {f"3.jpg", f"5.jpg", f"6.jpg", "sub1", "sub2", img_files[6]['original_name']}, \
        "Not all files have been moved to move_to directory"

    # check that sub1 and sub2 have file 3.jpg and 4.jpg and nothing else
    move_to_sub1_files = set(os.listdir(os.path.join(move_to_dir, "sub1")))
    move_to_sub2_files = set(os.listdir(os.path.join(move_to_dir, "sub2")))
    assert move_to_sub1_files == move_to_sub2_files == {f"3.jpg", f"4.jpg"}, \
        "Not all files have been moved to sub folders"

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == set([f"{i}.jpg" for i in [2, 3, 5, 6]] + ['sub1', 'sub2', img_files[6]['original_name']]), \
        "Reference directory files have changed"

    # Check no change to reference subfolders
    ref_sub1_files = set(os.listdir(os.path.join(reference_dir, "sub1")))
    ref_sub2_files = set(os.listdir(os.path.join(reference_dir, "sub2")))
    assert ref_sub1_files == ref_sub2_files == {f"3.jpg", f"4.jpg"}, "Reference sub directory files have changed"

    args.move_to = args.move_to + "_2"
    main(args)

    # check that move_to_2 doesn't exist
    assert not os.path.exists(move_to_dir + "_2"), "Second run of main() should not create move_to_2 directory"


# Test 10 - files 1 to 5 in scan_dir subfolder sub1, files 1-5 in ref base folder
def test10(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectory in the scan_dir directory
    os.makedirs(os.path.join(scan_dir, "sub1"))

    # Setup the files in the scan_dir subdirectory and reference directory
    copy_files(range(1, 6), os.path.join(scan_dir, "sub1"))
    copy_files(range(1, 6), reference_dir)

    args = parse_arguments(common_args)
    main(args)

    # Check if all files from scan_dir subdirectory are now in base folder of move_to
    scan_sub_files = set(os.listdir(scan_dir))
    assert not scan_sub_files, "Scan_dir subdirectory is not empty"

    # Check move_to folder has files 1-5
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == set([f"{i}.jpg" for i in range(1, 6)]), "Not all files have been moved to move_to directory"

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == set([f"{i}.jpg" for i in range(1, 6)]), "Reference directory files have changed"


# Test 11 - files 1 to 5 in scan_dir subfolder sub1, files 1-3 in ref base folder, files 4-5 in ref subfolder sub1
def test11(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    # Create the necessary subdirectories in the scan_dir and ref directories
    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(reference_dir, "sub1"))

    # Setup the files in the scan_dir subdirectory and ref directory
    copy_files(range(1, 6), os.path.join(scan_dir, "sub1"))
    copy_files(range(1, 4), reference_dir)
    copy_files(range(4, 6), os.path.join(reference_dir, "sub1"))

    args = parse_arguments(common_args)
    main(args)

    # Check if all files from scan_dir are now in base folder of move_to
    scan_sub_files = set(os.listdir(scan_dir))
    assert not scan_sub_files, "Source is not empty"

    # Check move_to folder has files 1-3
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == set([f"{i}.jpg" for i in range(1, 4)] + ['sub1']), \
        "Not all files have been moved to move_to directory"

    # Check move_to subfolder has files 4-5
    move_to_sub_files = set(os.listdir(os.path.join(move_to_dir, "sub1")))
    assert move_to_sub_files == set([f"{i}.jpg" for i in range(4, 6)]), \
        "Not all files have been moved to move_to subdirectory"

    # Check no change to reference folder
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == set([f"{i}.jpg" for i in range(1, 4)] + ['sub1']), "Reference directory files have changed"

    # Check no change to reference subfolder
    ref_sub_files = set(os.listdir(os.path.join(reference_dir, "sub1")))
    assert ref_sub_files == set([f"{i}.jpg" for i in range(4, 6)]), "Reference sub directory files have changed"


def test_3_duplicates_on_scan_2_on_ref_same_filename(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(scan_dir, "sub2"))
    os.makedirs(os.path.join(reference_dir, "sub1"))

    src_file = os.path.join(IMG_DIR, "1.jpg")

    shutil.copy(src_file, os.path.join(scan_dir, "sub1", "1.jpg"))
    shutil.copy(src_file, os.path.join(scan_dir, "1.jpg"))
    shutil.copy(src_file, os.path.join(scan_dir, "sub2", "1.jpg"))

    shutil.copy(src_file, os.path.join(reference_dir, "sub1", "1.jpg"))
    shutil.copy(src_file, os.path.join(reference_dir, "1.jpg"))

    common_args.append("--copy_to_all")
    common_args.append("--ignore_diff")
    common_args.append("filename,mdate")

    args = parse_arguments(common_args)
    main(args)

    scan_files = set(os.listdir(scan_dir))
    assert not scan_files, "Scan directory is not empty"


def test_duplicates_on_nested_folders_scan_and_target(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(scan_dir, "sub1", "sub2"))

    os.makedirs(os.path.join(scan_dir, "sub2"))
    os.makedirs(os.path.join(scan_dir, "sub2", "sub2"))

    os.makedirs(os.path.join(reference_dir, "sub2"))
    os.makedirs(os.path.join(reference_dir, "sub2", "sub2"))

    src_file = os.path.join(IMG_DIR, "1.jpg")

    shutil.copy(src_file, os.path.join(scan_dir, "sub1", "sub2", "1.jpg"))
    shutil.copy(src_file, os.path.join(scan_dir, "sub1", "1.jpg"))
    shutil.copy(src_file, os.path.join(scan_dir, "1.jpg"))

    shutil.copy(src_file, os.path.join(scan_dir, "sub2", "sub2", "1.jpg"))
    shutil.copy(src_file, os.path.join(scan_dir, "sub2", "1.jpg"))

    shutil.copy(src_file, os.path.join(reference_dir, "sub2", "sub2", "1.jpg"))
    shutil.copy(src_file, os.path.join(reference_dir, "sub2", "1.jpg"))
    shutil.copy(src_file, os.path.join(reference_dir, "1.jpg"))

    common_args.append("--copy_to_all")
    common_args.append("--ignore_diff")
    common_args.append("mdate")

    args = parse_arguments(common_args)
    main(args)

    scan_files = set(os.listdir(scan_dir))
    assert not scan_files, "Scan directory is not empty"


# this was a bug I couldn't reproduce, so I created a minimal test case with the same structure
def test18(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    shutil.copytree(os.path.join(BASE_DIR, "learn2_bug_minimal", "source"), scan_dir, dirs_exist_ok=True)
    shutil.copytree(os.path.join(BASE_DIR, "learn2_bug_minimal", "target"), reference_dir, dirs_exist_ok=True)

    common_args.append("--copy_to_all")
    common_args.append("--ignore_diff")
    common_args.append("filename,mdate")

    args = parse_arguments(common_args)
    main(args)

    scan_files = set(os.listdir(scan_dir))
    assert not scan_files, "Scan directory is not empty"
