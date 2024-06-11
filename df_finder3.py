# Identifies and processes duplicate files between a scan_dir and reference directory.
# https://github.com/niradar/duplicate_files_in_folders

from duplicate_files_in_folders.duplicates_finder import find_duplicates_files_v3, process_duplicates, \
    clean_scan_dir_duplications
from duplicate_files_in_folders.logging_config import setup_logging
from duplicate_files_in_folders.utils import parse_arguments, setup_hash_manager, setup_file_manager
from duplicate_files_in_folders.utils_io import display_initial_config, output_results, confirm_script_execution


def main(args):
    setup_logging()
    fm = setup_file_manager(args)
    display_initial_config(args)
    confirm_script_execution(args)
    hash_manager = setup_hash_manager(args)

    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, args.scan_dir, args.reference_dir)
    files_moved, files_created = process_duplicates(duplicates, args)
    duplicate_scan_files_moved = clean_scan_dir_duplications(args, duplicates)
    deleted_scan_folders = fm.delete_empty_folders_in_tree(args.scan_dir, True) if args.delete_empty_folders else 0

    hash_manager.save_data()
    output_results(args, files_moved, files_created, deleted_scan_folders, duplicate_scan_files_moved,
                   scan_stats, ref_stats)


if __name__ == "__main__":
    command_line_args = parse_arguments()
    main(command_line_args)
