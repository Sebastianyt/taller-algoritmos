def ternarySearch(arr, x):
    """
    Busqueda ternaria en arreglo ORDENADO.
    Retorna indice o -1.
    """
    low = 0
    high = len(arr) - 1

    while low <= high:
        third = (high - low) // 3
        mid1 = low + third
        mid2 = high - third

        if arr[mid1] == x:
            return mid1
        if arr[mid2] == x:
            return mid2

        if x < arr[mid1]:
            high = mid1 - 1
        elif x > arr[mid2]:
            low = mid2 + 1
        else:
            low = mid1 + 1
            high = mid2 - 1

    return -1


if __name__ == "__main__":
    arr = [2, 3, 4, 10, 40]
    x = 10
    print(ternarySearch(arr, x))