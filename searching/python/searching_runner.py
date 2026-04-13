"""
Benchmark de algoritmos de busqueda — SOLO PYTHON (Punto 2).

- Lee datos desde archivos pre-generados en data_searching/ (no regenera).
- Mide UNICAMENTE el tiempo de busqueda (sin I/O).
- Exporta resultados en results_searching/ (CSV/JSON) y grafica (PNG).

Uso:
    python searching/python/searching_runner.py
"""
from __future__ import annotations  # Permite usar anotaciones de tipo modernas en versiones anteriores de Python

import csv        # Para escribir archivos CSV con los resultados
import json       # Para escribir archivos JSON con los resultados
import subprocess # Para ejecutar subprocesos externos (el script generador de datos)
import sys        # Para manipular el path del sistema y el intérprete actual
import time       # Para medir tiempos de ejecución con alta precisión
from pathlib import Path  # Para manejar rutas de archivos de forma multiplataforma

_SEARCH_DIR = Path(__file__).resolve().parent  # Directorio donde vive este script
if str(_SEARCH_DIR) not in sys.path:           # Si ese directorio no está en el path de Python...
    sys.path.insert(0, str(_SEARCH_DIR))       # ...lo agrega al inicio para poder importar módulos locales

# Importa cada algoritmo de búsqueda desde sus módulos locales
from binary_search import binarySearch    # Importa Búsqueda Binaria
from ternary_search import ternarySearch  # Importa Búsqueda Ternaria
from jump_search import jumpSearch        # Importa Búsqueda por Saltos

ROOT = Path(__file__).resolve().parents[2]              # Sube 2 niveles desde el script para llegar a la raíz del proyecto
DATA_DIR = ROOT / "data_searching"                      # Carpeta donde se encuentran los archivos de datos de entrada
RESULTS_DIR = ROOT / "results_searching"                # Carpeta donde se guardarán los resultados del benchmark
GEN_SCRIPT = ROOT / "scripts" / "generate_searching_data.py"  # Ruta al script que genera los datos de prueba

# Lista de tamaños a probar: cada tupla es (cantidad de elementos, archivo de arreglo, archivo de queries)
SIZES: list[tuple[int, str, str]] = [
    (10_000,    "searching_10000.txt",   "queries_10000.txt"),   # Arreglo pequeño de 10.000 elementos
    (100_000,   "searching_100000.txt",  "queries_100000.txt"),  # Arreglo mediano de 100.000 elementos
    (1_000_000, "searching_1000000.txt", "queries_1000000.txt"), # Arreglo grande de 1.000.000 elementos
]

# Lista de algoritmos a evaluar: cada tupla es (nombre, complejidad, función de búsqueda)
ALGORITHMS: list[tuple[str, str, object]] = [
    ("Binary Search",  "O(log n)",   binarySearch),                    # Búsqueda binaria clásica
    ("Ternary Search", "O(log n)",   ternarySearch),                   # Búsqueda ternaria (divide en 3 partes)
    ("Jump Search",    "O(sqrt(n))", lambda a, x: jumpSearch(a, x)),   # Búsqueda por saltos envuelta en lambda para uniformar la firma
]


def ensure_data() -> None:
    subprocess.run([sys.executable, str(GEN_SCRIPT)], check=True, cwd=str(ROOT))
    # Ejecuta el script generador usando el mismo intérprete Python actual, desde la raíz del proyecto


def load_ints(path: Path) -> list[int]:
    with path.open("r", encoding="ascii") as f:          # Abre el archivo en modo lectura con codificación ASCII
        return [int(line) for line in f if line.strip()] # Lee cada línea no vacía y la convierte a entero, retornando la lista


