# Duplicate File Finder

This script identifies and processes duplicate files between a source and target directory.

## Main Use Case

- The source folder contains files without order.
- The target folder contains files that are sorted versions of the files in the source folder.
- The script moves the files from the source folder to a "dups" folder if they are found in the target folder, maintaining the structure of the target folder in the "dups" folder.

The script compares filename, modification date, size, and hash of the files to identify duplicates. Settings allow ignoring differences in modification dates and filenames. The script can be run in test mode to simulate actions without moving the files. It also logs its actions and errors for traceability.


## Installation

To install the necessary dependencies, use Conda with Python 3.11 and the `requirements.txt` file:

```sh
conda create -n duplicate_finder python=3.11
conda activate duplicate_finder
pip install -r requirements.txt
```

## Usage

To run the script, use the following command:

```sh
python df_finder3.py --src <source_folder> --target <target_folder> --move_to <move_to_folder> [options]
```

### Options

- `--run`: Run without test mode (default is test mode).
- `--ignore_diff`: Comma-separated list of differences to ignore: `mdate`, `filename`, `checkall` (default is `mdate`).
- `--copy_to_all`: Copy file to all folders if found in multiple target folders (default is to move file to the first folder).
- `--delete_empty_folders`: Delete empty folders in the source folder (default is enabled).
- `--no-delete_empty_folders`: Do not delete empty folders in the source folder.
- `--clear_cache`: Clear the hash manager cache.

### Example

```sh
python df_finder3.py --src /path/to/source --target /path/to/target --move_to /path/to/move_to --run
```

## Running Tests
To run the tests, use pytest:

```sh
pytest
```

## Logging
The script logs its actions and errors for traceability. The log file will be created in the same directory as the script under logs/ folder


## Possible Future Improvements
- [ ] More tests
  - [ ] More tests for less common cases
  - [ ] More tests to hash_manager.py 
- [ ] Improve summary and user interface
    - [ ] Add a better summary of the actions taken
  - [ ] Add summary also to the console output
- [ ] Better handling of folders with saved html files
  - [ ] Deal with `_files` folders in the source folder
  - [ ] Move it only if all files are duplicates
- [ ] More ways to influence how the script works
  - [ ] Add an argument to act only if the entire folder is a subfolder of a target folder, recursively (bottom-up)
  - [ ] Option to keep the source folder structure in the move_to folder
- [ ] Add a way to ignore files with specific extensions / process only files with specific extensions
- [ ] Consider using bloom filters for faster comparison (https://en.wikipedia.org/wiki/Bloom_filter)
  - [ ] idea - save also the first part of the hash - when comparing large files - if no match after that part, you don't need to continue the check
- [ ] To consider: make sure expired cache is removed over time even if not touched
- [ ] More safeguards
  - [ ] Check any file operation for errors
- [ ] Save also file size and modify date in hash. avoid io ops when needed. Compare performences before and after
- [ ] Before checking target files also check if there is no chance we need them, for example - filename no match and not ingoring file name, or file size doesn't match
## Known Issues
- [ ] Even if argument --copy_to_all is not present, still need to move the duplicates to the move_to folder without copying them to other folders
- [ ] Hash manager clears all target before writing the new data, even if the new data not contains all the old data
- [ ] Issue with files with non-standard characters in the filename - no reproducible yet


## Contributing
If you have suggestions for improving this script, please open an issue or submit a pull request.

## Author
This script was written by Nir Adar - [niradar@gmail.com](mailto:niradar@gmail.com)

## License
This project is licensed under the MIT License.
