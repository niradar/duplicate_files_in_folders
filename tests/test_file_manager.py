from tests.helpers_testing import *
from pathlib import Path
from duplicate_files_in_folders.file_manager import FileManager


def test_move_file(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [2])
    fm = FileManager(True).reset_all()
    fm.add_protected_dir(reference_dir)
    file_to_move = os.path.join(scan_dir, "1.jpg")
    dst_file = os.path.join(reference_dir, "1.jpg")

    # move to protected directory should fail
    with pytest.raises(file_manager.ProtectedPathError):
        fm.move_file(file_to_move, dst_file)

    # move from unprotected directory to unprotected directory should work
    fm.move_file(file_to_move, os.path.join(move_to_dir, "1.jpg"))
    assert os.path.exists(os.path.join(move_to_dir, "1.jpg"))
    assert not os.path.exists(file_to_move)

    # move from protected directory should fail too
    file_to_move = os.path.join(reference_dir, "2.jpg")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.move_file(file_to_move, os.path.join(move_to_dir, "2.jpg"))
    assert os.path.exists(file_to_move)
    assert not os.path.exists(os.path.join(move_to_dir, "2.jpg"))

    # now add allowed directory setting
    fm.add_allowed_dir(scan_dir)
    file_to_move = os.path.join(scan_dir, "3.jpg")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.move_file(file_to_move, os.path.join(move_to_dir, "3.jpg"))  # should fail as move_to_dir is not allowed
    assert os.path.exists(file_to_move)
    assert not os.path.exists(os.path.join(move_to_dir, "3.jpg"))

    fm.add_allowed_dir(move_to_dir)
    fm.move_file(file_to_move, os.path.join(move_to_dir, "3.jpg"))  # should work now


def test_copy_file(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [2, 3])
    fm = FileManager(True).reset_all()
    fm.add_protected_dir(reference_dir)
    file_to_copy = os.path.join(scan_dir, "1.jpg")
    dst_file = os.path.join(reference_dir, "1.jpg")

    # copy from unprotected directory to protected directory should fail
    with pytest.raises(file_manager.ProtectedPathError):
        fm.copy_file(file_to_copy, dst_file)

    # copy from unprotected directory to unprotected directory should work
    fm.copy_file(file_to_copy, os.path.join(move_to_dir, "1.jpg"))
    assert os.path.exists(os.path.join(move_to_dir, "1.jpg"))
    assert os.path.exists(file_to_copy)

    # copy from protected directory to unprotected directory should work
    file_to_copy = os.path.join(reference_dir, "2.jpg")
    fm.copy_file(file_to_copy, os.path.join(move_to_dir, "2.jpg"))
    assert os.path.exists(os.path.join(move_to_dir, "2.jpg"))
    assert os.path.exists(file_to_copy)

    # copy from protected directory to protected directory should fail
    file_to_copy = os.path.join(reference_dir, "3.jpg")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.copy_file(file_to_copy, os.path.join(reference_dir, "4.jpg"))
    assert os.path.exists(file_to_copy)
    assert not os.path.exists(os.path.join(reference_dir, "4.jpg"))

    # now add allowed directory setting
    fm.add_allowed_dir(scan_dir)
    file_to_copy = os.path.join(scan_dir, "5.jpg")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.copy_file(file_to_copy, os.path.join(move_to_dir, "5.jpg"))
    assert os.path.exists(file_to_copy)
    assert not os.path.exists(os.path.join(move_to_dir, "5.jpg"))

    fm.add_allowed_dir(move_to_dir)
    fm.copy_file(file_to_copy, os.path.join(move_to_dir, "5.jpg"))  # should work now
    assert os.path.exists(os.path.join(move_to_dir, "5.jpg"))
    assert os.path.exists(file_to_copy)