def run_python_benchmarks() -> list[dict]:
    rows: list[dict] = []  # Lista que acumulará los resultados de cada combinación algoritmo/tamaño

    for n, arr_file, q_file in SIZES:           # Itera sobre cada tamaño y sus archivos correspondientes
        arr_path = DATA_DIR / arr_file           # Construye la ruta completa al archivo del arreglo ordenado
        q_path   = DATA_DIR / q_file            # Construye la ruta completa al archivo de queries

        print(f"\n  -- n = {n:,} --")           # Imprime un separador visual con el tamaño actual formateado con comas
        print(f"    Cargando arreglo: {arr_file}") # Indica qué archivo de arreglo se está cargando
        arr = load_ints(arr_path)               # Carga los enteros del arreglo ordenado desde el archivo
        print(f"    Cargando queries: {q_file}") # Indica qué archivo de queries se está cargando
        queries = load_ints(q_path)             # Carga los valores a buscar desde el archivo de queries

        for name, complexity, fn in ALGORITHMS:  # Itera sobre cada algoritmo de búsqueda definido
            print(f"    [{name}] ejecutando ...", flush=True)  # Indica que el algoritmo está comenzando, vaciando el buffer

            # Medir SOLO busqueda (loop de queries)
            t0 = time.perf_counter()             # Registra el tiempo exacto de inicio de todas las búsquedas
            checksum = 0                         # Acumulador de resultados para verificar corrección y evitar optimizaciones del intérprete
            for q in queries:                    # Itera sobre cada valor a buscar en el arreglo
                checksum += fn(arr, q)           # Ejecuta la búsqueda y acumula el índice retornado en el checksum
            secs = time.perf_counter() - t0      # Calcula el tiempo total de todas las búsquedas en segundos

            label = f"{secs*1000:.1f} ms" if secs < 1 else f"{secs:.3f} s"  # Formatea el tiempo: ms si < 1s, segundos si ≥ 1s
            print(f"    [{name}] OK {label} (checksum={checksum})") # Imprime el resultado exitoso con tiempo y checksum

            rows.append({                        # Agrega un diccionario con los resultados de esta ejecución
                "algorithm":   name,             # Nombre del algoritmo ejecutado
                "language":    "Python",         # Lenguaje de programación usado
                "n":           n,                # Tamaño del arreglo sobre el que se buscó
                "timeSeconds": secs,             # Tiempo total de todas las búsquedas en segundos
                "complexity":  complexity,       # Complejidad teórica del algoritmo
            })

    return rows  # Retorna todos los resultados acumulados


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = ["algorithm", "language", "n", "timeSeconds", "complexity"]  # Define el orden de las columnas del CSV
    with path.open("w", newline="", encoding="utf-8") as f:  # Abre el archivo CSV para escritura en UTF-8
        w = csv.DictWriter(f, fieldnames=fieldnames)          # Crea un escritor de CSV basado en diccionarios
        w.writeheader()                                        # Escribe la fila de encabezados con los nombres de columna
        for row in rows:                                       # Itera sobre cada resultado del benchmark
            w.writerow({                                       # Escribe una fila con los datos formateados
                "algorithm":   row["algorithm"],               # Nombre del algoritmo
                "language":    row["language"],                # Lenguaje usado
                "n":           row["n"],                       # Tamaño del arreglo
                "timeSeconds": f"{row['timeSeconds']:.9f}",   # Tiempo con 9 decimales de precisión
                "complexity":  row["complexity"],              # Complejidad teórica
            })


