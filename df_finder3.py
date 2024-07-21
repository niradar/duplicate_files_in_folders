# Identifies and processes duplicate files between a scan_dir and reference directory.
# https://github.com/niradar/duplicate_files_in_folders

from duplicate_files_in_folders.duplicates_finder import find_duplicates_files_v3, process_duplicates, \
    clean_scan_dir_duplications, create_csv_file
from duplicate_files_in_folders.initializer import setup_logging, setup_hash_manager, setup_file_manager
from duplicate_files_in_folders.utils import parse_arguments
from duplicate_files_in_folders.utils_io import display_initial_config, output_results, confirm_script_execution, \
    output_csv_file_creation_results


def main(args):
    setup_logging()
    fm = setup_file_manager(args)
    display_initial_config(args)
    confirm_script_execution(args)
    hash_manager = setup_hash_manager(args.reference_dir, args.full_hash, args.clear_cache)

    duplicates, scan_stats, ref_stats = find_duplicates_files_v3(args, args.scan_dir, args.reference_dir,
                                                                 output_progress=True)

    if args.action == 'move_duplicates':
        files_moved, files_created = process_duplicates(duplicates, args)
        duplicate_scan_files_moved = clean_scan_dir_duplications(args, duplicates)
        deleted_scan_folders = fm.delete_empty_folders_in_tree(args.scan_dir, True) if args.delete_empty_folders else 0

        output_results(args, files_moved, files_created, deleted_scan_folders, duplicate_scan_files_moved,
                       scan_stats, ref_stats)
    elif args.action == 'create_csv':
        # Always run in run mode as it creates a file and maybe a folder.
        fm.with_run_mode(create_csv_file, args, duplicates)
        output_csv_file_creation_results(args, duplicates, scan_stats, ref_stats)

    hash_manager.save_data()


if __name__ == "__main__":
    command_line_args = parse_arguments()
    main(command_line_args)
