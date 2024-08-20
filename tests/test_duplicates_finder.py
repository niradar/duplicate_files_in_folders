import time

from duplicate_files_in_folders.duplicates_finder import find_duplicates_files_v3, process_duplicates
from duplicate_files_in_folders.file_manager import FileManager
from duplicate_files_in_folders.utils import parse_arguments, get_file_key
from tests.helpers_testing import *

logger = logging.getLogger(__name__)


def test_get_file_key(setup_teardown):
    scan_dir, reference_dir, move_to_dir, _ = setup_teardown
    setup_test_files(range(1, 6), range(1, 6))

    file_info = FileManager.get_file_info(os.path.join(scan_dir, "1.jpg"))

    # default args are to ignore mdate
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run"]
    args = parse_arguments(common_args)
    key = get_file_key(args, file_info['path'])
    assert key == 'edb36987f4e3526039ff5c174bcebb9513d95dbc235fb093806c8387dc9ffa91_1.jpg'

    # ignore filename
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
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
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "filename,mdate"]
    args = parse_arguments(common_args)
    key = get_file_key(args, file_info['path'])  # suppose to be only the hash
    assert key == 'edb36987f4e3526039ff5c174bcebb9513d95dbc235fb093806c8387dc9ffa91'

    # ignore none
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "none"]
    args = parse_arguments(common_args)
    key = get_file_key(args, file_info['path'])
    # split key to hash and the rest
    key_parts = key.split('_')
    assert key_parts[0] == 'edb36987f4e3526039ff5c174bcebb9513d95dbc235fb093806c8387dc9ffa91'
    assert key_parts[1] == file_info['name']
    assert key_parts[2] == str(os.path.getmtime(file_info['path']))


def test_find_duplicate_files_v3_same_scan_and_target(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [])
    time.sleep(0.1)  # sleep to make sure the modified date is different
    setup_test_files([], range(1, 6))

    # default args are to ignore mdate
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    assert len(duplicates) == 5
    assert len(scan_stats) == 5
    assert len(ref_stats) == 5

    # ignore filename
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "filename"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    assert len(duplicates) == 0
    assert len(scan_stats) == 5
    assert len(ref_stats) == 5

    # ignore mdate, filename
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "filename,mdate"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    assert len(duplicates) == 5
    assert len(scan_stats) == 5
    assert len(ref_stats) == 5

    # ignore none
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "none"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    assert len(duplicates) == 0
    assert len(scan_stats) == 5
    assert len(ref_stats) == 5


def test_find_duplicate_files_v3_different_scan_and_target(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 4), range(4, 7))

    # default args are to ignore mdate
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    assert len(duplicates) == 0
    assert len(scan_stats) == 3
    assert len(ref_stats) == 3

    # ignore filename
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "filename"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    assert len(duplicates) == 0
    assert len(scan_stats) == 3
    assert len(ref_stats) == 3

    # ignore mdate, filename
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "filename,mdate"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    assert len(duplicates) == 0
    assert len(scan_stats) == 3
    assert len(ref_stats) == 3

    # ignore none
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "none"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    assert len(duplicates) == 0
    assert len(scan_stats) == 3
    assert len(ref_stats) == 3


def test_find_duplicate_files_v3_unique_and_duplicate_files(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [])
    time.sleep(0.1)  # sleep to make sure the modified date is different
    setup_test_files([], range(4, 9))

    # default args are to ignore mdate
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    assert len(duplicates) == 2
    assert len(scan_stats) == 5
    assert len(ref_stats) == 5

    # ignore filename
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "filename"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    assert len(duplicates) == 0
    assert len(scan_stats) == 5
    assert len(ref_stats) == 5

    # ignore mdate, filename
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "filename,mdate"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    assert len(duplicates) == 2
    assert len(scan_stats) == 5
    assert len(ref_stats) == 5

    # ignore none
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "none"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    assert len(duplicates) == 0
    assert len(scan_stats) == 5
    assert len(ref_stats) == 5


def test_process_duplicates_keep_structure(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    os.makedirs(os.path.join(scan_dir, "subfolder"))
    setup_test_files(range(1, 6), [])
    setup_test_files(range(6, 11), [], base_dir=os.path.join(scan_dir, "subfolder"))
    time.sleep(0.1)  # sleep to make sure the modified date is different
    setup_test_files([], range(1, 11))

    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run", "--keep_structure"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    files_moved, files_created = process_duplicates(duplicates, args)

    assert files_created == 0
    assert files_moved == 10
    assert os.path.exists(os.path.join(move_to_dir, "subfolder", "6.jpg"))
    assert os.path.exists(os.path.join(move_to_dir, "subfolder", "7.jpg"))
    assert os.path.exists(os.path.join(move_to_dir, "subfolder", "8.jpg"))
    assert os.path.exists(os.path.join(move_to_dir, "subfolder", "9.jpg"))
    assert os.path.exists(os.path.join(move_to_dir, "subfolder", "10.jpg"))
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [])
    time.sleep(0.1)  # sleep to make sure the modified date is different
    setup_test_files([], range(1, 6))

    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    files_moved, files_created = process_duplicates(duplicates, args)
    assert files_created == 0
    assert files_moved == 5

    # reset the files
    setup_test_files(range(1, 6), [])
    shutil.rmtree(move_to_dir)
    os.makedirs(move_to_dir)

    # ignore filename
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "filename"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    files_moved, files_created = process_duplicates(duplicates, args)
    assert files_created == 0
    assert files_moved == 0

    # ignore none
    # no need to reset the files
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "none"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    files_moved, files_created = process_duplicates(duplicates, args)
    assert files_created == 0
    assert files_moved == 0

    # ignore mdate, filename
    # no need to reset the files
    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run",
                   "--ignore_diff", "filename,mdate"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    files_moved, files_created = process_duplicates(duplicates, args)
    assert files_created == 0
    assert files_moved == 5

    # reset the files
    setup_test_files(range(1, 6), [])  # reset the files
    shutil.rmtree(move_to_dir)
    os.makedirs(move_to_dir)

    os.makedirs(os.path.join(reference_dir, "subfolder"))
    copy_files(range(1, 6), os.path.join(reference_dir, "subfolder"))
    common_args = ["--s", scan_dir, "--r", reference_dir, "--move_to", move_to_dir, "--run", "--copy_to_all"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    files_moved, files_created = process_duplicates(duplicates, args)
    assert files_created == 5
    assert files_moved == 5
    assert os.path.exists(os.path.join(move_to_dir, "subfolder"))

    # reset the files
    setup_test_files(range(1, 6), [])  # reset the files
    shutil.rmtree(move_to_dir)
    os.makedirs(move_to_dir)

    common_args = ["--scan", scan_dir, "--reference_dir", reference_dir, "--move_to", move_to_dir, "--run"]
    args = parse_arguments(common_args)
    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, scan_dir, reference_dir)
    files_moved, files_created = process_duplicates(duplicates, args)
    assert files_created == 0
    assert files_moved == 5
