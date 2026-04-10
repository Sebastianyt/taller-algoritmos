"""
Dual-Pivot QuickSort – versión iterativa (stack explícito).
Evita RecursionError con arreglos de 1 M elementos.
Complejidad: O(n log n) promedio, O(log n) espacio de pila.
"""


def _partition(arr, low, high):
    if arr[low] > arr[high]:
        arr[low], arr[high] = arr[high], arr[low]
    p = arr[low]    # pivote izquierdo
    q = arr[high]   # pivote derecho
    j = k = low + 1
    g = high - 1
    while k <= g:
        if arr[k] < p:
            arr[k], arr[j] = arr[j], arr[k]
            j += 1
        elif arr[k] >= q:
            while arr[g] > q and k < g:
                g -= 1
            arr[k], arr[g] = arr[g], arr[k]
            g -= 1
            if arr[k] < p:
                arr[k], arr[j] = arr[j], arr[k]
                j += 1
        k += 1
    j -= 1
    g += 1
    arr[low], arr[j] = arr[j], arr[low]
    arr[high], arr[g] = arr[g], arr[high]
    return j, g


def dualPivotQuickSort(arr, low=None, high=None):
    """
    Interfaz compatible con el benchmark.
    Si se llama sin low/high, ordena todo el arreglo.
    """
    n = len(arr)
    if n < 2:
        return
    if low is None:
        low = 0
    if high is None:
        high = n - 1

    stack = [(low, high)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        lp, rp = _partition(arr, lo, hi)
        # Empujar las tres partes al stack
        stack.append((lo, lp - 1))
        stack.append((lp + 1, rp - 1))
        stack.append((rp + 1, hi))


# Driver
if __name__ == "__main__":
    arr = [24, 8, 42, 75, 29, 77, 38, 57]
    dualPivotQuickSort(arr)
    print("Sorted:", arr)