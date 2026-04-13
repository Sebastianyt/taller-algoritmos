"""
Benchmark de algoritmos de ordenamiento — SOLO PYTHON.
Lee datos desde archivos pre-generados (no los regenera).
Mide ÚNICAMENTE el tiempo de sort, sin I/O.

Shaker Sort se ejecuta sin timeout, sin importar cuánto tarde.
Se muestra en consola cuánto lleva cada ejecución larga (cada 5 s).

Uso:
    python sorting/python/benchmark_sorting.py
"""
from __future__ import annotations  # Permite usar anotaciones de tipo modernas en versiones anteriores de Python

import csv        # Para escribir archivos CSV con los resultados
import json       # Para escribir archivos JSON con los resultados
import subprocess # Para ejecutar subprocesos externos (el script generador de datos)
import sys        # Para manipular el path del sistema y el intérprete actual
import time       # Para medir tiempos de ejecución
import threading  # Para correr los sorts en hilos secundarios y mostrar progreso
from pathlib import Path  # Para manejar rutas de archivos de forma multiplataforma

# ── Rutas ──────────────────────────────────────────────────────────────────────
_SORT_DIR = Path(__file__).resolve().parent  # Directorio donde vive este script
if str(_SORT_DIR) not in sys.path:           # Si ese directorio no está en el path de Python...
    sys.path.insert(0, str(_SORT_DIR))       # ...lo agrega al inicio para poder importar módulos locales

# Importa cada algoritmo de ordenamiento desde sus módulos locales
from dual_pivot_quicksort import dualPivotQuickSort  # Importa QuickSort de doble pivote
from heap_sort import heapSort                        # Importa Heap Sort
from merge_sort import mergeSort                      # Importa Merge Sort
from radix_sort import radixSort                      # Importa Radix Sort
from shaker_sort import cocktailSort, ShakerSortTimeout  # Importa Shaker Sort y su excepción de timeout

ROOT = Path(__file__).resolve().parents[2]  # Sube 2 niveles desde el script para llegar a la raíz del proyecto
DATA_DIR = ROOT / "data"                    # Carpeta donde se encuentran los archivos de datos de entrada
RESULTS_DIR = ROOT / "results"              # Carpeta donde se guardarán los resultados del benchmark
GEN_SCRIPT = ROOT / "scripts" / "generate_sorting_data.py"  # Ruta al script que genera los datos de prueba

# Lista de tamaños a probar: cada tupla es (cantidad de elementos, nombre del archivo)
SIZES: list[tuple[int, str]] = [
    (10_000,    "sorting_10000.txt"),    # Arreglo pequeño de 10.000 elementos
    (100_000,   "sorting_100000.txt"),   # Arreglo mediano de 100.000 elementos
    (1_000_000, "sorting_1000000.txt"),  # Arreglo grande de 1.000.000 elementos
]

SHAKER_TIMEOUT_SECONDS = 10 * 60  # Tiempo máximo permitido para Shaker Sort: 10 minutos en segundos

# Lista de algoritmos a evaluar: cada tupla es (nombre, complejidad, función de sort)
ALGORITHMS: list[tuple[str, str, object]] = [
    ("Shaker Sort",          "O(n^2)",              lambda a: cocktailSort(a, timeout_seconds=SHAKER_TIMEOUT_SECONDS)),  # Shaker Sort con timeout configurable
    ("Dual-Pivot QuickSort", "O(n log n) promedio", lambda a: dualPivotQuickSort(a)),  # QuickSort optimizado con dos pivotes
    ("Heap Sort",            "O(n log n)",           heapSort),                         # Heap Sort clásico
    ("Merge Sort",           "O(n log n)",           lambda a: mergeSort(a)),            # Merge Sort clásico
    ("Radix Sort",           "O(d * n), d=8",        radixSort),                        # Radix Sort con 8 dígitos de base
]


# ── Generación / carga de datos ────────────────────────────────────────────────
def ensure_data() -> None:
    """Genera los archivos de datos si no existen."""
    subprocess.run([sys.executable, str(GEN_SCRIPT)], check=True, cwd=str(ROOT))  # Ejecuta el script generador usando el mismo intérprete Python actual


