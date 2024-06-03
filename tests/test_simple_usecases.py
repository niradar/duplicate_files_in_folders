from df_finder3 import main
from duplicate_files_in_folders.utils import parse_arguments
from tests.helpers_testing import *


def test_empty_scan_folder(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files([], range(1, 6))

    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2


def test_empty_reference_folder(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [])

    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2


def test_non_existing_scan_folder(setup_teardown):
    _, reference_dir, move_to_dir, _ = setup_teardown
    scan_dir = os.path.join(TEMP_DIR, "non_existing_folder")
    setup_test_files([], range(1, 6))
    custom_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run"]

    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(custom_args)
        main(args)
    assert excinfo.type == SystemExit


def test_non_existing_reference_folder(setup_teardown):
    scan_dir, _, move_to_dir, _ = setup_teardown
    reference_dir = os.path.join(TEMP_DIR, "non_existing_folder")
    setup_test_files(range(1, 6), [])
    custom_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run"]

    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(custom_args)
        main(args)
    assert excinfo.type == SystemExit


def test_scan_folder_inside_reference_folder_or_move_to_folder(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    common_args = ["--scan", os.path.join(reference_dir, SCAN_DIR_NAME), "--reference_dir", reference_dir, "--move_to",
                   move_to_dir, "--run"]
    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2

    common_args = ["--scan", os.path.join(move_to_dir, SCAN_DIR_NAME), "--reference_dir", reference_dir, "--move_to",
                   move_to_dir, "--run"]
    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2


def test_reference_folder_inside_scan_folder_or_move_to_folder(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    common_args = ["--scan", scan_dir, "--reference_dir", os.path.join(scan_dir, "target"), "--move_to",
                   move_to_dir, "--run"]
    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2

    common_args = ["--scan", scan_dir, "--reference_dir", os.path.join(move_to_dir, REF_DIR_NAME), "--move_to",
                   move_to_dir, "--run"]
    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2


def test_move_to_folder_inside_scan_folder_or_reference_folder(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to",
                   os.path.join(scan_dir, "move_to"), "--run"]
    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2

    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to",
                   os.path.join(reference_dir, "move_to"), "--run"]
    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 2


# run the script from the command line to test main block
def test_running_main_block(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), range(1, 6))
    common_args.append("--run")

    # run the script from the command line - don't call main() directly
    os.system(f"python df_finder3.py {' '.join(common_args)}")

    # Check if all files from scan_dir are now in base folder of move_to
    scan_files = set(os.listdir(scan_dir))
    assert not scan_files, "Scan directory is not empty"
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == set(
        [f"{i}.jpg" for i in range(1, 6)]), "Not all files have been moved to move_to directory"

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == set([f"{i}.jpg" for i in range(1, 6)]), "Reference directory files have changed"


# simple test - test --extra_logging flag - should work without errors
def test_extra_logging(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 5), range(3, 7))
    common_args.append("--extra_logging")
    args = parse_arguments(common_args)
    main(args)

    assert args.extra_logging, "Extra logging flag not set"

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == set([f"{i}.jpg" for i in range(3, 7)]), "Reference directory files have changed"

    # Check scan_dir has files 1, 2
    scan_files = set(os.listdir(scan_dir))
    assert scan_files == set([f"{i}.jpg" for i in range(1, 3)]), "Scan directory files not correct"

    # Check that move_to has files 3,4
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == set([f"{i}.jpg" for i in range(3, 5)]), "Not all files have been moved to move_to directory"


# test that if args.run but delete_empty_folders is false, then empty folders are not deleted
def test_delete_empty_folders_false(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), range(1, 6))

    # copy to scan_dir sub1 folder too
    os.makedirs(os.path.join(scan_dir, "sub1"))
    copy_files(range(1, 6), os.path.join(scan_dir, "sub1"))

    common_args.append("--run")
    common_args.append("--keep_empty_folders")
    args = parse_arguments(common_args)
    main(args)

    # sub1 folder should still be there
    scan_files = set(os.listdir(scan_dir))
    assert scan_files == {"sub1"}, "Empty folders have been deleted"

    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == set(
        [f"{i}.jpg" for i in range(1, 6)] + ["scan_dups"]), "Not all files have been moved to move_to directory"

    # Check no change to reference
    ref_files = set(os.listdir(reference_dir))
    assert ref_files == set([f"{i}.jpg" for i in range(1, 6)]), "Reference directory files have changed"


# test slash at end of folder name - should work without errors
def test_scan_folder_slash(setup_teardown):
    scan_dir, reference_dir, move_to_dir, _ = setup_teardown
    setup_test_files(range(1, 4), range(1, 4))
    common_args = ["--scan", scan_dir + os.sep, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run"]
    args = parse_arguments(common_args)
    main(args)

    simple_usecase_test(scan_dir, reference_dir, move_to_dir, 3)


# test slash at end of folder name - should work without errors
def test_reference_folder_slash(setup_teardown):
    scan_dir, reference_dir, move_to_dir, _ = setup_teardown
    setup_test_files(range(1, 4), range(1, 4))
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir + os.sep, "--move_to", move_to_dir, "--run"]
    args = parse_arguments(common_args)
    main(args)

    simple_usecase_test(scan_dir, reference_dir, move_to_dir, 3)


# test slash at end of folder name - should work without errors
def test_move_to_folder_slash(setup_teardown):
    scan_dir, reference_dir, move_to_dir, _ = setup_teardown
    setup_test_files(range(1, 4), range(1, 4))
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir + os.sep, "--run"]
    args = parse_arguments(common_args)
    main(args)

    simple_usecase_test(scan_dir, reference_dir, move_to_dir, 3)


def test_scan_argument_instead_of_src_to_instead_of_move_to(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 4), range(1, 4))
    common_args = ["--scan_dir", scan_dir, "--reference_dir", reference_dir, "--to", move_to_dir, "--run"]
    args = parse_arguments(common_args)
    main(args)

    simple_usecase_test(scan_dir, reference_dir, move_to_dir, 3)


def test_old_script_sanity(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 4), range(1, 4))
    common_args.append("--old_script")
    args = parse_arguments(common_args)
    assert args.old_script, "Old script flag not set"
    main(args)

    simple_usecase_test(scan_dir, reference_dir, move_to_dir, 3)
