import urllib.request
from time import time


def get(url: str):
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def test(url: str, times: int = 10):
    took = []
    for _ in range(times):
        start = time()
        get(url)
        end = time() - start
        print(f"GET {url} {end:.3f} seconds", end="\r")
        took.append(end)
    print()

    print(f"Average: {sum(took)/len(took):.3f} seconds for {times} times")


if __name__ == "__main__":
    import sys

    test(sys.argv[1], int(sys.argv[2]))
