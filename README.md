# Duplicate File Finder

This script identifies and processes duplicate files between a scan folder and a reference folder.

## Main Use Case

The primary scenario for using this script is when you have a folder suspected to be a backup or containing some files from a "central repository." You want to compare it to the central repository and determine which files in it already exist in the central folder.
1. The scan folder contains files that might be without order or sub set of the files in the reference folder.
2. The reference folder contains files that are sorted versions of the files in the scan folder.

The script moves the files from the scan folder to a "dups" folder if they are found in the reference folder, maintaining the structure of the reference folder in the "dups" folder.

The script compares filename, modification date, size, and hash of the files to identify duplicates. Settings allow ignoring differences in modification dates and filenames. The script can be run in test mode to simulate actions without moving the files. It also logs its actions for traceability.


## Features

- **Bloom Filters:** Efficiently identify potential duplicates using [Bloom filters](https://en.wikipedia.org/wiki/Bloom_filter) for file size, name, and modified time, reducing unnecessary comparisons.
- **Parallel Processing:** Automatically selects and utilizes parallel processing, improving performance for large datasets.
- **Flexible Filtering:** Supports filtering of files based on size and extensions, with options for whitelisting and blacklisting extensions.
- **Comprehensive Logging:** Detailed logs track operations and outcomes, including a summary of actions taken.



## Usage

To run the script, use the following command:

```sh
python df_finder3.py --scan_dir <scan_folder> --reference_dir <reference_folder> --move_to <move_to_folder> [options]
```

### Options
- `--scan_dir` or `--scan` or `--s`: (Required) Path to the folder where duplicate files are scanned and cleaned.
- `--reference_dir` or `--reference` or `--r`: (Required) Path to the folder where duplicates are searched for reference.
- `--move_to` or `--to`: (Required) Path to the folder where duplicate files will be moved.
- `--run`: Executes the script. If not specified, the script runs in test mode.
- `--ignore_diff`: Comma-separated list of differences to ignore: `mdate`, `filename`, `none` (default is `mdate`).
- `--copy_to_all`: Copy file to all folders if found in multiple target folders (default is to move file to the first folder).
- `--keep_empty_folders`: Keep empty folders after moving files. Default is `False`.
- `--whitelist_ext`: Comma-separated list of extensions to include.
- `--blacklist_ext`: Comma-separated list of extensions to exclude.
- `--min_size`: Minimum file size to include. Specify with units (B, KB, MB).
- `--max_size`: Maximum file size to include. Specify with units (B, KB, MB).
- `--full_hash`: Use full file hash for comparison. Default is partial.
- `--action`: Action to take on duplicates. Default is `move_duplicates`. Options are `create_csv`, `move_duplicates`. 
    - `create_csv` - Create a CSV file with the list of duplicates.
    - `move_duplicates` - Move duplicates from scan folder to move_to folder.
### Example

#### Simple usage:
```sh
python df_finder3.py --run --scan_dir /path/to/scan_dir --reference_dir /path/to/reference_dir --move_to /path/to/move_to
```
#### Most common usage:
Ignore differences in modification dates, copy the file to all target folders if found in multiple folders, and run without test mode:
```sh
python df_finder3.py --run --ignore_diff mdate --copy_to_all --s /path/to/scan_dir --r /path/to/reference_dir --to /path/to/move_to
```

#### Using Whitelist and Blacklist
```sh
python df_finder3.py --whitelist_ext jpg,png --run --s /path/to/scan_dir --r /path/to/reference_dir --to /path/to/move_to
```

```sh
python df_finder3.py --blacklist_ext tmp,log --run --s /path/to/scan_dir --r /path/to/reference_dir --to /path/to/move_to
```

#### Filtering by File Size
```sh
python df_finder3.py --min_size 1MB --max_size 100MB --run --s /path/to/scan_dir --r /path/to/reference_dir --to /path/to/move_to
```
#### Ignore none of the differences
```sh
python df_finder3.py --ignore_diff none --run --s /path/to/scan_dir --r /path/to/reference_dir --to /path/to/move_to
```

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

## Contributing
If you have suggestions for improving this script, please open an issue or submit a pull request.

## Author
This script was written by Nir Adar - [niradar@gmail.com](mailto:niradar@gmail.com)

## License
This project is licensed under the MIT License. See the LICENSE file for details.