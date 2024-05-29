import os
import timeit

def fast_basename(path):
    return path[path.rfind(os.sep) + 1:]


test_path = "your/file/path/here"  # Define the test path
test_path = "C:\\temp\\duplicate_files_in_folders\\get_name_from_path.py"

# Measure performance of os.path.basename
os_basename_time = timeit.timeit(lambda: os.path.basename(test_path), number=1000000)

# Measure performance of fast_basename
fast_basename_time = timeit.timeit(lambda: fast_basename(test_path), number=1000000)

# Measure performance of inline operation
inline_basename_time = timeit.timeit(lambda: test_path[test_path.rfind(os.sep) + 1:], number=1000000)


print(f"os.path.basename: {os_basename_time:.6f} seconds")
print(f"fast_basename: {fast_basename_time:.6f} seconds")
print(f"inline_basename: {inline_basename_time:.6f} seconds")

# Sample output with the test_path defined above:
#  os.path.basename: 1.916315 seconds
#  fast_basename: 0.218280 seconds
#  inline_basename: 0.193531 seconds
