"""
Genera gráfico comparativo (Python vs Java) a partir de resultados ya medidos.

- NO corre benchmarks.
- Lee:
    results/sorting_benchmark_python.json
    results/sorting_benchmark_java.json
- Produce:
    results/sorting_benchmark_all.json
    results/sorting_benchmark_all.csv
    results/sorting_benchmark_compare.png
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"

PY_JSON = RESULTS_DIR / "sorting_benchmark_python.json"
JAVA_JSON = RESULTS_DIR / "sorting_benchmark_java.json"

OUT_JSON = RESULTS_DIR / "sorting_benchmark_all.json"
OUT_CSV = RESULTS_DIR / "sorting_benchmark_all.csv"
OUT_PNG = RESULTS_DIR / "sorting_benchmark_compare.png"
OUT_JAVA_PNG = RESULTS_DIR / "sorting_benchmark_java.png"


def _load_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = ["algorithm", "language", "n", "timeSeconds", "complexity"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({
                "algorithm": r["algorithm"],
                "language": r["language"],
                "n": r["n"],
                "timeSeconds": f"{float(r['timeSeconds']):.9f}",
                "complexity": r.get("complexity", ""),
            })


def plot_compare(rows: list[dict], out_png: Path) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        print(f"matplotlib no instalado — se omite el gráfico. ({e})")
        return

    sizes = sorted({int(r["n"]) for r in rows})
    order = [
        "Shaker Sort",
        "Dual-Pivot QuickSort",
        "Heap Sort",
        "Merge Sort",
        "Radix Sort",
    ]
    langs = ["Python", "Java"]

    fig, axes = plt.subplots(1, len(sizes), figsize=(21, 6), sharey=False)
    if len(sizes) == 1:
        axes = [axes]

    fig.suptitle(
        "Benchmark Algoritmos de Ordenamiento — Comparativo (Python vs Java)\n"
        "Tiempo de sort puro (sin I/O)",
        fontsize=13,
        fontweight="bold",
    )

    colors = {"Python": "#4C72B0", "Java": "#55A868"}

    for ax, n in zip(axes, sizes):
        subset = [r for r in rows if int(r["n"]) == n]
        table = {(r["algorithm"], r["language"]): float(r["timeSeconds"]) for r in subset}

        x = np.arange(len(order))
        w = 0.36

        for li, lang in enumerate(langs):
            vals = [table.get((alg, lang), 0.0) for alg in order]
            bars = ax.bar(x + (li - 0.5) * w, vals, w, label=lang, color=colors[lang], edgecolor="white", linewidth=0.6)

            for bar, v in zip(bars, vals):
                if v <= 0:
                    continue
                h = bar.get_height()
                cx = bar.get_x() + bar.get_width() / 2
                label = f"{v*1000:.2f} ms" if v < 1 else f"{v:.3f} s"
                ax.annotate(
                    label,
                    xy=(cx, h),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=7,
                )

        ax.set_title(f"n = {n:,}", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(order, rotation=28, ha="right", fontsize=8)
        ax.set_ylabel("Tiempo (s)")
        ax.legend()

    plt.tight_layout()
    plt.savefig(out_png, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"Gráfico guardado en: {out_png}")


def plot_single_language(rows: list[dict], language: str, out_png: Path) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        print(f"matplotlib no instalado — se omite el gráfico. ({e})")
        return

    sizes = sorted({int(r["n"]) for r in rows if r.get("language") == language})
    order = [
        "Shaker Sort",
        "Dual-Pivot QuickSort",
        "Heap Sort",
        "Merge Sort",
        "Radix Sort",
    ]

    fig, axes = plt.subplots(1, len(sizes), figsize=(21, 6), sharey=False)
    if len(sizes) == 1:
        axes = [axes]

    fig.suptitle(
        f"Benchmark Algoritmos de Ordenamiento — {language}\n"
        "Tiempo de sort puro (sin I/O)",
        fontsize=13,
        fontweight="bold",
    )

    color = {"Python": "#DD8452", "Java": "#55A868"}.get(language, "#999999")

    for ax, n in zip(axes, sizes):
        subset = [r for r in rows if r.get("language") == language and int(r["n"]) == n]
        table = {r["algorithm"]: float(r["timeSeconds"]) for r in subset}

        x = np.arange(len(order))
        vals = [table.get(alg, 0.0) for alg in order]
        bars = ax.bar(x, vals, 0.55, label=language, color=color, edgecolor="white", linewidth=0.6)

        for bar, v in zip(bars, vals):
            if v <= 0:
                continue
            h = bar.get_height()
            cx = bar.get_x() + bar.get_width() / 2
            label = f"{v*1000:.2f} ms" if v < 1 else f"{v:.3f} s"
            ax.annotate(
                label,
                xy=(cx, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7,
            )

        ax.set_title(f"n = {n:,}", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(order, rotation=28, ha="right", fontsize=8)
        ax.set_ylabel("Tiempo (s)")
        ax.legend()

    plt.tight_layout()
    plt.savefig(out_png, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"Gráfico guardado en: {out_png}")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    missing = [p for p in (PY_JSON, JAVA_JSON) if not p.exists()]
    if missing:
        print("Faltan archivos de resultados. Ejecuta primero los benchmarks:")
        for p in missing:
            print(f"  - No existe: {p}")
        return

    rows = _load_json(PY_JSON) + _load_json(JAVA_JSON)
    rows.sort(key=lambda r: (int(r["n"]), r["algorithm"], r["language"]))

    OUT_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_csv(OUT_CSV, rows)
    print(f"JSON combinado: {OUT_JSON}")
    print(f"CSV combinado:  {OUT_CSV}")

    plot_compare(rows, OUT_PNG)
    plot_single_language(rows, "Java", OUT_JAVA_PNG)


if __name__ == "__main__":
    main()

