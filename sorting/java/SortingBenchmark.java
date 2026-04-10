import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.Locale;
import java.util.Timer;
import java.util.TimerTask;
import java.util.List;

/**
 * Benchmark de ordenamiento — SOLO JAVA.
 *
 * Lee los datos desde tres archivos separados (10k, 100k, 1M).
 * Si los archivos no existen, el programa lo indica y termina.
 * Mide SOLO el tiempo de sort, sin I/O.
 * Shaker Sort NO tiene timeout — se espera hasta que termine,
 * imprimiendo progreso cada 10 segundos.
 *
 * Uso:
 *   java SortingBenchmark <ruta_directorio_data> <salida.json>
 *
 * Ejemplo:
 *   java -cp sorting/java SortingBenchmark data results/sorting_benchmark_java.json
 */
public class SortingBenchmark {

    // Archivos de datos (deben existir en el directorio indicado)
    private static final int[]    SIZES     = { 10_000, 100_000, 1_000_000 };
    private static final String[] FILENAMES = {
        "sorting_10000.txt",
        "sorting_100000.txt",
        "sorting_1000000.txt"
    };

    @FunctionalInterface
    private interface SortFn {
        void sort(int[] a);
    }

    private record AlgoCase(String name, String complexity, SortFn fn) {}
    private record ResultRow(String algorithm, String language, int n, double timeSeconds, String complexity) {}
    private record ResultRow2(String algorithm, String language, int n, double timeSeconds, String complexity, boolean timedOut) {}

