import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;

/**
 * Benchmark de algoritmos de busqueda - SOLO JAVA (Punto 2).
 *
 * - Lee datos desde data_searching/ (arreglos ordenados + queries).
 * - Mide UNICAMENTE el tiempo de busqueda (sin I/O).
 * - Exporta JSON + CSV.
 *
 * Uso:
 *   java -cp searching/java SearchingRunner <dir_datos> <salida.json>
 *
 * Ejemplo:
 *   javac searching/java/*.java
 *   java -cp searching/java SearchingRunner data_searching results_searching/searching_benchmark_java.json
 */
public class SearchingRunner {

    private static final int[] SIZES = { 10_000, 100_000, 1_000_000 };
    private static final String[] ARR_FILES = {
        "searching_10000.txt",
        "searching_100000.txt",
        "searching_1000000.txt"
    };
    private static final String[] Q_FILES = {
        "queries_10000.txt",
        "queries_100000.txt",
        "queries_1000000.txt"
    };

    @FunctionalInterface
    private interface SearchFn {
        int search(int[] a, int x);
    }

    private record AlgoCase(String name, String complexity, SearchFn fn) {}
    private record ResultRow(String algorithm, String language, int n, double timeSeconds, String complexity) {}

    public static void main(String[] args) throws IOException {
        if (args.length < 2) {
            System.err.println("Uso: java SearchingRunner <dir_datos> <salida.json>");
            System.exit(1);
        }

        Path dataDir = Path.of(args[0]);
        Path outPath = Path.of(args[1]);
        if (outPath.getParent() != null) outPath.getParent().toFile().mkdirs();

        PrintStream out = new PrintStream(System.out, true, "UTF-8");

        out.println("============================================================");
        out.println("  BENCHMARK DE BUSQUEDA - JAVA");
        out.println("============================================================");

        AlgoCase[] cases = {
            new AlgoCase("Binary Search",  "O(log n)",   BinarySearch::search),
            new AlgoCase("Ternary Search", "O(log n)",   TernarySearch::search),
            new AlgoCase("Jump Search",    "O(sqrt(n))", JumpSearch::search),
        };

        List<ResultRow> rows = new ArrayList<>();
        StringBuilder json = new StringBuilder("[\n");
        boolean first = true;

        for (int si = 0; si < SIZES.length; si++) {
            int n = SIZES[si];
            Path arrPath = dataDir.resolve(ARR_FILES[si]);
            Path qPath = dataDir.resolve(Q_FILES[si]);

            if (!Files.exists(arrPath) || !Files.exists(qPath)) {
                System.err.println("  [ERROR] Faltan archivos de datos en: " + dataDir);
                System.err.println("  Necesarios: " + arrPath + " y " + qPath);
                System.err.println("  Ejecuta primero: python scripts/generate_searching_data.py");
                System.exit(1);
            }

            out.println("\n  -- n = " + String.format("%,d", n) + " --");
            out.print("    Cargando arreglo ...");
            out.flush();
            int[] arr = loadInts(arrPath, n);
            out.println(" OK (" + arr.length + " elementos)");

            out.print("    Cargando queries ...");
            out.flush();
            int[] queries = loadInts(qPath, Integer.MAX_VALUE);
            out.println(" OK (" + queries.length + " consultas)");

            for (AlgoCase c : cases) {
                out.println("    [" + c.name() + "] ejecutando ...");
                out.flush();

                long checksum = 0;
                long t0 = System.nanoTime();
                for (int q : queries) {
                    checksum += c.fn().search(arr, q);
                }
                double secs = (System.nanoTime() - t0) / 1_000_000_000.0;

                String label = secs < 1.0 ? String.format(Locale.US, "%.2f ms", secs * 1000) : String.format(Locale.US, "%.3f s", secs);
                out.println("    [" + c.name() + "] OK " + label + " (checksum=" + checksum + ")");
                out.flush();

                rows.add(new ResultRow(c.name(), "Java", n, secs, c.complexity()));

                if (!first) json.append(",\n");
                first = false;
                json.append("  {");
                json.append("\"algorithm\":\"").append(esc(c.name())).append("\",");
                json.append("\"language\":\"Java\",");
                json.append("\"n\":").append(n).append(",");
                json.append("\"timeSeconds\":").append(String.format(Locale.US, "%.9f", secs)).append(",");
                json.append("\"complexity\":\"").append(esc(c.complexity())).append("\"");
                json.append("}");
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

    private static void writeCsv(Path path, List<ResultRow> rows) throws IOException {
        StringBuilder sb = new StringBuilder();
        sb.append("algorithm,language,n,timeSeconds,complexity\n");
        for (ResultRow r : rows) {
            sb.append(csvEsc(r.algorithm())).append(",");
            sb.append(csvEsc(r.language())).append(",");
            sb.append(r.n()).append(",");
            sb.append(String.format(Locale.US, "%.9f", r.timeSeconds())).append(",");
            sb.append(csvEsc(r.complexity()));
            sb.append("\n");
        }
        Files.writeString(path, sb.toString(), StandardCharsets.UTF_8);
    }

    private static int[] loadInts(Path path, int maxCount) throws IOException {
        int cap = maxCount == Integer.MAX_VALUE ? 1_000_000 : maxCount;
        int[] buf = new int[Math.min(cap, 1_000_000)];
        int idx = 0;
        try (BufferedReader br = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;
                if (idx == buf.length) {
                    buf = Arrays.copyOf(buf, buf.length * 2);
                }
                buf[idx++] = Integer.parseInt(line);
                if (idx >= maxCount) break;
            }
        }
        return Arrays.copyOf(buf, idx);
    }
}

