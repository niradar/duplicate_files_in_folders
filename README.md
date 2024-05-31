# Duplicate File Finder

This script identifies and processes duplicate files between a source and target directory.

## Main Use Case

- The source folder contains files without order.
- The target folder contains files that are sorted versions of the files in the source folder.
- The script moves the files from the source folder to a "dups" folder if they are found in the target folder, maintaining the structure of the target folder in the "dups" folder.

The script compares filename, modification date, size, and hash of the files to identify duplicates. Settings allow ignoring differences in modification dates and filenames. The script can be run in test mode to simulate actions without moving the files. It also logs its actions and errors for traceability.


## Usage

To run the script, use the following command:

```sh
python df_finder3.py --src <source_folder> --target <target_folder> --move_to <move_to_folder> [options]
```

### Options

- `--src` or `--source`: (Required) Path to the source folder.
- `--target`: (Required) Path to the target folder.
- `--move_to` or `--to`: (Required) Path to the folder where duplicate files will be moved.
- `--run`: (Optional) Run without test mode (default is test mode).
- `--ignore_diff`: (Optional) Comma-separated list of differences to ignore: `mdate`, `filename`, `checkall` (default is `mdate`).
- `--copy_to_all`: (Optional) Copy file to all folders if found in multiple target folders (default is to move file to the first folder).
- `--delete_empty_folders`: (Optional) Delete empty folders in the source folder (default is enabled).
- `--no-delete_empty_folders`: (Optional) Do not delete empty folders in the source folder.
- `--whitelist_ext`: (Optional) Comma-separated list of file extensions to whitelist. Only these will be checked.
- `--blacklist_ext`: (Optional) Comma-separated list of file extensions to blacklist. These will not be checked.
- `--min_size`: (Optional) Minimum file size to check. Specify with units (B, KB, MB).
- `--max_size`: (Optional) Maximum file size to check. Specify with units (B, KB, MB).
- `--full_hash`: (Optional) Use full file hash for comparison. Default is partial.

### Example

#### Simple usage:
```sh
python df_finder3.py --src /path/to/source --target /path/to/target --move_to /path/to/move_to --run
```
#### Most common usage:
Ignore differences in modification dates, copy the file to all target folders if found in multiple folders, and run without test mode:
```sh
python df_finder3.py --src /path/to/source --target /path/to/target --move_to /path/to/move_to --run --ignore_diff mdate --copy_to_all
```

#### Using Whitelist and Blacklist
```sh
python df_finder3.py --src /path/to/source --target /path/to/target --move_to /path/to/destination --whitelist_ext jpg,png --run
```

```sh
python df_finder3.py --src /path/to/source --target /path/to/target --move_to /path/to/destination --blacklist_ext tmp,log --run
```

#### Filtering by File Size
```sh
python df_finder3.py --src /path/to/source --target /path/to/target --move_to /path/to/destination --min_size 1MB --max_size 100MB --run
```

## Logging
The script logs its actions and errors for traceability. The log file will be created in the same directory as the script under logs/ folder


## Installation

To install the necessary dependencies:

1. Clone the repository and go into repository folder
```sh
git clone https://github.com/niradar/duplicate_files_in_folders.git
cd duplicate_files_in_folders
```

2. Use Conda with Python 3.11 and the requirements.txt file to install the necessary dependencies:
```sh
conda create -n duplicate_finder python=3.11
conda activate duplicate_finder
pip install -r requirements.txt
```

## Possible Future Improvements
- [ ] Improve summary and user interface
    - [ ] Add a better summary of the actions taken
    - [ ] Add summary also to the console output
- [ ] Better handling of folders with saved html files
  - [ ] Deal with `_files` folders in the source folder
  - [ ] Move it only if all files are duplicates
- [ ] More ways to influence how the script works
  - [ ] Add an argument to act only if the entire folder is a subfolder of a target folder, recursively (bottom-up)
  - [ ] Option to keep the source folder structure in the move_to folder
  - [ ] Option to send duplicates to recycle bin instead of move_to folder
- [ ] Use bloom filters for faster comparison (https://en.wikipedia.org/wiki/Bloom_filter)
  - [ ] Before checking target files also check if there is no chance we need them, for example - filename no match and not ingoring file name, or file size doesn't match
- [ ] More safeguards
  - [ ] Check any file operation for errors
## Known Issues
- [ ] Even if argument --copy_to_all is not present, still need to move the duplicates to the move_to folder without copying them to other folders
- [ ] Issue with files with non-standard characters in the filename - no reproducible yet


## Contributing
If you have suggestions for improving this script, please open an issue or submit a pull request.

## Author
This script was written by Nir Adar - [niradar@gmail.com](mailto:niradar@gmail.com)

## License
This project is licensed under the MIT License.
