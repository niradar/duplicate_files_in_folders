from tests.helpers_testing import *
from pathlib import Path
from file_manager import FileManager

# FileManager suppose to protect some directories from being moved, copied or deleted.


def test_move_file(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [2])
    fm = file_manager.FileManager(True).reset_all()
    fm.add_protected_dir(target_dir)
    file_to_move = os.path.join(source_dir, "1.jpg")
    dst_file = os.path.join(target_dir, "1.jpg")

    # move to protected directory should fail
    with pytest.raises(file_manager.ProtectedPathError):
        fm.move_file(file_to_move, dst_file)

    # move from unprotected directory to unprotected directory should work
    fm.move_file(file_to_move, os.path.join(move_to_dir, "1.jpg"))
    assert os.path.exists(os.path.join(move_to_dir, "1.jpg"))
    assert not os.path.exists(file_to_move)

    # move from protected directory should fail too
    file_to_move = os.path.join(target_dir, "2.jpg")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.move_file(file_to_move, os.path.join(move_to_dir, "2.jpg"))
    assert os.path.exists(file_to_move)
    assert not os.path.exists(os.path.join(move_to_dir, "2.jpg"))

    # now add allowed directory setting
    fm.add_allowed_dir(source_dir)
    file_to_move = os.path.join(source_dir, "3.jpg")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.move_file(file_to_move, os.path.join(move_to_dir, "3.jpg")) # should fail as move_to_dir is not allowed
    assert os.path.exists(file_to_move)
    assert not os.path.exists(os.path.join(move_to_dir, "3.jpg"))

    fm.add_allowed_dir(move_to_dir)
    fm.move_file(file_to_move, os.path.join(move_to_dir, "3.jpg")) # should work now


def test_copy_file(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [2, 3])
    fm = file_manager.FileManager(True).reset_all()
    fm.add_protected_dir(target_dir)
    file_to_copy = os.path.join(source_dir, "1.jpg")
    dst_file = os.path.join(target_dir, "1.jpg")

    # copy from unprotected directory to protected directory should fail
    with pytest.raises(file_manager.ProtectedPathError):
        fm.copy_file(file_to_copy, dst_file)

    # copy from unprotected directory to unprotected directory should work
    fm.copy_file(file_to_copy, os.path.join(move_to_dir, "1.jpg"))
    assert os.path.exists(os.path.join(move_to_dir, "1.jpg"))
    assert os.path.exists(file_to_copy)

    # copy from protected directory to unprotected directory should work
    file_to_copy = os.path.join(target_dir, "2.jpg")
    fm.copy_file(file_to_copy, os.path.join(move_to_dir, "2.jpg"))
    assert os.path.exists(os.path.join(move_to_dir, "2.jpg"))
    assert os.path.exists(file_to_copy)

    # copy from protected directory to protected directory should fail
    file_to_copy = os.path.join(target_dir, "3.jpg")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.copy_file(file_to_copy, os.path.join(target_dir, "4.jpg"))
    assert os.path.exists(file_to_copy)
    assert not os.path.exists(os.path.join(target_dir, "4.jpg"))

    # now add allowed directory setting
    fm.add_allowed_dir(source_dir)
    file_to_copy = os.path.join(source_dir, "5.jpg")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.copy_file(file_to_copy, os.path.join(move_to_dir, "5.jpg"))
    assert os.path.exists(file_to_copy)
    assert not os.path.exists(os.path.join(move_to_dir, "5.jpg"))

    fm.add_allowed_dir(move_to_dir)
    fm.copy_file(file_to_copy, os.path.join(move_to_dir, "5.jpg")) # should work now
    assert os.path.exists(os.path.join(move_to_dir, "5.jpg"))
    assert os.path.exists(file_to_copy)


def test_delete_file(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [2, 3])
    fm = file_manager.FileManager(True).reset_all()
    fm.add_protected_dir(target_dir)
    file_to_delete = os.path.join(source_dir, "1.jpg")

    # delete from unprotected directory should work
    fm.delete_file(file_to_delete)
    assert not os.path.exists(file_to_delete)

    # delete from protected directory should fail
    file_to_delete = os.path.join(target_dir, "2.jpg")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.delete_file(file_to_delete)
    assert os.path.exists(file_to_delete)

    # copy 3.jpg to move_to_dir
    shutil.copy(os.path.join(source_dir, "3.jpg"), os.path.join(move_to_dir, "3.jpg"))

    # now add allowed directory setting - source should be allowed but move_to_dir should not be allowed
    fm.add_allowed_dir(source_dir)
    file_to_delete = os.path.join(source_dir, "3.jpg")

    fm.delete_file(file_to_delete)
    assert not os.path.exists(file_to_delete)

    file_to_delete = os.path.join(move_to_dir, "3.jpg")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.delete_file(file_to_delete)
    assert os.path.exists(file_to_delete)