def write_json(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:              # Abre el archivo JSON para escritura en UTF-8
        json.dump(rows, f, indent=2, ensure_ascii=False)     # Serializa la lista de resultados con indentación y soporte UTF-8


def plot_bars(rows: list[dict], out_png: Path) -> None:
    try:
        import matplotlib.pyplot as plt  # Importa matplotlib para graficar (dentro del try por si no está instalado)
        import numpy as np               # Importa numpy para manejar posiciones numéricas de las barras
    except ImportError as e:
        print(f"matplotlib no instalado - se omite el grafico. ({e})")  # Si no están instalados, avisa y sale
        return                                                            # Sale de la función sin graficar

    order = [a[0] for a in ALGORITHMS]  # Extrae solo los nombres de los algoritmos en el orden definido
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=False)  # Crea una figura con 3 subgráficos lado a lado (uno por tamaño)
    fig.suptitle(                        # Agrega un título general a toda la figura
        "Benchmark Algoritmos de Busqueda - Python\n"
        "Tiempo de busqueda puro (sin I/O)",
        fontsize=13,
        fontweight="bold",
    )

    for ax, (n, _, _) in zip(axes, SIZES):  # Itera sobre cada subgráfico y su tamaño (ignora los nombres de archivo con _)
        mp = {r["algorithm"]: r for r in rows if r["n"] == n and r["language"] == "Python"}
        # Filtra los resultados Python para este tamaño n y los indexa por nombre de algoritmo
        x = np.arange(len(order))            # Crea posiciones numéricas en el eje X para cada algoritmo
        vals = [mp[k]["timeSeconds"] if k in mp else 0 for k in order]  # Obtiene el tiempo de cada algoritmo (0 si no existe)
        bars = ax.bar(x, vals, 0.55, label="Python", color="#4C72B0", edgecolor="white", linewidth=0.6)
        # Dibuja las barras azules con ancho 0.55 y borde blanco fino
        ax.set_title(f"n = {n:,}", fontsize=11, fontweight="bold")      # Establece el título del subgráfico con el tamaño n
        ax.set_xticks(x)                                                 # Ubica las marcas del eje X en las posiciones de los algoritmos
        ax.set_xticklabels(order, rotation=20, ha="right", fontsize=9)  # Etiqueta el eje X con los nombres rotados 20°
        ax.set_ylabel("Tiempo (s)")                                      # Etiqueta el eje Y como "Tiempo (s)"
        ax.legend()                                                       # Muestra la leyenda del subgráfico

        for bar, v in zip(bars, vals):  # Itera sobre cada barra y su valor para añadir anotaciones de tiempo
            if v <= 0:                  # Si el valor es 0 o negativo (no ejecutado o error)...
                continue                # ...no agrega etiqueta sobre esa barra
            h  = bar.get_height()      # Obtiene la altura de la barra (igual al valor de tiempo)
            cx = bar.get_x() + bar.get_width() / 2  # Calcula el centro horizontal de la barra
            label = f"{v*1000:.2f} ms" if v < 1 else f"{v:.3f} s"  # Formatea el tiempo: ms si < 1s, segundos si ≥ 1s
            ax.annotate(label, xy=(cx, h), xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8)
            # Agrega la etiqueta de tiempo 3 puntos arriba del tope de la barra, centrada horizontalmente

    plt.tight_layout()                                   # Ajusta automáticamente los márgenes para evitar solapamientos
    plt.savefig(out_png, dpi=160, bbox_inches="tight")  # Guarda el gráfico como PNG con 160 DPI y sin recortes
    plt.close()                                          # Cierra la figura para liberar memoria
    print(f"\n  Grafico guardado en {out_png}")          # Informa en consola dónde se guardó el gráfico


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)  # Crea la carpeta de resultados si no existe (y sus padres también)
    print("=" * 60)                                 # Imprime una línea decorativa de separación
    print("  BENCHMARK DE BUSQUEDA - PYTHON")       # Imprime el título del benchmark
    print("=" * 60)                                 # Imprime otra línea decorativa

    print("\n[1] Verificando/generando archivos de datos ...") # Informa el paso 1
    ensure_data()                                              # Genera los archivos de datos si no existen

    print("\n[2] Ejecutando benchmarks Python ...")  # Informa el paso 2
    rows = run_python_benchmarks()                  # Ejecuta todos los algoritmos y recopila resultados
    rows.sort(key=lambda r: (r["n"], r["algorithm"]))  # Ordena los resultados por tamaño n y luego por nombre de algoritmo

    csv_path  = RESULTS_DIR / "searching_benchmark_python.csv"  # Ruta de salida para el archivo CSV
    json_path = RESULTS_DIR / "searching_benchmark_python.json" # Ruta de salida para el archivo JSON
    png_path  = RESULTS_DIR / "searching_benchmark_python.png"  # Ruta de salida para el gráfico PNG

    write_csv(csv_path, rows)    # Exporta los resultados al archivo CSV
    write_json(json_path, rows)  # Exporta los resultados al archivo JSON
    print("\n[3] Resultados exportados:")            # Informa el paso 3
    print(f"    CSV  -> {csv_path}")                # Muestra la ruta del CSV generado
    print(f"    JSON -> {json_path}")               # Muestra la ruta del JSON generado

    plot_bars(rows, png_path)  # Genera y guarda el gráfico de barras comparativo

    print("\n" + "=" * 60)                          # Imprime una línea decorativa de cierre
    print("  BENCHMARK PYTHON COMPLETADO")          # Mensaje final de éxito
    print("=" * 60)                                 # Última línea decorativa


if __name__ == "__main__":  # Solo ejecuta main() si este script es el punto de entrada (no si es importado)
    main()                  # Llama a la función principal para arrancar el benchmark