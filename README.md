## Taller de algoritmos — Benchmark de ordenamiento (Python + Java)

### Qué incluye

- **Algoritmos**: Shaker Sort, Dual-Pivot QuickSort, Heap Sort, Merge Sort, Radix Sort
- **Tamaños**: 10,000 / 100,000 / 1,000,000
- **Datos**: números aleatorios de **8 dígitos** (10,000,000 a 99,999,999), se generan **una sola vez** y se reutilizan
- **Benchmark**: mide **solo el tiempo del sort** (sin lectura/escritura de archivos)
- **Resultados**: JSON/CSV en `results/`
- **Gráfico**: barras comparativas **Python vs Java** (dos barras por algoritmo)

### Estructura

- `scripts/generate_sorting_data.py`: genera `data/sorting_10000.txt`, `data/sorting_100000.txt`, `data/sorting_1000000.txt` (si ya existen, no regenera)
- `sorting/python/benchmark_sorting.py`: corre **solo Python** y exporta `results/sorting_benchmark_python.(json|csv|png)`
- `sorting/java/SortingBenchmark.java`: corre **solo Java** y exporta `results/sorting_benchmark_java.json`
- `scripts/plot_sorting_results.py`: **no corre benchmarks**, solo lee resultados y genera:
  - `results/sorting_benchmark_all.(json|csv)`
  - `results/sorting_benchmark_compare.png`

### Requisitos

- **Python 3.10+**
- **Java 17+** (o similar)
- (Opcional para gráficos) `matplotlib`

### Cómo ejecutar

Generar datos (una sola vez):

```bash
python scripts/generate_sorting_data.py
```

Benchmark Python (solo Python):

```bash
python sorting/python/benchmark_sorting.py
```

Benchmark Java (solo Java):

```bash
javac sorting/java/*.java
java -cp sorting/java SortingBenchmark data results/sorting_benchmark_java.json
```

Gráfico comparativo Python vs Java:

```bash
python scripts/plot_sorting_results.py
```

### Notas importantes

- **Shaker Sort es \(O(n^2)\)**: con 100,000 y especialmente 1,000,000 puede tardar muchísimo.  
  En ambos benchmarks se imprime en consola cada cierto tiempo cuánto lleva ejecutándose.