def test_delete_file(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [2, 3])
    fm = FileManager(True).reset_all()
    fm.add_protected_dir(reference_dir)
    file_to_delete = os.path.join(scan_dir, "1.jpg")

    # delete from unprotected directory should work
    fm.delete_file(file_to_delete)
    assert not os.path.exists(file_to_delete)

    # delete from protected directory should fail
    file_to_delete = os.path.join(reference_dir, "2.jpg")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.delete_file(file_to_delete)
    assert os.path.exists(file_to_delete)

    # copy 3.jpg to move_to_dir
    shutil.copy(os.path.join(scan_dir, "3.jpg"), os.path.join(move_to_dir, "3.jpg"))

    # now add allowed directory setting - scan_dir should be allowed but move_to_dir should not be allowed
    fm.add_allowed_dir(scan_dir)
    file_to_delete = os.path.join(scan_dir, "3.jpg")

    fm.delete_file(file_to_delete)
    assert not os.path.exists(file_to_delete)

    file_to_delete = os.path.join(move_to_dir, "3.jpg")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.delete_file(file_to_delete)
    assert os.path.exists(file_to_delete)


def test_make_dirs(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    fm = FileManager(True).reset_all()
    fm.add_protected_dir(reference_dir)
    dir_to_make = os.path.join(scan_dir, "new_dir")

    # make dir in unprotected directory should work
    fm.make_dirs(dir_to_make)
    assert os.path.exists(dir_to_make)

    # make dir in protected directory should fail
    dir_to_make = os.path.join(reference_dir, "new_dir")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.make_dirs(dir_to_make)
    assert not os.path.exists(dir_to_make)

    # makedirs should work with multiple levels
    dir_to_make = os.path.join(scan_dir, "another_new_dir", "sub_dir", "sub_sub_dir")
    fm.make_dirs(dir_to_make)
    assert os.path.exists(dir_to_make)

    # now add allowed directory setting
    fm.add_allowed_dir(scan_dir)
    dir_to_make = os.path.join(scan_dir, "another_new_dir", "sub_dir", "sub_sub_dir2")
    fm.make_dirs(dir_to_make)
    assert os.path.exists(dir_to_make)

    dir_to_make = os.path.join(move_to_dir, "another_new_dir", "sub_dir", "sub_sub_dir3")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.make_dirs(dir_to_make)
    assert not os.path.exists(dir_to_make)


def test_rmdir(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    fm = FileManager(True).reset_all()
    fm.add_protected_dir(reference_dir)
    dir_to_remove = os.path.join(scan_dir, "new_dir")
    os.makedirs(dir_to_remove)

    # remove dir in unprotected directory should work
    fm.rmdir(dir_to_remove)
    assert not os.path.exists(dir_to_remove)

    # remove dir in protected directory should fail
    dir_to_remove = os.path.join(reference_dir, "new_dir")
    os.makedirs(dir_to_remove)
    with pytest.raises(file_manager.ProtectedPathError):
        fm.rmdir(dir_to_remove)
    assert os.path.exists(dir_to_remove)

    # rmdir should work with multiple levels
    dir_to_remove = os.path.join(scan_dir, "another_new_dir", "sub_dir", "sub_sub_dir")
    os.makedirs(dir_to_remove)
    fm.rmdir(dir_to_remove)
    assert not os.path.exists(dir_to_remove)

    # now add allowed directory setting
    fm.add_allowed_dir(scan_dir)
    dir_to_remove = os.path.join(scan_dir, "another_new_dir", "sub_dir", "sub_sub_dir2")
    os.makedirs(dir_to_remove)
    fm.rmdir(dir_to_remove)
    assert not os.path.exists(dir_to_remove)

    dir_to_remove = os.path.join(move_to_dir, "another_new_dir", "sub_dir", "sub_sub_dir3")
    os.makedirs(dir_to_remove)
    with pytest.raises(file_manager.ProtectedPathError):
        fm.rmdir(dir_to_remove)
    assert os.path.exists(dir_to_remove)


# The FileManager class should be a singleton, so we should not be able to create multiple instances of it.
def test_singleton():
    fm1 = FileManager(True)
    fm2 = FileManager(True)
    assert fm1 is fm2
    assert fm1 == fm2
    assert fm1 is not None
    assert fm2 is not None


def test_add_protected_dir():
    fm = FileManager(True).reset_all()
    fm.add_protected_dir("C:\\")
    fm.add_protected_dir("D:\\")
    assert len(fm.protected_dirs) == 2
    assert Path("C:\\").resolve() in fm.protected_dirs
    assert Path("D:\\").resolve() in fm.protected_dirs


def get_folder_files_as_set(folder):
    ret = set()
    for root, dirs, files in os.walk(folder):
        for file in files:
            ret.add(os.path.join(root, file))
    return ret


def test_list_tree_os_scandir_bfs_simple(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [2, 3])
    fm = FileManager.get_instance()

    scan_files = get_folder_files_as_set(scan_dir)
    scan_tree = fm.list_tree_os_scandir_bfs(scan_dir)  # result is in the form of full path
    assert set(scan_tree) == scan_files

    ref_files = get_folder_files_as_set(reference_dir)
    ref_tree = fm.list_tree_os_scandir_bfs(reference_dir)  # result is in the form of full path
    assert set(ref_tree) == ref_files


# files only in scan_dir - root folder has 3 files and 2 sub folders. each sub folder has some files and 2 sub folders.
# goes 3 levels deep.
def test_list_tree_os_scandir_bfs_tree_with_many_subfolders(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown

    os.makedirs(os.path.join(scan_dir, "sub1"))
    os.makedirs(os.path.join(scan_dir, "sub2"))
    os.makedirs(os.path.join(scan_dir, "sub1", "sub1"))
    os.makedirs(os.path.join(scan_dir, "sub1", "sub2"))
    os.makedirs(os.path.join(scan_dir, "sub2", "sub1"))
    os.makedirs(os.path.join(scan_dir, "sub2", "sub2"))

    copy_files(range(1, 4), scan_dir)
    copy_files(range(1, 3), os.path.join(scan_dir, "sub1"))
    copy_files(range(1, 3), os.path.join(scan_dir, "sub2"))
    copy_files(range(2, 4), os.path.join(scan_dir, "sub1", "sub1"))
    copy_files(range(3, 6), os.path.join(scan_dir, "sub1", "sub2"))
    copy_files(range(2, 5), os.path.join(scan_dir, "sub2", "sub1"))
    copy_files(range(1, 5), os.path.join(scan_dir, "sub2", "sub2"))

    fm = FileManager.get_instance()
    scan_files = get_folder_files_as_set(scan_dir)
    scan_tree = fm.list_tree_os_scandir_bfs(scan_dir)  # result is in the form of full path
    assert set(scan_tree) == scan_files


def test_file_manager_any_is_subfolder_of():
    # Test case 1: one folder is subfolder of another
    is_subfolder, relationships = FileManager.any_is_subfolder_of(
        ["C:\\Users\\user\\Desktop\\folder", "C:\\Users\\user\\Desktop\\folder\\subfolder"])
    assert is_subfolder is True

    # Test case 2: no folder is subfolder of another
    is_subfolder, relationships = FileManager.any_is_subfolder_of(
        ["C:\\Users\\user\\Desktop\\folder1", "C:\\Users\\user\\Desktop\\folder2"])
    assert is_subfolder is False

    # Test case 3: one folder is subfolder of another
    is_subfolder, relationships = FileManager.any_is_subfolder_of(
        ["/path/to/folder", "/path/to/folder/subfolder"])
    assert is_subfolder is True

    # Test case 4: no folder is subfolder of another
    is_subfolder, relationships = FileManager.any_is_subfolder_of(
        ["/path/to/folder1", "/path/to/folder2"])
    assert is_subfolder is False

    # Test case 5: 3 folders, one is subfolder of another
    is_subfolder, relationships = FileManager.any_is_subfolder_of(
        ["/path/to/folder1", "/path/to/folder2", "/path/to/folder2/subfolder"])
    assert is_subfolder is True

    # Test case 6: 3 folders, no folder is subfolder of another
    is_subfolder, relationships = FileManager.any_is_subfolder_of(
        ["/path/to/folder1", "/path/to/folder2", "/path/to/folder3"])
    assert is_subfolder is False

    # Test case 7: 3 folders, one is subfolder of another
    is_subfolder, relationships = FileManager.any_is_subfolder_of(
        ["C:\\Users\\user\\Desktop\\folder1", "C:\\Users\\user\\Desktop\\folder2",
         "C:\\Users\\user\\Desktop\\folder2\\subfolder"])
    assert is_subfolder is True

    # Test case 8: 3 folders, no folder is subfolder of another
    is_subfolder, relationships = FileManager.any_is_subfolder_of(
        ["C:\\Users\\user\\Desktop\\folder1", "C:\\Users\\user\\Desktop\\folder2",
         "C:\\Users\\user\\Desktop\\folder3"])
    assert is_subfolder is False

    # test case 9: one folder starts with another
    is_subfolder, relationships = FileManager.any_is_subfolder_of(
        ["C:\\Users\\user\\Desktop\\folder1", "C:\\Users\\user\\Desktop\\folder11"])
    assert is_subfolder is False


def test_file_manager_is_allowed_path(setup_teardown):
    scan_dir, reference_dir, move_to_dir, common_args = setup_teardown
    fm = FileManager(True).reset_all()

    protected_dir1 = os.path.join(reference_dir, "folder")
    protected_dir2 = os.path.join(reference_dir, "folder1")
    allowed_dir = os.path.join(scan_dir, "folder2")
    os.makedirs(protected_dir1)
    os.makedirs(protected_dir2)
    os.makedirs(allowed_dir)
    os.makedirs(os.path.join(scan_dir, "folder3"))

    fm.add_protected_dir(os.path.join(reference_dir, "folder"))
    fm.add_protected_dir(os.path.join(reference_dir, "folder1"))
    fm.add_allowed_dir(os.path.join(scan_dir, "folder2"))

    # Test case 1: protected path
    assert not fm.is_allowed_path(os.path.join(reference_dir, "folder", "subfolder"))

    # Test case 2: protected path
    assert not fm.is_allowed_path(os.path.join(reference_dir, "folder1", "subfolder"))

    # Test case 3: allowed path
    assert fm.is_allowed_path(os.path.join(scan_dir, "folder2", "subfolder"))

    # Test case 4: non-protected path - should be disallowed as allowed directories are set
    assert not fm.is_allowed_path(os.path.join(scan_dir, "folder3", "subfolder"))

    fm = FileManager(True).reset_all()
    # Test case 5: no protected or allowed directories set - all paths should be allowed
    assert fm.is_allowed_path(os.path.join(scan_dir, "folder3", "subfolder"))
    assert not fm.is_protected_path(os.path.join(scan_dir, "folder3", "subfolder"))


def test_python_source_files():
    """
    Test all python files in the project under duplicate_files_in_folders folder. Make sure that all python files
    are using FileManager for file operations.
    i.e. No call to shutil.copy(), shutil.move(), os.makedirs(), os.rmdir(), os.remove() etc. should be present in any
    python file under duplicate_files_in_folders folder except file_manager.py
    """
    project_root = Path(__file__).parent.parent
    project_root = project_root / "duplicate_files_in_folders"
    python_files = list(project_root.glob("**/*.py"))
    python_files = [str(file) for file in python_files if "__init__.py" not in str(file)]
    disallowed_functions = ["shutil.copy", "shutil.move", "shutil.rmtree", "os.makedirs", "os.rmdir", "os.remove"]
    exceptions_list = {  # allow these functions in these files
        "initializer.py": ["os.makedirs"]
    }
    for file in python_files:
        filename = file[file.rfind(os.sep) + 1:]
        if filename == "file_manager.py":
            continue
        with open(file, "r") as f:
            lines = f.readlines()
            for line in lines:
                for func in disallowed_functions:
                    if func in line:
                        if filename in exceptions_list and func in exceptions_list[filename]:
                            continue
                        assert False, f"{func} found in {file}"
