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
from __future__ import annotations  # Permite usar anotaciones de tipo modernas en versiones anteriores de Python

import csv        # Para escribir el archivo CSV combinado con todos los resultados
import json       # Para leer los JSON de cada lenguaje y escribir el JSON combinado
from pathlib import Path  # Para manejar rutas de archivos de forma multiplataforma

ROOT = Path(__file__).resolve().parents[1]  # Sube 1 nivel desde el script para llegar a la raíz del proyecto
RESULTS_DIR = ROOT / "results"              # Carpeta donde están los resultados y donde se guardarán las salidas

PY_JSON   = RESULTS_DIR / "sorting_benchmark_python.json"  # Ruta al JSON de resultados del benchmark Python
JAVA_JSON = RESULTS_DIR / "sorting_benchmark_java.json"    # Ruta al JSON de resultados del benchmark Java

OUT_JSON     = RESULTS_DIR / "sorting_benchmark_all.json"     # Ruta de salida para el JSON combinado de ambos lenguajes
OUT_CSV      = RESULTS_DIR / "sorting_benchmark_all.csv"      # Ruta de salida para el CSV combinado de ambos lenguajes
OUT_PNG      = RESULTS_DIR / "sorting_benchmark_compare.png"  # Ruta de salida para el gráfico comparativo Python vs Java
OUT_JAVA_PNG = RESULTS_DIR / "sorting_benchmark_java.png"     # Ruta de salida para el gráfico exclusivo de Java


def _load_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:  # Abre el archivo JSON en modo lectura con codificación UTF-8
        return json.load(f)                       # Deserializa el contenido JSON y lo retorna como lista de diccionarios


def _write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = ["algorithm", "language", "n", "timeSeconds", "complexity"]  # Define el orden de las columnas del CSV
    with path.open("w", newline="", encoding="utf-8") as f:  # Abre el archivo CSV para escritura en UTF-8
        w = csv.DictWriter(f, fieldnames=fieldnames)          # Crea un escritor de CSV basado en diccionarios
        w.writeheader()                                        # Escribe la fila de encabezados con los nombres de columna
        for r in rows:                                         # Itera sobre cada fila de resultado combinado
            w.writerow({                                       # Escribe una fila con los datos formateados
                "algorithm":   r["algorithm"],                 # Nombre del algoritmo de ordenamiento
                "language":    r["language"],                  # Lenguaje de programación usado
                "n":           r["n"],                         # Tamaño del arreglo ordenado
                "timeSeconds": f"{float(r['timeSeconds']):.9f}", # Tiempo convertido a float y formateado con 9 decimales
                "complexity":  r.get("complexity", ""),        # Complejidad teórica (cadena vacía si no existe la clave)
            })