def load_data(path: Path) -> list[int]:
    """Lee enteros desde archivo de texto plano."""
    print(f"    Leyendo {path.name} ...", end=" ", flush=True)  # Muestra en consola qué archivo se está leyendo
    t0 = time.perf_counter()                                    # Registra el tiempo de inicio de lectura
    with path.open("r", encoding="ascii") as f:                 # Abre el archivo en modo lectura con codificación ASCII
        data = [int(line) for line in f if line.strip()]        # Lee cada línea no vacía y la convierte a entero
    elapsed = time.perf_counter() - t0                          # Calcula el tiempo total de lectura
    print(f"{elapsed:.1f}s - {len(data):,} elementos")          # Muestra el tiempo y cantidad de elementos leídos
    return data                                                  # Retorna la lista de enteros cargada


# ── Ejecución con progreso (sin timeout) ──────────────────────────────────────
def run_with_progress(fn, arr: list, name: str) -> float:
    """
    Ejecuta fn(arr) en un hilo secundario mientras el hilo principal
    imprime cada 5 segundos cuánto tiempo lleva.
    Sin timeout — se espera hasta que termine.
    Retorna los segundos de sort puro.
    """
    result: list = [None, None]   # Lista compartida para guardar [tiempo_elapsed, excepción]

    def worker():
        t0 = time.perf_counter()  # Registra el inicio del sort
        try:
            fn(arr)               # Ejecuta la función de ordenamiento sobre el arreglo
        except Exception as exc:  # Si ocurre cualquier excepción durante el sort...
            result[1] = exc       # ...la guarda en la posición 1 del resultado
        result[0] = time.perf_counter() - t0  # Guarda el tiempo transcurrido en la posición 0

    thread = threading.Thread(target=worker, daemon=True)  # Crea un hilo daemon que ejecuta la función worker
    thread.start()                                         # Inicia el hilo secundario

    tick = 0                       # Contador de segundos transcurridos para el reporte de progreso
    while thread.is_alive():       # Mientras el hilo de ordenamiento siga ejecutándose...
        thread.join(timeout=5.0)   # ...espera hasta 5 segundos a que termine
        if thread.is_alive():      # Si después de 5s el hilo aún sigue vivo...
            tick += 5              # ...incrementa el contador de segundos
            print(f"      [RUNNING] {name} sigue corriendo... {tick}s transcurridos", flush=True)  # Reporta el progreso en consola

    if result[1] is not None:      # Si el worker capturó alguna excepción...
        raise result[1]            # ...la relanza en el hilo principal

    return result[0]               # Retorna el tiempo total de ejecución del sort en segundos


# ── Benchmark Python ──────────────────────────────────────────────────────────
def run_python_benchmarks() -> list[dict]:
    """Ejecuta todos los algoritmos sobre cada tamaño de arreglo."""
    rows: list[dict] = []  # Lista que acumulará los resultados de cada combinación algoritmo/tamaño

    for n, filename in SIZES:              # Itera sobre cada tamaño de arreglo definido
        data_path = DATA_DIR / filename    # Construye la ruta completa al archivo de datos
        print(f"\n  -- n = {n:,} --")     # Imprime un separador visual con el tamaño actual
        data = load_data(data_path)        # Carga los datos desde el archivo correspondiente

        for name, complexity, sort_fn in ALGORITHMS:  # Itera sobre cada algoritmo definido
            arr = data[:n].copy()                      # Crea una copia del arreglo de tamaño n para no modificar el original
            print(f"    [{name}] ejecutando ...", flush=True)  # Indica en consola que el algoritmo está comenzando

            timed_out = False  # Bandera para saber si el algoritmo superó el tiempo límite
            secs = -1.0        # Tiempo de ejecución inicial en -1 (indica "no ejecutado aún")
            try:
                secs = run_with_progress(sort_fn, arr, name)          # Ejecuta el sort y mide su tiempo
                label = f"{secs*1000:.1f} ms" if secs < 1 else f"{secs:.3f} s"  # Formatea el tiempo: ms si < 1s, segundos si ≥ 1s
                print(f"    [{name}] OK {label}")                      # Imprime el resultado exitoso con su tiempo
            except ShakerSortTimeout:                                  # Si Shaker Sort lanzó su excepción de timeout...
                timed_out = True                                       # ...marca la bandera de timeout
                print(f"    [{name}] TIMEOUT ({SHAKER_TIMEOUT_SECONDS}s)")  # Informa del timeout en consola

            rows.append({               # Agrega un diccionario con los resultados de esta ejecución
                "algorithm":   name,    # Nombre del algoritmo ejecutado
                "language":    "Python", # Lenguaje de programación usado
                "n":           n,        # Tamaño del arreglo ordenado
                "timeSeconds": secs,     # Tiempo de ejecución en segundos (-1 si hubo timeout)
                "complexity":  complexity,  # Complejidad teórica del algoritmo
                "timedOut":    timed_out,   # Indica si el algoritmo superó el tiempo límite
            })

    return rows  # Retorna todos los resultados acumulados


