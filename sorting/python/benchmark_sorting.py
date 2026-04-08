"""
Punto 1: carga datos desde archivo (generados una sola vez), mide solo el sort en Python,
invoca el benchmark Java para los mismos datos, exporta CSV/JSON y genera gráfico de barras.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from pathlib import Path

_SORT_DIR = Path(__file__).resolve().parent
if str(_SORT_DIR) not in sys.path:
    sys.path.insert(0, str(_SORT_DIR))

from dual_pivot_quicksort import dualPivotQuickSort
from heap_sort import heapSort
from merge_sort import mergeSort
from radix_sort import radixSort
from shaker_sort import cocktailSort

ROOT = Path(__file__).resolve().parents[2]
JAVA_DIR = ROOT / "sorting" / "java"
DATA_PATH = ROOT / "data" / "sorting_1000000.txt"
RESULTS_DIR = ROOT / "results"
GEN_SCRIPT = ROOT / "scripts" / "generate_sorting_data.py"

SIZES = (10_000, 100_000, 1_000_000)

ALGORITHMS: list[tuple[str, str, object]] = [
    ("Shaker Sort", "O(n^2)", cocktailSort),
    ("Dual-Pivot QuickSort", "O(n log n) promedio", lambda a: dualPivotQuickSort(a, 0, len(a) - 1)),
    ("Heap Sort", "O(n log n)", heapSort),
    ("Merge Sort", "O(n log n)", lambda a: mergeSort(a, 0, len(a) - 1)),
    ("Radix Sort", "O(d * n), d=8", radixSort),
]


def ensure_data() -> None:
    subprocess.run([sys.executable, str(GEN_SCRIPT)], check=True, cwd=str(ROOT))


def load_ints(path: Path) -> list[int]:
    with path.open("r", encoding="ascii") as f:
        return [int(line) for line in f if line.strip()]


def run_python_benchmarks(full: list[int]) -> list[dict]:
    rows: list[dict] = []
    for n in SIZES:
        for name, complexity, sort_fn in ALGORITHMS:
            arr = full[:n].copy()
            t0 = time.perf_counter()
            sort_fn(arr)
            secs = time.perf_counter() - t0
            rows.append(
                {
                    "algorithm": name,
                    "language": "Python",
                    "n": n,
                    "timeSeconds": secs,
                    "complexity": complexity,
                }
            )
    return rows


def compile_and_run_java() -> list[dict]:
    java_files = sorted(JAVA_DIR.glob("*.java"))
    if not java_files:
        raise FileNotFoundError(f"No hay .java en {JAVA_DIR}")

    compile_cmd = ["javac", "-encoding", "UTF-8"] + [str(p) for p in java_files]
    r = subprocess.run(compile_cmd, cwd=str(JAVA_DIR), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            "javac falló (¿JDK instalado y en PATH?).\n"
            f"{r.stderr or r.stdout}"
        )

    partial = RESULTS_DIR / "sorting_java_partial.json"
    run_cmd = [
        "java",
        "-cp",
        str(JAVA_DIR),
        "SortingBenchmark",
        str(DATA_PATH),
        str(partial),
    ]
    r2 = subprocess.run(run_cmd, capture_output=True, text=True)
    if r2.returncode != 0:
        raise RuntimeError(f"Java benchmark falló:\n{r2.stderr or r2.stdout}")

    with partial.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = ["algorithm", "language", "n", "timeSeconds", "complexity"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(
                {
                    "algorithm": row["algorithm"],
                    "language": row["language"],
                    "n": row["n"],
                    "timeSeconds": f"{row['timeSeconds']:.9f}",
                    "complexity": row["complexity"],
                }
            )


def write_json(path: Path, rows: list[dict]) -> None:
    out = []
    for row in rows:
        out.append(
            {
                "algorithm": row["algorithm"],
                "language": row["language"],
                "n": row["n"],
                "timeSeconds": row["timeSeconds"],
                "complexity": row["complexity"],
            }
        )
    with path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


def plot_bars(rows: list[dict], out_png: Path) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        print("matplotlib no instalado; se omite el gráfico.", e)
        return

    order = [a[0] for a in ALGORITHMS]
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=False)
    fig.suptitle("Punto 1 — Ordenamiento: Java vs Python (tiempo de sort, sin I/O)")

    for ax, n in zip(axes, SIZES):
        java_t = {r["algorithm"]: r["timeSeconds"] for r in rows if r["n"] == n and r["language"] == "Java"}
        py_t = {r["algorithm"]: r["timeSeconds"] for r in rows if r["n"] == n and r["language"] == "Python"}
        x = np.arange(len(order))
        w = 0.35
        jvals = [java_t[k] for k in order]
        pvals = [py_t[k] for k in order]
        b1 = ax.bar(x - w / 2, jvals, w, label="Java")
        b2 = ax.bar(x + w / 2, pvals, w, label="Python")
        ax.set_title(f"n = {n:,}")
        ax.set_xticks(x)
        ax.set_xticklabels(order, rotation=25, ha="right")
        ax.set_ylabel("Tiempo (s)")
        ax.legend()

        def label_bars(bars):
            for b in bars:
                h = b.get_height()
                if h <= 0:
                    continue
                if h < 1e-3:
                    t = f"{h * 1000:.2f} ms"
                elif h < 1:
                    t = f"{h:.4f} s"
                else:
                    t = f"{h:.3f} s"
                ax.annotate(
                    t,
                    xy=(b.get_x() + b.get_width() / 2, h),
                    xytext=(0, 2),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=7,
                )

        label_bars(b1)
        label_bars(b2)

    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"Gráfico guardado en {out_png}")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ensure_data()
    if not DATA_PATH.exists():
        raise FileNotFoundError(DATA_PATH)

    print("Cargando datos (no incluido en la medición del sort)...")
    full = load_ints(DATA_PATH)
    if len(full) < 1_000_000:
        raise ValueError(f"Se esperan 1_000_000 enteros; hay {len(full)}")

    print("Ejecutando benchmarks en Python...")
    py_rows = run_python_benchmarks(full)

    print("Compilando y ejecutando benchmarks en Java...")
    java_rows = compile_and_run_java()

    combined = py_rows + java_rows
    combined.sort(key=lambda r: (r["n"], r["algorithm"], r["language"]))

    csv_path = RESULTS_DIR / "sorting_benchmark.csv"
    json_path = RESULTS_DIR / "sorting_benchmark.json"
    write_csv(csv_path, combined)
    write_json(json_path, combined)
    print(f"CSV:  {csv_path}")
    print(f"JSON: {json_path}")

    plot_bars(combined, RESULTS_DIR / "sorting_benchmark.png")


if __name__ == "__main__":
    main()
