"""
Merge Sort – versión iterativa (bottom-up) para Python.
Evita RecursionError en arreglos grandes (100 K – 1 M elementos).
Complejidad: O(n log n) tiempo, O(n) espacio.
"""


def mergeSort(arr, left=None, right=None):
    """Interfaz compatible con el benchmark (ignora left/right, ordena in-place)."""
    n = len(arr)
    if n < 2:
        return

    # Bottom-up merge sort
    width = 1
    while width < n:
        for lo in range(0, n, 2 * width):
            mid = min(lo + width, n)
            hi = min(lo + 2 * width, n)
            if mid < hi:
                _merge(arr, lo, mid, hi)
        width *= 2


def _merge(arr, lo, mid, hi):
    left = arr[lo:mid]
    right = arr[mid:hi]
    i = j = 0
    k = lo
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            arr[k] = left[i]
            i += 1
        else:
            arr[k] = right[j]
            j += 1
        k += 1
    while i < len(left):
        arr[k] = left[i]
        i += 1
        k += 1
    while j < len(right):
        arr[k] = right[j]
        j += 1
        k += 1


# Driver
if __name__ == "__main__":
    arr = [38, 27, 43, 10, 3, 9, 82, 10]
    mergeSort(arr)
    print("Sorted:", arr)