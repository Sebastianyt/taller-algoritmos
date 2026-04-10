"""
Benchmark de algoritmos de busqueda — SOLO PYTHON (Punto 2).

- Lee datos desde archivos pre-generados en data_searching/ (no regenera).
- Mide UNICAMENTE el tiempo de busqueda (sin I/O).
- Exporta resultados en results_searching/ (CSV/JSON) y grafica (PNG).

Uso:
    python searching/python/searching_runner.py
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from pathlib import Path

_SEARCH_DIR = Path(__file__).resolve().parent
if str(_SEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_SEARCH_DIR))

from binary_search import binarySearch
from ternary_search import ternarySearch
from jump_search import jumpSearch

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data_searching"
RESULTS_DIR = ROOT / "results_searching"
GEN_SCRIPT = ROOT / "scripts" / "generate_searching_data.py"

SIZES: list[tuple[int, str, str]] = [
    (10_000, "searching_10000.txt", "queries_10000.txt"),
    (100_000, "searching_100000.txt", "queries_100000.txt"),
    (1_000_000, "searching_1000000.txt", "queries_1000000.txt"),
]

ALGORITHMS: list[tuple[str, str, object]] = [
    ("Binary Search", "O(log n)", binarySearch),
    ("Ternary Search", "O(log n)", ternarySearch),
    ("Jump Search", "O(sqrt(n))", lambda a, x: jumpSearch(a, x)),
]


def ensure_data() -> None:
    subprocess.run([sys.executable, str(GEN_SCRIPT)], check=True, cwd=str(ROOT))


def load_ints(path: Path) -> list[int]:
    with path.open("r", encoding="ascii") as f:
        return [int(line) for line in f if line.strip()]


def run_python_benchmarks() -> list[dict]:
    rows: list[dict] = []

    for n, arr_file, q_file in SIZES:
        arr_path = DATA_DIR / arr_file
        q_path = DATA_DIR / q_file

        print(f"\n  -- n = {n:,} --")
        print(f"    Cargando arreglo: {arr_file}")
        arr = load_ints(arr_path)
        print(f"    Cargando queries: {q_file}")
        queries = load_ints(q_path)

        for name, complexity, fn in ALGORITHMS:
            print(f"    [{name}] ejecutando ...", flush=True)

            # Medir SOLO busqueda (loop de queries)
            t0 = time.perf_counter()
            checksum = 0
            for q in queries:
                checksum += fn(arr, q)
            secs = time.perf_counter() - t0

            label = f"{secs*1000:.1f} ms" if secs < 1 else f"{secs:.3f} s"
            print(f"    [{name}] OK {label} (checksum={checksum})")

            rows.append({
                "algorithm": name,
                "language": "Python",
                "n": n,
                "timeSeconds": secs,
                "complexity": complexity,
            })

    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = ["algorithm", "language", "n", "timeSeconds", "complexity"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({
                "algorithm": row["algorithm"],
                "language": row["language"],
                "n": row["n"],
                "timeSeconds": f"{row['timeSeconds']:.9f}",
                "complexity": row["complexity"],
            })


def write_json(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)


def plot_bars(rows: list[dict], out_png: Path) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        print(f"matplotlib no instalado - se omite el grafico. ({e})")
        return

    order = [a[0] for a in ALGORITHMS]
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=False)
    fig.suptitle(
        "Benchmark Algoritmos de Busqueda - Python\n"
        "Tiempo de busqueda puro (sin I/O)",
        fontsize=13,
        fontweight="bold",
    )

    for ax, (n, _, _) in zip(axes, SIZES):
        mp = {r["algorithm"]: r for r in rows if r["n"] == n and r["language"] == "Python"}
        x = np.arange(len(order))
        vals = [mp[k]["timeSeconds"] if k in mp else 0 for k in order]
        bars = ax.bar(x, vals, 0.55, label="Python", color="#4C72B0", edgecolor="white", linewidth=0.6)
        ax.set_title(f"n = {n:,}", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(order, rotation=20, ha="right", fontsize=9)
        ax.set_ylabel("Tiempo (s)")
        ax.legend()

        for bar, v in zip(bars, vals):
            if v <= 0:
                continue
            h = bar.get_height()
            cx = bar.get_x() + bar.get_width() / 2
            label = f"{v*1000:.2f} ms" if v < 1 else f"{v:.3f} s"
            ax.annotate(label, xy=(cx, h), xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(out_png, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"\n  Grafico guardado en {out_png}")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("  BENCHMARK DE BUSQUEDA - PYTHON")
    print("=" * 60)

    print("\n[1] Verificando/generando archivos de datos ...")
    ensure_data()

    print("\n[2] Ejecutando benchmarks Python ...")
    rows = run_python_benchmarks()
    rows.sort(key=lambda r: (r["n"], r["algorithm"]))

    csv_path = RESULTS_DIR / "searching_benchmark_python.csv"
    json_path = RESULTS_DIR / "searching_benchmark_python.json"
    png_path = RESULTS_DIR / "searching_benchmark_python.png"

    write_csv(csv_path, rows)
    write_json(json_path, rows)
    print("\n[3] Resultados exportados:")
    print(f"    CSV  -> {csv_path}")
    print(f"    JSON -> {json_path}")

    plot_bars(rows, png_path)

    print("\n" + "=" * 60)
    print("  BENCHMARK PYTHON COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    main()