def plot_compare(rows: list[dict], out_png: Path) -> None:
    try:
        import matplotlib.pyplot as plt  # Importa matplotlib para graficar (dentro del try por si no está instalado)
        import numpy as np               # Importa numpy para manejar posiciones numéricas de las barras
    except ImportError as e:
        print(f"matplotlib no instalado — se omite el gráfico. ({e})")  # Avisa si las librerías no están disponibles
        return                                                            # Sale sin graficar

    sizes = sorted({int(r["n"]) for r in rows})  # Obtiene los tamaños únicos presentes en los datos, ordenados
    order = [                                     # Orden fijo de algoritmos en el eje X (mismo que en los benchmarks)
        "Shaker Sort",
        "Dual-Pivot QuickSort",
        "Heap Sort",
        "Merge Sort",
        "Radix Sort",
    ]
    langs = ["Python", "Java"]  # Lenguajes a comparar lado a lado en cada grupo de barras

    fig, axes = plt.subplots(1, len(sizes), figsize=(21, 6), sharey=False)  # Crea un subgráfico por cada tamaño
    if len(sizes) == 1:
        axes = [axes]  # Si solo hay un tamaño, envuelve el eje en lista para que el for funcione igual

    fig.suptitle(                # Agrega un título general a toda la figura
        "Benchmark Algoritmos de Ordenamiento — Comparativo (Python vs Java)\n"
        "Tiempo de sort puro (sin I/O)",
        fontsize=13,
        fontweight="bold",
    )

    colors = {"Python": "#4C72B0", "Java": "#55A868"}  # Colores diferenciados: azul para Python, verde para Java

    for ax, n in zip(axes, sizes):  # Itera sobre cada subgráfico y su tamaño correspondiente
        subset = [r for r in rows if int(r["n"]) == n]  # Filtra las filas que corresponden al tamaño actual
        table = {(r["algorithm"], r["language"]): float(r["timeSeconds"]) for r in subset}
        # Construye un diccionario indexado por (algoritmo, lenguaje) para acceso rápido a los tiempos

        x = np.arange(len(order))  # Crea posiciones numéricas en el eje X para cada algoritmo
        w = 0.36                   # Ancho de cada barra (dos barras por algoritmo: Python y Java)

        for li, lang in enumerate(langs):  # Itera sobre cada lenguaje para dibujar su grupo de barras
            vals = [table.get((alg, lang), 0.0) for alg in order]  # Obtiene el tiempo de cada algoritmo para este lenguaje (0 si no existe)
            bars = ax.bar(x + (li - 0.5) * w, vals, w, label=lang, color=colors[lang], edgecolor="white", linewidth=0.6)
            # Desplaza las barras de cada lenguaje ±0.18 del centro para que queden lado a lado sin solaparse

            for bar, v in zip(bars, vals):  # Itera sobre cada barra para agregar etiqueta de tiempo encima
                if v <= 0:                  # Si el valor es 0 o negativo (timeout o no ejecutado)...
                    continue                # ...no agrega etiqueta sobre esa barra
                h  = bar.get_height()       # Obtiene la altura de la barra (igual al valor de tiempo)
                cx = bar.get_x() + bar.get_width() / 2  # Calcula el centro horizontal de la barra
                label = f"{v*1000:.2f} ms" if v < 1 else f"{v:.3f} s"  # Formatea: ms si < 1s, segundos si ≥ 1s
                ax.annotate(
                    label,
                    xy=(cx, h),                          # Punto de anclaje en el tope de la barra
                    xytext=(0, 3),                       # Desplaza el texto 3 puntos hacia arriba
                    textcoords="offset points",          # Interpreta xytext como desplazamiento en puntos
                    ha="center",                         # Centra el texto horizontalmente sobre la barra
                    va="bottom",                         # Alinea el texto desde su borde inferior
                    fontsize=7,                          # Tamaño de fuente pequeño para no solapar barras cercanas
                )

        ax.set_title(f"n = {n:,}", fontsize=11, fontweight="bold")       # Título del subgráfico con el tamaño formateado
        ax.set_xticks(x)                                                  # Ubica las marcas del eje X en las posiciones de los algoritmos
        ax.set_xticklabels(order, rotation=28, ha="right", fontsize=8)   # Etiqueta el eje X con los nombres rotados 28°
        ax.set_ylabel("Tiempo (s)")                                       # Etiqueta el eje Y como "Tiempo (s)"
        ax.legend()                                                        # Muestra la leyenda con los colores de cada lenguaje

    plt.tight_layout()                                   # Ajusta automáticamente los márgenes para evitar solapamientos
    plt.savefig(out_png, dpi=160, bbox_inches="tight")  # Guarda el gráfico como PNG con 160 DPI y sin recortes
    plt.close()                                          # Cierra la figura para liberar memoria
    print(f"Gráfico guardado en: {out_png}")             # Informa en consola dónde se guardó el gráfico


