# Python3 code to implement Jump Search
from __future__ import annotations

import math


def jumpSearch(arr, x):
    """
    Jump Search en arreglo ORDENADO.
    Retorna indice o -1.
    """
    n = len(arr)
    if n == 0:
        return -1

    step = int(math.isqrt(n))
    prev = 0

    while prev < n and arr[min(prev + step, n) - 1] < x:
        prev += step
        if prev >= n:
            return -1

    end = min(prev + step, n)
    while prev < end and arr[prev] < x:
        prev += 1

    if prev < n and arr[prev] == x:
        return prev
    return -1


if __name__ == "__main__":
    arr = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    print(jumpSearch(arr, 55))