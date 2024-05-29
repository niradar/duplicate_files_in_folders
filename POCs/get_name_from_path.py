import os
import timeit

def fast_basename(path):
    return path[path.rfind(os.sep) + 1:]


test_path = "your/file/path/here"  # Define the test path

# Measure performance of os.path.basename
os_basename_time = timeit.timeit(lambda: os.path.basename(test_path), number=1000000)

# Measure performance of fast_basename
fast_basename_time = timeit.timeit(lambda: fast_basename(test_path), number=1000000)

print(f"os.path.basename: {os_basename_time:.6f} seconds")
print(f"fast_basename: {fast_basename_time:.6f} seconds")

# Sample output with the test_path defined above:
#  os.path.basename: 1.713233 seconds
#  fast_basename: 0.209291 seconds