    // ─────────────────────────────────────────────────────────────────────────
    public static void main(String[] args) throws IOException {
        if (args.length < 2) {
            System.err.println("Uso: java SortingBenchmark <dir_datos> <salida.json>");
            System.exit(1);
        }

        Path dataDir = Path.of(args[0]);
        Path outPath = Path.of(args[1]);
        outPath.getParent().toFile().mkdirs();

        // Forzar stdout sin buffer para ver progreso en tiempo real
        PrintStream out = new PrintStream(System.out, true, "UTF-8");

        out.println("============================================================");
        out.println("  BENCHMARK DE ORDENAMIENTO - JAVA");
        out.println("============================================================");

        AlgoCase[] cases = {
            new AlgoCase("Shaker Sort",          "O(n^2)",              a -> new ShakerSort().cocktailSort(a, 600_000L)),
            new AlgoCase("Dual-Pivot QuickSort", "O(n log n) promedio", DualPivotQuickSort::sort),
            new AlgoCase("Heap Sort",            "O(n log n)",          HeapSort::sort),
            new AlgoCase("Merge Sort",           "O(n log n)",          MergeSort::sort),
            new AlgoCase("Radix Sort",           "O(d * n), d=8",       RadixSort::sort),
        };

        StringBuilder json = new StringBuilder("[\n");
        boolean first = true;
        List<ResultRow2> rows = new ArrayList<>();

        for (int si = 0; si < SIZES.length; si++) {
            int n = SIZES[si];
            Path dataFile = dataDir.resolve(FILENAMES[si]);

            if (!Files.exists(dataFile)) {
                System.err.println("  [ERROR] No existe el archivo: " + dataFile);
                System.err.println("  Ejecuta primero: python scripts/generate_sorting_data.py");
                System.exit(1);
            }

            out.println("\n  -- n = " + String.format("%,d", n) + " --");
            out.print("    Cargando datos ...");
            out.flush();
            int[] full = loadInts(dataFile, n);
            out.println(" OK (" + full.length + " elementos)");

            for (AlgoCase c : cases) {
                final int[] copy = Arrays.copyOfRange(full, 0, n);
                out.println("    [" + c.name() + "] ejecutando ...");
                out.flush();

                // Timer que imprime cada 10 s mientras el algoritmo corre
                long[] startRef = { System.nanoTime() };
                Timer timer = new Timer(true);
                timer.scheduleAtFixedRate(new TimerTask() {
                    @Override public void run() {
                        long elapsed = (System.nanoTime() - startRef[0]) / 1_000_000_000L;
                        out.println("      [RUNNING] " + c.name() + " sigue corriendo... " + elapsed + "s transcurridos");
                        out.flush();
                    }
                }, 10_000L, 10_000L); // primer aviso a los 10s, luego cada 10s

                boolean timedOut = false;
                double secs = -1.0;
                startRef[0] = System.nanoTime();
                try {
                    c.fn().sort(copy);
                    secs = (System.nanoTime() - startRef[0]) / 1_000_000_000.0;
                } catch (ShakerSort.ShakerSortTimeout ex) {
                    timedOut = true;
                } finally {
                    timer.cancel();
                }

                String label;
                if (timedOut) {
                    out.println("    [" + c.name() + "] TIMEOUT (600s)");
                } else {
                    if (secs < 0.001)      label = String.format(Locale.US, "%.2f ms", secs * 1000);
                    else if (secs < 1.0)   label = String.format(Locale.US, "%.4f s",  secs);
                    else                   label = String.format(Locale.US, "%.3f s",   secs);
                    out.println("    [" + c.name() + "] OK " + label);
                }
                out.flush();

                if (!first) json.append(",\n");
                first = false;
                json.append("  {");
                json.append("\"algorithm\":\"").append(esc(c.name())).append("\",");
                json.append("\"language\":\"Java\",");
                json.append("\"n\":").append(n).append(",");
                json.append("\"timeSeconds\":").append(String.format(Locale.US, "%.9f", secs)).append(",");
                json.append("\"complexity\":\"").append(esc(c.complexity())).append("\"");
                json.append(",\"timedOut\":").append(timedOut);
                json.append("}");

                rows.add(new ResultRow2(c.name(), "Java", n, secs, c.complexity(), timedOut));
            }
        }

        json.append("\n]\n");
        Files.writeString(outPath, json.toString(), StandardCharsets.UTF_8);

        Path csvPath = toCsvPath(outPath);
        writeCsv(csvPath, rows);

        out.println("\n  Resultados guardados en:");
        out.println("    JSON: " + outPath);
        out.println("    CSV:  " + csvPath);
        out.println("\n============================================================");
        out.println("  BENCHMARK JAVA COMPLETADO");
        out.println("============================================================");
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    private static String esc(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private static String csvEsc(String s) {
        if (s == null) return "";
        boolean needsQuotes = s.contains(",") || s.contains("\"") || s.contains("\n") || s.contains("\r");
        String v = s.replace("\"", "\"\"");
        return needsQuotes ? ("\"" + v + "\"") : v;
    }

    private static Path toCsvPath(Path jsonPath) {
        String name = jsonPath.getFileName().toString();
        String base = name.endsWith(".json") ? name.substring(0, name.length() - 5) : name;
        return jsonPath.resolveSibling(base + ".csv");
    }

    private static void writeCsv(Path path, List<ResultRow2> rows) throws IOException {
        StringBuilder sb = new StringBuilder();
        sb.append("algorithm,language,n,timeSeconds,complexity,timedOut\n");
        for (ResultRow2 r : rows) {
            sb.append(csvEsc(r.algorithm())).append(",");
            sb.append(csvEsc(r.language())).append(",");
            sb.append(r.n()).append(",");
            sb.append(String.format(Locale.US, "%.9f", r.timeSeconds())).append(",");
            sb.append(csvEsc(r.complexity())).append(",");
            sb.append(r.timedOut());
            sb.append("\n");
        }
        Files.writeString(path, sb.toString(), StandardCharsets.UTF_8);
    }

    /** Lee hasta maxCount enteros desde archivo de texto plano. */
    private static int[] loadInts(Path path, int maxCount) throws IOException {
        int[] buf = new int[maxCount];
        int idx = 0;
        try (BufferedReader br = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            String line;
            while ((line = br.readLine()) != null && idx < maxCount) {
                line = line.trim();
                if (!line.isEmpty()) {
                    buf[idx++] = Integer.parseInt(line);
                }
            }
        }
        return idx == maxCount ? buf : Arrays.copyOf(buf, idx);
    }
}