def test_make_dirs(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    fm = file_manager.FileManager(True).reset_all()
    fm.add_protected_dir(target_dir)
    dir_to_make = os.path.join(source_dir, "new_dir")

    # make dir in unprotected directory should work
    fm.make_dirs(dir_to_make)
    assert os.path.exists(dir_to_make)

    # make dir in protected directory should fail
    dir_to_make = os.path.join(target_dir, "new_dir")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.make_dirs(dir_to_make)
    assert not os.path.exists(dir_to_make)

    # makedirs should work with multiple levels
    dir_to_make = os.path.join(source_dir, "another_new_dir", "sub_dir", "sub_sub_dir")
    fm.make_dirs(dir_to_make)
    assert os.path.exists(dir_to_make)

    # now add allowed directory setting
    fm.add_allowed_dir(source_dir)
    dir_to_make = os.path.join(source_dir, "another_new_dir", "sub_dir", "sub_sub_dir2")
    fm.make_dirs(dir_to_make)
    assert os.path.exists(dir_to_make)

    dir_to_make = os.path.join(move_to_dir, "another_new_dir", "sub_dir", "sub_sub_dir3")
    with pytest.raises(file_manager.ProtectedPathError):
        fm.make_dirs(dir_to_make)
    assert not os.path.exists(dir_to_make)


def test_rmdir(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    fm = file_manager.FileManager(True).reset_all()
    fm.add_protected_dir(target_dir)
    dir_to_remove = os.path.join(source_dir, "new_dir")
    os.makedirs(dir_to_remove)

    # remove dir in unprotected directory should work
    fm.rmdir(dir_to_remove)
    assert not os.path.exists(dir_to_remove)

    # remove dir in protected directory should fail
    dir_to_remove = os.path.join(target_dir, "new_dir")
    os.makedirs(dir_to_remove)
    with pytest.raises(file_manager.ProtectedPathError):
        fm.rmdir(dir_to_remove)
    assert os.path.exists(dir_to_remove)

    # rmdir should work with multiple levels
    dir_to_remove = os.path.join(source_dir, "another_new_dir", "sub_dir", "sub_sub_dir")
    os.makedirs(dir_to_remove)
    fm.rmdir(dir_to_remove)
    assert not os.path.exists(dir_to_remove)

    # now add allowed directory setting
    fm.add_allowed_dir(source_dir)
    dir_to_remove = os.path.join(source_dir, "another_new_dir", "sub_dir", "sub_sub_dir2")
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
    fm1 = file_manager.FileManager(True)
    fm2 = file_manager.FileManager(True)
    assert fm1 is fm2
    assert fm1 == fm2
    assert fm1 is not None
    assert fm2 is not None


def test_add_protected_dir():
    fm = file_manager.FileManager(True).reset_all()
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
    source_dir, target_dir, move_to_dir, common_args = setup_teardown
    setup_test_files(range(1, 6), [2, 3])
    fm = file_manager.FileManager.get_instance()

    source_files = get_folder_files_as_set(source_dir)
    source_tree = fm.list_tree_os_scandir_bfs(source_dir)  # result is in the form of full path
    assert set(source_tree) == source_files

    target_files = get_folder_files_as_set(target_dir)
    target_tree = fm.list_tree_os_scandir_bfs(target_dir)  # result is in the form of full path
    assert set(target_tree) == target_files


# files only in source - root folder has 3 files and 2 sub folders. each sub folder has some files and 2 sub folders.
# goes 3 levels deep.
def test_list_tree_os_scandir_bfs_tree_with_many_subfolders(setup_teardown):
    source_dir, target_dir, move_to_dir, common_args = setup_teardown

    os.makedirs(os.path.join(source_dir, "sub1"))
    os.makedirs(os.path.join(source_dir, "sub2"))
    os.makedirs(os.path.join(source_dir, "sub1", "sub1"))
    os.makedirs(os.path.join(source_dir, "sub1", "sub2"))
    os.makedirs(os.path.join(source_dir, "sub2", "sub1"))
    os.makedirs(os.path.join(source_dir, "sub2", "sub2"))

    copy_files(range(1, 4), source_dir)
    copy_files(range(1, 3), os.path.join(source_dir, "sub1"))
    copy_files(range(1, 3), os.path.join(source_dir, "sub2"))
    copy_files(range(2, 4), os.path.join(source_dir, "sub1", "sub1"))
    copy_files(range(3, 6), os.path.join(source_dir, "sub1", "sub2"))
    copy_files(range(2, 5), os.path.join(source_dir, "sub2", "sub1"))
    copy_files(range(1, 5), os.path.join(source_dir, "sub2", "sub2"))

    fm = file_manager.FileManager.get_instance()
    source_files = get_folder_files_as_set(source_dir)
    source_tree = fm.list_tree_os_scandir_bfs(source_dir)  # result is in the form of full path
    assert set(source_tree) == source_files

