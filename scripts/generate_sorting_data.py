"""
Genera una sola vez el archivo de datos para el punto 1 (ordenamiento).
1_000_000 enteros aleatorios de exactamente 8 dígitos (10_000_000–99_999_999).
Si el archivo ya existe, no lo regenera.
"""
from __future__ import annotations

import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "sorting_1000000.txt"
COUNT = 1_000_000
SEED = 42


def main() -> None:
    if DATA_PATH.exists():
        print(f"Ya existe {DATA_PATH}, no se regenera.")
        return
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    with DATA_PATH.open("w", encoding="ascii", newline="\n") as f:
        for _ in range(COUNT):
            f.write(str(rng.randint(10_000_000, 99_999_999)) + "\n")
    print(f"Escritos {COUNT} valores en {DATA_PATH}")


if __name__ == "__main__":
    main()
