"""
Genera los tres archivos de datos para el benchmark de ordenamiento.
  - sorting_10000.txt      → 10,000 enteros de 8 dígitos
  - sorting_100000.txt     → 100,000 enteros de 8 dígitos
  - sorting_1000000.txt    → 1,000,000 enteros de 8 dígitos

Cada número es aleatorio entre 10_000_000 y 99_999_999 (exactamente 8 digitos).
Si el archivo ya existe NO se regenera (mismos datos garantizados entre ejecuciones).
SEED fija para reproducibilidad.
"""
from __future__ import annotations  # Permite usar anotaciones de tipo modernas en versiones anteriores de Python

import random        # Para generar números enteros aleatorios reproducibles con semilla fija
from pathlib import Path  # Para manejar rutas de archivos de forma multiplataforma

ROOT = Path(__file__).resolve().parents[1]  # Sube 1 nivel desde el script para llegar a la raíz del proyecto
DATA_DIR = ROOT / "data"                    # Carpeta donde se guardarán todos los archivos de datos de ordenamiento
SEED = 42                                   # Semilla fija para el generador aleatorio (garantiza los mismos datos en cada ejecución)

# Diccionario que mapea cada tamaño de arreglo a su nombre de archivo correspondiente
SIZES = {
    10_000:    "sorting_10000.txt",    # Archivo pequeño de 10.000 enteros
    100_000:   "sorting_100000.txt",   # Archivo mediano de 100.000 enteros
    1_000_000: "sorting_1000000.txt",  # Archivo grande de 1.000.000 enteros
}


def generate_all() -> None:
    """Genera todos los archivos de datos necesarios."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)  # Crea la carpeta de datos si no existe (y sus padres también)
    rng = random.Random(SEED)                    # Crea un generador de números aleatorios aislado con la semilla fija

    # Generamos todos los números de una sola vez para mantener coherencia entre archivos
    # El archivo de 1M contiene también los primeros 10k y 100k (mismos datos)
    max_count = max(SIZES.keys())  # Obtiene el tamaño máximo (1.000.000) — declarado pero no usado directamente, documenta la intención
    all_numbers: list[int] = []    # Lista acumulativa que crece conforme se necesitan más números para los archivos siguientes

    for size, filename in sorted(SIZES.items()):  # Itera sobre los tamaños en orden ascendente (10k → 100k → 1M)
        path = DATA_DIR / filename                # Construye la ruta completa al archivo para este tamaño
        if path.exists():
            print(f"  [OK] {filename} ya existe - no se regenera.")  # Si ya existe, lo informa y lo salta
            continue                             # Pasa al siguiente tamaño sin regenerar ni consumir números del RNG

        # Generamos solo lo que nos falta para llegar al tamaño requerido
        needed = size - len(all_numbers)         # Calcula cuántos números faltan para completar el tamaño actual
        if needed > 0:                           # Si hacen falta números adicionales (siempre en la primera iteración)...
            all_numbers.extend(rng.randint(10_000_000, 99_999_999) for _ in range(needed))
            # ...extiende la lista con 'needed' enteros aleatorios de exactamente 8 dígitos

        print(f"  Generando {filename} ({size:,} elementos) ...", end=" ", flush=True)  # Informa el inicio de escritura
        with path.open("w", encoding="ascii", newline="\n") as f:  # Abre el archivo para escritura con saltos de línea Unix y codificación ASCII
            for n in all_numbers[:size]:         # Toma solo los primeros 'size' números de la lista acumulada
                f.write(str(n) + "\n")           # Escribe cada entero en una línea separada
        print("OK")                              # Confirma que el archivo fue generado exitosamente

    print("Datos listos en:", DATA_DIR)          # Mensaje final indicando que todos los archivos están disponibles


if __name__ == "__main__":  # Solo ejecuta generate_all() si este script es el punto de entrada (no si es importado)
    generate_all()          # Llama a la función principal que genera todos los archivos de datos