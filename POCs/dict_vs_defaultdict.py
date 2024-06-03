import timeit
from collections import defaultdict


def dict_performance(n):
    regular_dict = {}
    for i in range(n):
        if i not in regular_dict:
            regular_dict[i] = []
        regular_dict[i].append(i)


def defaultdict_performance(n):
    default_dict = defaultdict(list)
    for i in range(n):
        default_dict[i].append(i)


if __name__ == '__main__':
    n = 3000000  # Number of iterations
    dict_time = timeit.timeit(lambda: dict_performance(n), number=10)
    defaultdict_time = timeit.timeit(lambda: defaultdict_performance(n), number=10)

    print(f'Time taken by dict: {dict_time:.6f} seconds')
    print(f'Time taken by defaultdict: {defaultdict_time:.6f} seconds')

# Sample output:
#   Time taken by dict: 4.709627 seconds
#   Time taken by defaultdict: 5.102884 seconds