def plot_single_language(rows: list[dict], language: str, out_png: Path) -> None:
    try:
        import matplotlib.pyplot as plt  # Importa matplotlib para graficar (dentro del try por si no está instalado)
        import numpy as np               # Importa numpy para manejar posiciones numéricas de las barras
    except ImportError as e:
        print(f"matplotlib no instalado — se omite el gráfico. ({e})")  # Avisa si las librerías no están disponibles
        return                                                            # Sale sin graficar

    sizes = sorted({int(r["n"]) for r in rows if r.get("language") == language})
    # Obtiene los tamaños únicos presentes solo para el lenguaje indicado, ordenados
    order = [                     # Orden fijo de algoritmos en el eje X (mismo que en los benchmarks)
        "Shaker Sort",
        "Dual-Pivot QuickSort",
        "Heap Sort",
        "Merge Sort",
        "Radix Sort",
    ]

    fig, axes = plt.subplots(1, len(sizes), figsize=(21, 6), sharey=False)  # Crea un subgráfico por cada tamaño
    if len(sizes) == 1:
        axes = [axes]  # Si solo hay un tamaño, envuelve el eje en lista para que el for funcione igual

    fig.suptitle(                 # Agrega un título general a toda la figura con el nombre del lenguaje
        f"Benchmark Algoritmos de Ordenamiento — {language}\n"
        "Tiempo de sort puro (sin I/O)",
        fontsize=13,
        fontweight="bold",
    )

    color = {"Python": "#DD8452", "Java": "#55A868"}.get(language, "#999999")
    # Selecciona el color del lenguaje: naranja para Python, verde para Java, gris por defecto si es otro

    for ax, n in zip(axes, sizes):  # Itera sobre cada subgráfico y su tamaño correspondiente
        subset = [r for r in rows if r.get("language") == language and int(r["n"]) == n]
        # Filtra las filas que corresponden al lenguaje indicado y al tamaño actual
        table = {r["algorithm"]: float(r["timeSeconds"]) for r in subset}
        # Construye un diccionario indexado por nombre de algoritmo para acceso rápido a los tiempos

        x    = np.arange(len(order))              # Crea posiciones numéricas en el eje X para cada algoritmo
        vals = [table.get(alg, 0.0) for alg in order]  # Obtiene el tiempo de cada algoritmo (0 si no existe)
        bars = ax.bar(x, vals, 0.55, label=language, color=color, edgecolor="white", linewidth=0.6)
        # Dibuja las barras con ancho 0.55, usando el color del lenguaje y borde blanco fino

        for bar, v in zip(bars, vals):  # Itera sobre cada barra para agregar etiqueta de tiempo encima
            if v <= 0:                  # Si el valor es 0 o negativo (timeout o no ejecutado)...
                continue                # ...no agrega etiqueta sobre esa barra
            h  = bar.get_height()       # Obtiene la altura de la barra (igual al valor de tiempo)
            cx = bar.get_x() + bar.get_width() / 2  # Calcula el centro horizontal de la barra
            label = f"{v*1000:.2f} ms" if v < 1 else f"{v:.3f} s"  # Formatea: ms si < 1s, segundos si ≥ 1s
            ax.annotate(
                label,
                xy=(cx, h),                          # Punto de anclaje en el tope de la barra
                xytext=(0, 3),                       # Desplaza el texto 3 puntos hacia arriba
                textcoords="offset points",          # Interpreta xytext como desplazamiento en puntos
                ha="center",                         # Centra el texto horizontalmente sobre la barra
                va="bottom",                         # Alinea el texto desde su borde inferior
                fontsize=7,                          # Tamaño de fuente pequeño para no solapar barras cercanas
            )

        ax.set_title(f"n = {n:,}", fontsize=11, fontweight="bold")       # Título del subgráfico con el tamaño formateado
        ax.set_xticks(x)                                                  # Ubica las marcas del eje X en las posiciones de los algoritmos
        ax.set_xticklabels(order, rotation=28, ha="right", fontsize=8)   # Etiqueta el eje X con los nombres rotados 28°
        ax.set_ylabel("Tiempo (s)")                                       # Etiqueta el eje Y como "Tiempo (s)"
        ax.legend()                                                        # Muestra la leyenda con el nombre del lenguaje

    plt.tight_layout()                                   # Ajusta automáticamente los márgenes para evitar solapamientos
    plt.savefig(out_png, dpi=160, bbox_inches="tight")  # Guarda el gráfico como PNG con 160 DPI y sin recortes
    plt.close()                                          # Cierra la figura para liberar memoria
    print(f"Gráfico guardado en: {out_png}")             # Informa en consola dónde se guardó el gráfico


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)  # Crea la carpeta de resultados si no existe (y sus padres también)

    missing = [p for p in (PY_JSON, JAVA_JSON) if not p.exists()]  # Lista los archivos JSON que no existen
    if missing:                          # Si falta alguno de los dos archivos requeridos...
        print("Faltan archivos de resultados. Ejecuta primero los benchmarks:")  # Avisa al usuario
        for p in missing:
            print(f"  - No existe: {p}") # Muestra la ruta exacta de cada archivo faltante
        return                           # Sale sin generar gráficos ni archivos combinados

    rows = _load_json(PY_JSON) + _load_json(JAVA_JSON)  # Carga y concatena los resultados de Python y Java en una sola lista
    rows.sort(key=lambda r: (int(r["n"]), r["algorithm"], r["language"]))
    # Ordena los resultados por tamaño n, luego por nombre de algoritmo y finalmente por lenguaje

    OUT_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    # Serializa la lista combinada como JSON indentado y lo escribe directamente en el archivo de salida
    _write_csv(OUT_CSV, rows)             # Escribe todos los resultados combinados en formato CSV
    print(f"JSON combinado: {OUT_JSON}")  # Informa la ruta del JSON combinado generado
    print(f"CSV combinado:  {OUT_CSV}")   # Informa la ruta del CSV combinado generado

    plot_compare(rows, OUT_PNG)                   # Genera el gráfico comparativo Python vs Java y lo guarda
    plot_single_language(rows, "Java", OUT_JAVA_PNG)  # Genera el gráfico exclusivo de Java y lo guarda


if __name__ == "__main__":  # Solo ejecuta main() si este script es el punto de entrada (no si es importado)
    main()                  # Llama a la función principal que combina resultados y genera todos los gráficos