# ── Exportación ───────────────────────────────────────────────────────────────
def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = ["algorithm", "language", "n", "timeSeconds", "complexity", "timedOut"]  # Define el orden de las columnas del CSV
    with path.open("w", newline="", encoding="utf-8") as f:  # Abre el archivo CSV para escritura en UTF-8
        w = csv.DictWriter(f, fieldnames=fieldnames)         # Crea un escritor de CSV basado en diccionarios
        w.writeheader()                                       # Escribe la fila de encabezados con los nombres de columna
        for row in rows:                                      # Itera sobre cada resultado del benchmark
            w.writerow({                                      # Escribe una fila con los datos formateados
                "algorithm":   row["algorithm"],              # Nombre del algoritmo
                "language":    row["language"],               # Lenguaje usado
                "n":           row["n"],                      # Tamaño del arreglo
                "timeSeconds": f"{row['timeSeconds']:.9f}",  # Tiempo con 9 decimales de precisión
                "complexity":  row["complexity"],             # Complejidad teórica
                "timedOut":    bool(row.get("timedOut", False)),  # Convierte a booleano explícito (por si acaso)
            })


def write_json(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:              # Abre el archivo JSON para escritura en UTF-8
        json.dump(rows, f, indent=2, ensure_ascii=False)     # Serializa la lista de resultados con indentación y soporte UTF-8


# ── Gráfico ───────────────────────────────────────────────────────────────────
def plot_bars(rows: list[dict], out_png: Path) -> None:
    try:
        import matplotlib.pyplot as plt  # Importa matplotlib para graficar (dentro del try por si no está instalado)
        import numpy as np               # Importa numpy para manejar arreglos numéricos y posiciones de barras
    except ImportError as e:
        print(f"  matplotlib no instalado — se omite el gráfico. ({e})")  # Si no están instalados, avisa y sale
        return                                                              # Sale de la función sin graficar

    order = [a[0] for a in ALGORITHMS]  # Extrae solo los nombres de los algoritmos en el orden definido
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=False)  # Crea una figura con 3 subgráficos lado a lado (uno por tamaño)
    fig.suptitle(                        # Agrega un título general a toda la figura
        "Benchmark Algoritmos de Ordenamiento — Python\n"
        "(tiempo de sort puro, sin I/O)",
        fontsize=13, fontweight="bold",
    )

    color = "#DD8452"  # Define el color naranja para las barras del gráfico

    for ax, (n, _) in zip(axes, SIZES):  # Itera sobre cada subgráfico y su tamaño correspondiente
        py_map = {r["algorithm"]: r for r in rows if r["n"] == n and r["language"] == "Python"}  # Filtra resultados Python para este tamaño n
        x = np.arange(len(order))        # Crea posiciones numéricas en el eje X para cada algoritmo
        vals = [py_map[k]["timeSeconds"] if k in py_map else 0 for k in order]  # Obtiene el tiempo de cada algoritmo (0 si no existe)

        bars = ax.bar(x, vals, 0.55, label="Python", color=color, edgecolor="white", linewidth=0.5)  # Dibuja las barras con ancho 0.55 y borde blanco
        ax.set_title(f"n = {n:,}", fontsize=11, fontweight="bold")   # Establece el título del subgráfico con el tamaño n
        ax.set_xticks(x)                                              # Ubica las marcas del eje X en las posiciones de los algoritmos
        ax.set_xticklabels(order, rotation=28, ha="right", fontsize=8)  # Etiqueta el eje X con los nombres de algoritmos rotados 28°
        ax.set_ylabel("Tiempo (s)")                                   # Etiqueta el eje Y como "Tiempo (s)"
        ax.legend()                                                    # Muestra la leyenda del subgráfico

        for bar, v in zip(bars, vals):   # Itera sobre cada barra y su valor para añadir anotaciones
            if v <= 0:                   # Si el valor es 0 o negativo (timeout o no ejecutado)...
                continue                 # ...no agrega etiqueta sobre esa barra
            h = bar.get_height()         # Obtiene la altura de la barra (igual al valor)
            cx = bar.get_x() + bar.get_width() / 2  # Calcula el centro horizontal de la barra
            label = f"{v*1000:.2f} ms" if v < 1 else f"{v:.3f} s"  # Formatea el tiempo: ms si < 1s, segundos si ≥ 1s
            ax.annotate(                 # Agrega una anotación de texto encima de la barra
                label,
                xy=(cx, h), xytext=(0, 3), textcoords="offset points",  # Posiciona el texto 3 puntos arriba del tope de la barra
                ha="center", va="bottom", fontsize=7,                     # Centra horizontalmente y alinea al fondo del texto
            )

    plt.tight_layout()                          # Ajusta automáticamente los márgenes para evitar solapamientos
    plt.savefig(out_png, dpi=150, bbox_inches="tight")  # Guarda el gráfico como PNG con 150 DPI y sin recortes
    plt.close()                                 # Cierra la figura para liberar memoria
    print(f"\n  Gráfico guardado en {out_png}") # Informa en consola dónde se guardó el gráfico


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)  # Crea la carpeta de resultados si no existe (y sus padres también)
    print("=" * 60)                                 # Imprime una línea decorativa de separación
    print("  BENCHMARK DE ORDENAMIENTO - PYTHON")  # Imprime el título del benchmark
    print("=" * 60)                                 # Imprime otra línea decorativa

    print("\n[1] Verificando/generando archivos de datos ...")  # Informa el paso 1
    ensure_data()                                               # Genera los archivos de datos si no existen

    print("\n[2] Ejecutando benchmarks Python ...")  # Informa el paso 2
    py_rows = run_python_benchmarks()               # Ejecuta todos los algoritmos y recopila resultados

    py_rows.sort(key=lambda r: (r["n"], r["algorithm"]))  # Ordena los resultados por tamaño n y luego por nombre de algoritmo

    csv_path  = RESULTS_DIR / "sorting_benchmark_python.csv"   # Ruta de salida para el archivo CSV
    json_path = RESULTS_DIR / "sorting_benchmark_python.json"  # Ruta de salida para el archivo JSON
    png_path  = RESULTS_DIR / "sorting_benchmark_python.png"   # Ruta de salida para el gráfico PNG

    write_csv(csv_path, py_rows)    # Exporta los resultados al archivo CSV
    write_json(json_path, py_rows)  # Exporta los resultados al archivo JSON

    print(f"\n[3] Resultados exportados:")      # Informa el paso 3
    print(f"    CSV  → {csv_path}")             # Muestra la ruta del CSV generado
    print(f"    JSON → {json_path}")            # Muestra la ruta del JSON generado

    plot_bars(py_rows, png_path)  # Genera y guarda el gráfico de barras comparativo

    print("\n" + "=" * 60)                      # Imprime una línea decorativa de cierre
    print("  BENCHMARK PYTHON COMPLETADO")      # Mensaje final de éxito
    print("=" * 60)                             # Última línea decorativa


if __name__ == "__main__":  # Solo ejecuta main() si este script es el punto de entrada (no si es importado)
    main()                  # Llama a la función principal para arrancar el benchmark