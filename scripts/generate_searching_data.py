"""
Genera los archivos de datos para el benchmark de busqueda (Punto 2).

- Arreglos de enteros de 8 digitos (10_000_000 a 99_999_999)
- Tres tamanos: 10k, 100k, 1M
- Se generan una sola vez y se guardan en texto plano
- En ejecuciones posteriores NO se regeneran si el archivo existe

Nota: los algoritmos (binaria/ternaria/jump) requieren el arreglo ordenado,
por eso se guarda el arreglo ya ordenado.
"""
from __future__ import annotations  # Permite usar anotaciones de tipo modernas en versiones anteriores de Python

import random        # Para generar números enteros aleatorios reproducibles con semilla fija
from pathlib import Path  # Para manejar rutas de archivos de forma multiplataforma

ROOT = Path(__file__).resolve().parents[1]  # Sube 1 nivel desde el script para llegar a la raíz del proyecto
DATA_DIR = ROOT / "data_searching"          # Carpeta donde se guardarán todos los archivos de datos de búsqueda

SEED_ARRAY   = 12345  # Semilla fija para el generador de arreglos (garantiza reproducibilidad)
SEED_QUERIES = 54321  # Semilla fija para el generador de queries (diferente a la del arreglo para independencia)

# Diccionario que mapea cada tamaño de arreglo a su nombre de archivo correspondiente
SIZES = {
    10_000:    "searching_10000.txt",
    100_000:   "searching_100000.txt",
    1_000_000: "searching_1000000.txt",
}

# Diccionario que mapea cada tamaño a su archivo de queries (valores a buscar) correspondiente
QUERY_FILES = {
    10_000:    "queries_10000.txt",
    100_000:   "queries_100000.txt",
    1_000_000: "queries_1000000.txt",
}

# Cantidad máxima de consultas a generar (se reutiliza el mismo set en todos los tamaños)
QUERY_COUNT_MAX = 50_000


