"""
Genera los tres archivos de datos para el benchmark de ordenamiento.
  - sorting_10000.txt      → 10,000 enteros de 8 dígitos
  - sorting_100000.txt     → 100,000 enteros de 8 dígitos
  - sorting_1000000.txt    → 1,000,000 enteros de 8 dígitos

Cada número es aleatorio entre 10_000_000 y 99_999_999 (exactamente 8 digitos).
Si el archivo ya existe NO se regenera (mismos datos garantizados entre ejecuciones).
SEED fija para reproducibilidad.
"""
from __future__ import annotations

import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SEED = 42

# Tamaños requeridos por el taller
SIZES = {
    10_000: "sorting_10000.txt",
    100_000: "sorting_100000.txt",
    1_000_000: "sorting_1000000.txt",
}


def generate_all() -> None:
    """Genera todos los archivos de datos necesarios."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    # Generamos todos los números de una sola vez para mantener coherencia entre archivos
    # El archivo de 1M contiene también los primeros 10k y 100k (mismos datos)
    max_count = max(SIZES.keys())
    all_numbers: list[int] = []

    for size, filename in sorted(SIZES.items()):
        path = DATA_DIR / filename
        if path.exists():
            print(f"  [OK] {filename} ya existe - no se regenera.")
            continue

        # Generamos solo lo que nos falta para llegar al tamaño requerido
        needed = size - len(all_numbers)
        if needed > 0:
            all_numbers.extend(rng.randint(10_000_000, 99_999_999) for _ in range(needed))

        print(f"  Generando {filename} ({size:,} elementos) ...", end=" ", flush=True)
        with path.open("w", encoding="ascii", newline="\n") as f:
            for n in all_numbers[:size]:
                f.write(str(n) + "\n")
        print("OK")

    print("Datos listos en:", DATA_DIR)


if __name__ == "__main__":
    generate_all()
