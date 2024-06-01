# Identifies and processes duplicate files between a source and target directory.
# https://github.com/niradar/duplicate_files_in_folders

from duplicate_files_in_folders.duplicates_finder import find_duplicates_files_v3, process_duplicates, \
    clean_source_duplications
from duplicate_files_in_folders.file_manager import FileManager
from duplicate_files_in_folders.logging_config import setup_logging
from duplicate_files_in_folders.old_duplicates_finder import find_and_process_duplicates
from duplicate_files_in_folders.utils import (confirm_script_execution, parse_arguments, output_results,
                                              display_initial_config, setup_hash_manager)


def main(args):
    setup_logging()
    fm = FileManager.reset_file_manager([args.target], [args.src, args.move_to], args.run)
    display_initial_config(args)
    confirm_script_execution(args)
    hash_manager = setup_hash_manager(args)
    if args.old_script is True:
        (files_moved, files_created, unique_source_duplicate_files_found, duplicate_source_files_moved) = (
            find_and_process_duplicates(args))
    else:
        duplicates, _, _ = find_duplicates_files_v3(args, args.src, args.target)
        files_moved, files_created = process_duplicates(duplicates, args)
        duplicate_source_files_moved = clean_source_duplications(args, duplicates)

    deleted_source_folders = fm.delete_empty_folders_in_tree(args.src, True) if args.delete_empty_folders else 0
    hash_manager.save_data()
    output_results(args, files_moved, files_created, deleted_source_folders, duplicate_source_files_moved)


if __name__ == "__main__":
    command_line_args = parse_arguments()
    main(command_line_args)