def generate_all() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)  # Crea la carpeta de datos si no existe (y sus padres también)

    max_n = max(SIZES.keys())                    # Obtiene el tamaño máximo (1.000.000) para generar el archivo base
    array_path   = DATA_DIR / SIZES[max_n]       # Ruta al archivo del arreglo completo de 1M elementos
    queries_path = DATA_DIR / QUERY_FILES[max_n] # Ruta al archivo de queries completo de 50.000 consultas

    # 1) Generar arreglo maximo (ordenado) si falta
    if not array_path.exists():                  # Solo genera el archivo si no existe previamente
        rng = random.Random(SEED_ARRAY)          # Crea un generador de números aleatorios con la semilla fija del arreglo
        print(f"  Generando {array_path.name} ({max_n:,} elementos, ordenado) ...", end=" ", flush=True)  # Informa el inicio de la generación
        arr = [rng.randint(10_000_000, 99_999_999) for _ in range(max_n)]  # Genera 1M enteros aleatorios de 8 dígitos
        arr.sort()  # Ordena el arreglo de menor a mayor (requerido por los algoritmos de búsqueda binaria/ternaria/jump)
        with array_path.open("w", encoding="ascii", newline="\n") as f:  # Abre el archivo para escritura con saltos de línea Unix
            for v in arr:
                f.write(str(v) + "\n")  # Escribe cada entero en una línea separada
        print("OK")  # Confirma que la generación terminó exitosamente
    else:
        print(f"  [OK] {array_path.name} ya existe - no se regenera.")  # Informa que el archivo ya existe y se omite

    # 2) Generar consultas maximas si faltan
    if not queries_path.exists():                # Solo genera el archivo si no existe previamente
        rngq = random.Random(SEED_QUERIES)       # Crea un generador de números aleatorios con la semilla fija de queries
        print(f"  Generando {queries_path.name} ({QUERY_COUNT_MAX:,} consultas) ...", end=" ", flush=True)  # Informa el inicio

        # Mezcla: 50% presentes (8 digitos), 50% aleatorios (podrian no estar)
        # Evitamos leer el arreglo (I/O) aca para no hacer el script pesado;
        # la colision es posible pero rara y aceptable para benchmarking.
        queries: list[int] = []                  # Lista vacía que acumulará todos los valores de consulta
        for i in range(QUERY_COUNT_MAX):         # Genera exactamente QUERY_COUNT_MAX consultas
            if i % 2 == 0:                       # En posiciones pares...
                queries.append(rngq.randint(10_000_000, 99_999_999))  # ...genera un entero de 8 dígitos en rango (podría estar en el arreglo)
            else:                                # En posiciones impares...
                queries.append(rngq.randint(10_000_000, 99_999_999))  # ...también genera un entero de 8 dígitos (misma lógica, estructura preparada para diferenciación futura)

        with queries_path.open("w", encoding="ascii", newline="\n") as f:  # Abre el archivo de queries para escritura
            for q in queries:
                f.write(str(q) + "\n")  # Escribe cada query en una línea separada
        print("OK")  # Confirma que la generación de queries terminó exitosamente
    else:
        print(f"  [OK] {queries_path.name} ya existe - no se regenera.")  # Informa que el archivo ya existe y se omite

    # 3) Crear archivos por prefijo (10k, 100k) si faltan
    # Reutilizamos el mismo inicio del archivo de 1M (mismos datos garantizados)
    for n, filename in sorted(SIZES.items()):    # Itera sobre los tamaños en orden ascendente (10k, 100k, 1M)
        path = DATA_DIR / filename               # Construye la ruta completa al archivo de arreglo para este tamaño
        if path.exists():
            print(f"  [OK] {filename} ya existe - no se regenera.")  # Si ya existe, lo informa y lo salta
            continue                            # Pasa al siguiente tamaño sin regenerar
        print(f"  Creando {filename} por prefijo ({n:,}) ...", end=" ", flush=True)  # Informa que se está creando por prefijo
        with array_path.open("r", encoding="ascii") as src, path.open("w", encoding="ascii", newline="\n") as dst:
            # Abre el archivo de 1M como fuente y el archivo destino para escritura simultáneamente
            for _ in range(n):                   # Lee exactamente las primeras n líneas del archivo de 1M
                dst.write(src.readline())        # Copia cada línea del arreglo fuente al archivo destino más pequeño
        print("OK")  # Confirma que el archivo fue creado exitosamente por prefijo

    for n, filename in sorted(QUERY_FILES.items()):  # Itera sobre los archivos de queries en orden ascendente
        path = DATA_DIR / filename                    # Construye la ruta completa al archivo de queries para este tamaño
        if path.exists():
            print(f"  [OK] {filename} ya existe - no se regenera.")  # Si ya existe, lo informa y lo salta
            continue                                  # Pasa al siguiente sin regenerar
        print(f"  Creando {filename} por prefijo ({n:,}) ...", end=" ", flush=True)  # Informa la creación por prefijo
        # 10k/100k/1M usan el MISMO set de consultas por prefijo del maximo
        # (para que sean comparables entre tamanos).
        with queries_path.open("r", encoding="ascii") as src, path.open("w", encoding="ascii", newline="\n") as dst:
            # Abre el archivo de queries de 50k como fuente y el destino para escritura simultáneamente
            # Usamos misma cantidad de consultas en todos los tamanos:
            # el archivo maximo ya tiene QUERY_COUNT_MAX.
            for _ in range(QUERY_COUNT_MAX):     # Copia exactamente QUERY_COUNT_MAX líneas (todos los queries)
                line = src.readline()            # Lee la siguiente línea del archivo fuente de queries
                if not line:                     # Si llegó al final del archivo antes de completar el rango...
                    break                        # ...detiene la copia para evitar escribir líneas vacías
                dst.write(line)                  # Escribe la línea de query en el archivo destino
        print("OK")  # Confirma que el archivo de queries fue creado exitosamente

    print("Datos de busqueda listos en:", DATA_DIR)  # Mensaje final indicando que todos los archivos están listos


if __name__ == "__main__":  # Solo ejecuta generate_all() si este script es el punto de entrada (no si es importado)
    generate_all()          # Llama a la función principal que genera todos los archivos de datos