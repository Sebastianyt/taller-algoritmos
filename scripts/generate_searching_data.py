"""
Genera los archivos de datos para el benchmark de busqueda (Punto 2).

- Arreglos de enteros de 8 digitos (10_000_000 a 99_999_999)
- Tres tamanos: 10k, 100k, 1M
- Se generan una sola vez y se guardan en texto plano
- En ejecuciones posteriores NO se regeneran si el archivo existe

Nota: los algoritmos (binaria/ternaria/jump) requieren el arreglo ordenado,
por eso se guarda el arreglo ya ordenado.
"""
from __future__ import annotations

import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data_searching"

SEED_ARRAY = 12345
SEED_QUERIES = 54321

SIZES = {
    10_000: "searching_10000.txt",
    100_000: "searching_100000.txt",
    1_000_000: "searching_1000000.txt",
}

QUERY_FILES = {
    10_000: "queries_10000.txt",
    100_000: "queries_100000.txt",
    1_000_000: "queries_1000000.txt",
}

# Cantidad de consultas por tamanio (mismas consultas por prefijo)
QUERY_COUNT_MAX = 50_000


def generate_all() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    max_n = max(SIZES.keys())
    array_path = DATA_DIR / SIZES[max_n]
    queries_path = DATA_DIR / QUERY_FILES[max_n]

    # 1) Generar arreglo maximo (ordenado) si falta
    if not array_path.exists():
        rng = random.Random(SEED_ARRAY)
        print(f"  Generando {array_path.name} ({max_n:,} elementos, ordenado) ...", end=" ", flush=True)
        arr = [rng.randint(10_000_000, 99_999_999) for _ in range(max_n)]
        arr.sort()
        with array_path.open("w", encoding="ascii", newline="\n") as f:
            for v in arr:
                f.write(str(v) + "\n")
        print("OK")
    else:
        print(f"  [OK] {array_path.name} ya existe - no se regenera.")

    # 2) Generar consultas maximas si faltan
    if not queries_path.exists():
        rngq = random.Random(SEED_QUERIES)
        print(f"  Generando {queries_path.name} ({QUERY_COUNT_MAX:,} consultas) ...", end=" ", flush=True)

        # Mezcla: 50% presentes (8 digitos), 50% aleatorios (podrian no estar)
        # Evitamos leer el arreglo (I/O) aca para no hacer el script pesado;
        # la colision es posible pero rara y aceptable para benchmarking.
        queries: list[int] = []
        for i in range(QUERY_COUNT_MAX):
            if i % 2 == 0:
                # Numero de 8 digitos en rango
                queries.append(rngq.randint(10_000_000, 99_999_999))
            else:
                queries.append(rngq.randint(10_000_000, 99_999_999))

        with queries_path.open("w", encoding="ascii", newline="\n") as f:
            for q in queries:
                f.write(str(q) + "\n")
        print("OK")
    else:
        print(f"  [OK] {queries_path.name} ya existe - no se regenera.")

    # 3) Crear archivos por prefijo (10k, 100k) si faltan
    # Reutilizamos el mismo inicio del archivo de 1M (mismos datos garantizados)
    for n, filename in sorted(SIZES.items()):
        path = DATA_DIR / filename
        if path.exists():
            print(f"  [OK] {filename} ya existe - no se regenera.")
            continue
        print(f"  Creando {filename} por prefijo ({n:,}) ...", end=" ", flush=True)
        with array_path.open("r", encoding="ascii") as src, path.open("w", encoding="ascii", newline="\n") as dst:
            for _ in range(n):
                dst.write(src.readline())
        print("OK")

    for n, filename in sorted(QUERY_FILES.items()):
        path = DATA_DIR / filename
        if path.exists():
            print(f"  [OK] {filename} ya existe - no se regenera.")
            continue
        print(f"  Creando {filename} por prefijo ({n:,}) ...", end=" ", flush=True)
        # 10k/100k/1M usan el MISMO set de consultas por prefijo del maximo
        # (para que sean comparables entre tamanos).
        with queries_path.open("r", encoding="ascii") as src, path.open("w", encoding="ascii", newline="\n") as dst:
            # Usamos misma cantidad de consultas en todos los tamanos:
            # el archivo maximo ya tiene QUERY_COUNT_MAX.
            for _ in range(QUERY_COUNT_MAX):
                line = src.readline()
                if not line:
                    break
                dst.write(line)
        print("OK")

    print("Datos de busqueda listos en:", DATA_DIR)


if __name__ == "__main__":
    generate_all()

