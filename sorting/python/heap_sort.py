"""
Heap Sort – heapify iterativo para evitar RecursionError con 1 M elementos.
Complejidad: O(n log n) tiempo, O(1) espacio extra.
"""


def _heapify_iterative(arr, n, i):
    """Versión iterativa de heapify: sin riesgo de stack overflow."""
    while True:
        largest = i
        l = 2 * i + 1
        r = 2 * i + 2
        if l < n and arr[l] > arr[largest]:
            largest = l
        if r < n and arr[r] > arr[largest]:
            largest = r
        if largest == i:
            break
        arr[i], arr[largest] = arr[largest], arr[i]
        i = largest


def heapSort(arr):
    n = len(arr)
    # Build max-heap
    for i in range(n // 2 - 1, -1, -1):
        _heapify_iterative(arr, n, i)
    # Extract elements one by one
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        _heapify_iterative(arr, i, 0)


# Driver
if __name__ == "__main__":
    arr = [9, 4, 3, 8, 10, 2, 5]
    heapSort(arr)
    print("Sorted:", arr)