import os

from df_finder3 import main, parse_arguments
from tests.helpers_testing import *


def test_empty_source_folder(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    setup_test_files([], range(1, 6))

    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1


def test_empty_target_folder(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [])

    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1


def test_non_existing_source_folder(setup_teardown):
    _, target_dir, move_to_dir, _ = setup_teardown
    source_dir = os.path.join(TEMP_DIR, "non_existing_folder")
    setup_test_files([], range(1, 6))
    custom_args = ["--src", source_dir, "--target", target_dir, "--move_to", move_to_dir, "--run"]

    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(custom_args)
        main(args)
    assert excinfo.type == SystemExit


def test_non_existing_target_folder(setup_teardown):
    source_dir, _, move_to_dir, _ = setup_teardown
    target_dir = os.path.join(TEMP_DIR, "non_existing_folder")
    setup_test_files(range(1, 6), [])
    custom_args = ["--src", source_dir, "--target", target_dir, "--move_to", move_to_dir, "--run"]

    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(custom_args)
        main(args)
    assert excinfo.type == SystemExit


def test_source_folder_inside_target_folder_or_move_to_folder(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    common_args = ["--src", os.path.join(target_dir, "source"), "--target", target_dir, "--move_to",
                   move_to_dir, "--run"]
    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

    common_args = ["--src", os.path.join(move_to_dir, "source"), "--target", target_dir, "--move_to",
                      move_to_dir, "--run"]
    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1


def test_target_folder_inside_source_folder_or_move_to_folder(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    common_args = ["--src", source_dir, "--target", os.path.join(source_dir, "target"), "--move_to",
                   move_to_dir, "--run"]
    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

    common_args = ["--src", source_dir, "--target", os.path.join(move_to_dir, "target"), "--move_to",
                      move_to_dir, "--run"]
    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1


def test_move_to_folder_inside_source_folder_or_target_folder(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    common_args = ["--src", source_dir, "--target", target_dir, "--move_to",
                   os.path.join(source_dir, "move_to"), "--run"]
    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1

    common_args = ["--src", source_dir, "--target", target_dir, "--move_to",
                      os.path.join(target_dir, "move_to"), "--run"]
    with pytest.raises(SystemExit) as excinfo:
        args = parse_arguments(common_args)
        main(args)
    assert excinfo.type == SystemExit
    assert excinfo.value.code == 1


# run the script from the command line to test main block
def test_running_main_block(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), range(1, 6))
    common_args.append("--run")

    # run the script from the command line - don't call main() directly
    os.system(f"python df_finder3.py {' '.join(common_args)}")

    # Check if all files from source are now in base folder of move_to
    source_files = set(os.listdir(source_dir))
    assert not source_files, "Source directory is not empty"
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == set(
        [f"{i}.jpg" for i in range(1, 6)]), "Not all files have been moved to move_to directory"

    # Check no change to target
    target_files = set(os.listdir(target_dir))
    assert target_files == set([f"{i}.jpg" for i in range(1, 6)]), "Target directory files have changed"


# simple test - test --extra_logging flag - should work without errors
def test_extra_logging(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 5), range(3, 7))
    common_args.append("--extra_logging")
    args = parse_arguments(common_args)
    main(args)

    assert args.extra_logging, "Extra logging flag not set"

    # Check no change to target
    target_files = set(os.listdir(target_dir))
    assert target_files == set([f"{i}.jpg" for i in range(3, 7)]), "Target directory files have changed"

    # Check source has files 1, 2
    source_files = set(os.listdir(source_dir))
    assert source_files == set([f"{i}.jpg" for i in range(1, 3)]), "Source directory files not correct"

    # Check that move_to has files 3,4
    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == set([f"{i}.jpg" for i in range(3, 5)]), "Not all files have been moved to move_to directory"


# test that if args.run but delete_empty_folders is false, then empty folders are not deleted
def test_delete_empty_folders_false(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), range(1, 6))

    # copy to source sub1 folder too
    os.makedirs(os.path.join(source_dir, "sub1"))
    copy_files(range(1, 6), os.path.join(source_dir, "sub1"))

    common_args.append("--run")
    common_args.append("--no-delete_empty_folders")
    args = parse_arguments(common_args)
    main(args)

    # sub1 folder should still be there
    source_files = set(os.listdir(source_dir))
    assert source_files == {"sub1"}, "Empty folders have been deleted"

    move_to_files = set(os.listdir(move_to_dir))
    assert move_to_files == set(
        [f"{i}.jpg" for i in range(1, 6)] + ["source_dups"]), "Not all files have been moved to move_to directory"

    # Check no change to target
    target_files = set(os.listdir(target_dir))
    assert target_files == set([f"{i}.jpg" for i in range(1, 6)]), "Target directory files have changed"


# test slash at end of folder name - should work without errors
def test_source_folder_slash(setup_teardown):
    source_dir, target_dir, move_to_dir, _ = setup_teardown
    setup_test_files(range(1, 4), range(1, 4))
    common_args = ["--src", source_dir + os.sep, "--target", target_dir, "--move_to", move_to_dir, "--run"]
    args = parse_arguments(common_args)
    main(args)

    simple_usecase_test(source_dir, target_dir, move_to_dir, 3)


# test slash at end of folder name - should work without errors
def test_target_folder_slash(setup_teardown):
    source_dir, target_dir, move_to_dir, _ = setup_teardown
    setup_test_files(range(1, 4), range(1, 4))
    common_args = ["--src", source_dir, "--target", target_dir + os.sep, "--move_to", move_to_dir, "--run"]
    args = parse_arguments(common_args)
    main(args)

    simple_usecase_test(source_dir, target_dir, move_to_dir, 3)


# test slash at end of folder name - should work without errors
def test_move_to_folder_slash(setup_teardown):
    source_dir, target_dir, move_to_dir, _ = setup_teardown
    setup_test_files(range(1, 4), range(1, 4))
    common_args = ["--src", source_dir, "--target", target_dir, "--move_to", move_to_dir + os.sep, "--run"]
    args = parse_arguments(common_args)
    main(args)

    simple_usecase_test(source_dir, target_dir, move_to_dir, 3)


def test_source_argument_instead_of_src_to_instead_of_move_to(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 4), range(1, 4))
    common_args = ["--source", source_dir, "--target", target_dir, "--to", move_to_dir, "--run"]
    args = parse_arguments(common_args)
    main(args)

    simple_usecase_test(source_dir, target_dir, move_to_dir, 3)
