"""
Benchmark de algoritmos de ordenamiento — SOLO PYTHON.
Lee datos desde archivos pre-generados (no los regenera).
Mide ÚNICAMENTE el tiempo de sort, sin I/O.

Shaker Sort se ejecuta sin timeout, sin importar cuánto tarde.
Se muestra en consola cuánto lleva cada ejecución larga (cada 5 s).

Uso:
    python sorting/python/benchmark_sorting.py
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
import threading
from pathlib import Path

# ── Rutas ──────────────────────────────────────────────────────────────────────
_SORT_DIR = Path(__file__).resolve().parent
if str(_SORT_DIR) not in sys.path:
    sys.path.insert(0, str(_SORT_DIR))

from dual_pivot_quicksort import dualPivotQuickSort
from heap_sort import heapSort
from merge_sort import mergeSort
from radix_sort import radixSort
from shaker_sort import cocktailSort, ShakerSortTimeout

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
GEN_SCRIPT = ROOT / "scripts" / "generate_sorting_data.py"

# Tamaños y sus archivos correspondientes
SIZES: list[tuple[int, str]] = [
    (10_000,    "sorting_10000.txt"),
    (100_000,   "sorting_100000.txt"),
    (1_000_000, "sorting_1000000.txt"),
]

SHAKER_TIMEOUT_SECONDS = 10 * 60  # 10 minutos

ALGORITHMS: list[tuple[str, str, object]] = [
    ("Shaker Sort",          "O(n^2)",              lambda a: cocktailSort(a, timeout_seconds=SHAKER_TIMEOUT_SECONDS)),
    ("Dual-Pivot QuickSort", "O(n log n) promedio", lambda a: dualPivotQuickSort(a)),
    ("Heap Sort",            "O(n log n)",           heapSort),
    ("Merge Sort",           "O(n log n)",           lambda a: mergeSort(a)),
    ("Radix Sort",           "O(d * n), d=8",        radixSort),
]


# ── Generación / carga de datos ────────────────────────────────────────────────
def ensure_data() -> None:
    """Genera los archivos de datos si no existen."""
    subprocess.run([sys.executable, str(GEN_SCRIPT)], check=True, cwd=str(ROOT))


def load_data(path: Path) -> list[int]:
    """Lee enteros desde archivo de texto plano."""
    print(f"    Leyendo {path.name} ...", end=" ", flush=True)
    t0 = time.perf_counter()
    with path.open("r", encoding="ascii") as f:
        data = [int(line) for line in f if line.strip()]
    elapsed = time.perf_counter() - t0
    print(f"{elapsed:.1f}s - {len(data):,} elementos")
    return data


# ── Ejecución con progreso (sin timeout) ──────────────────────────────────────
def run_with_progress(fn, arr: list, name: str) -> float:
    """
    Ejecuta fn(arr) en un hilo secundario mientras el hilo principal
    imprime cada 5 segundos cuánto tiempo lleva.
    Sin timeout — se espera hasta que termine.
    Retorna los segundos de sort puro.
    """
    result: list = [None, None]   # [elapsed_seconds, exception]

    def worker():
        t0 = time.perf_counter()
        try:
            fn(arr)
        except Exception as exc:
            result[1] = exc
        result[0] = time.perf_counter() - t0

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    tick = 0
    while thread.is_alive():
        thread.join(timeout=5.0)
        if thread.is_alive():
            tick += 5
            print(f"      [RUNNING] {name} sigue corriendo... {tick}s transcurridos", flush=True)

    if result[1] is not None:
        raise result[1]

    return result[0]


# ── Benchmark Python ──────────────────────────────────────────────────────────
def run_python_benchmarks() -> list[dict]:
    """Ejecuta todos los algoritmos sobre cada tamaño de arreglo."""
    rows: list[dict] = []

    for n, filename in SIZES:
        data_path = DATA_DIR / filename
        print(f"\n  -- n = {n:,} --")
        data = load_data(data_path)

        for name, complexity, sort_fn in ALGORITHMS:
            arr = data[:n].copy()
            print(f"    [{name}] ejecutando ...", flush=True)

            timed_out = False
            secs = -1.0
            try:
                secs = run_with_progress(sort_fn, arr, name)
                label = f"{secs*1000:.1f} ms" if secs < 1 else f"{secs:.3f} s"
                print(f"    [{name}] OK {label}")
            except ShakerSortTimeout:
                timed_out = True
                print(f"    [{name}] TIMEOUT ({SHAKER_TIMEOUT_SECONDS}s)")

            rows.append({
                "algorithm":   name,
                "language":    "Python",
                "n":           n,
                "timeSeconds": secs,
                "complexity":  complexity,
                "timedOut":    timed_out,
            })

    return rows


# ── Exportación ───────────────────────────────────────────────────────────────
def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = ["algorithm", "language", "n", "timeSeconds", "complexity", "timedOut"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({
                "algorithm":   row["algorithm"],
                "language":    row["language"],
                "n":           row["n"],
                "timeSeconds": f"{row['timeSeconds']:.9f}",
                "complexity":  row["complexity"],
                "timedOut":    bool(row.get("timedOut", False)),
            })


def write_json(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)


# ── Gráfico ───────────────────────────────────────────────────────────────────
def plot_bars(rows: list[dict], out_png: Path) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        print(f"  matplotlib no instalado — se omite el gráfico. ({e})")
        return

    order = [a[0] for a in ALGORITHMS]
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=False)
    fig.suptitle(
        "Benchmark Algoritmos de Ordenamiento — Python\n"
        "(tiempo de sort puro, sin I/O)",
        fontsize=13, fontweight="bold",
    )

    color = "#DD8452"

    for ax, (n, _) in zip(axes, SIZES):
        py_map = {r["algorithm"]: r for r in rows if r["n"] == n and r["language"] == "Python"}
        x = np.arange(len(order))
        vals = [py_map[k]["timeSeconds"] if k in py_map else 0 for k in order]

        bars = ax.bar(x, vals, 0.55, label="Python", color=color, edgecolor="white", linewidth=0.5)
        ax.set_title(f"n = {n:,}", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(order, rotation=28, ha="right", fontsize=8)
        ax.set_ylabel("Tiempo (s)")
        ax.legend()

        for bar, v in zip(bars, vals):
            if v <= 0:
                continue
            h = bar.get_height()
            cx = bar.get_x() + bar.get_width() / 2
            label = f"{v*1000:.2f} ms" if v < 1 else f"{v:.3f} s"
            ax.annotate(
                label,
                xy=(cx, h), xytext=(0, 3), textcoords="offset points",
                ha="center", va="bottom", fontsize=7,
            )

    plt.tight_layout()
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Gráfico guardado en {out_png}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("  BENCHMARK DE ORDENAMIENTO - PYTHON")
    print("=" * 60)

    print("\n[1] Verificando/generando archivos de datos ...")
    ensure_data()

    print("\n[2] Ejecutando benchmarks Python ...")
    py_rows = run_python_benchmarks()

    py_rows.sort(key=lambda r: (r["n"], r["algorithm"]))

    csv_path  = RESULTS_DIR / "sorting_benchmark_python.csv"
    json_path = RESULTS_DIR / "sorting_benchmark_python.json"
    png_path  = RESULTS_DIR / "sorting_benchmark_python.png"

    write_csv(csv_path, py_rows)
    write_json(json_path, py_rows)

    print(f"\n[3] Resultados exportados:")
    print(f"    CSV  → {csv_path}")
    print(f"    JSON → {json_path}")

    plot_bars(py_rows, png_path)

    print("\n" + "=" * 60)
    print("  BENCHMARK PYTHON COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    main()
