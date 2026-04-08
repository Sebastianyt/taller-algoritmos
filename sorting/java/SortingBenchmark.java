import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Mide solo el tiempo de ordenamiento (sin I/O). Lee hasta 1M enteros desde texto plano.
 * Uso: java SortingBenchmark <ruta_datos.txt> <salida.json>
 */
public class SortingBenchmark {

    private static final int[] SIZES = { 10_000, 100_000, 1_000_000 };

    private static final class AlgoCase {
        final String name;
        final String complexity;
        final SortFn fn;

        AlgoCase(String name, String complexity, SortFn fn) {
            this.name = name;
            this.complexity = complexity;
            this.fn = fn;
        }
    }

    @FunctionalInterface
    private interface SortFn {
        void sort(int[] a);
    }

    public static void main(String[] args) throws IOException {
        if (args.length < 2) {
            System.err.println("Uso: java SortingBenchmark <datos.txt> <salida.json>");
            System.exit(1);
        }
        Path dataPath = Path.of(args[0]);
        Path outPath = Path.of(args[1]);

        int[] full = loadAllInts(dataPath);
        if (full.length < 1_000_000) {
            System.err.println("Se esperan al menos 1_000_000 enteros en el archivo.");
            System.exit(1);
        }

        AlgoCase[] cases = new AlgoCase[] {
            new AlgoCase("Shaker Sort", "O(n^2)", a -> new ShakerSort().cocktailSort(a)),
            new AlgoCase("Dual-Pivot QuickSort", "O(n log n) promedio", DualPivotQuickSort::sort),
            new AlgoCase("Heap Sort", "O(n log n)", HeapSort::sort),
            new AlgoCase("Merge Sort", "O(n log n)", MergeSort::sort),
            new AlgoCase("Radix Sort", "O(d * n), d=8", RadixSort::sort),
        };

        StringBuilder json = new StringBuilder();
        json.append("[\n");
        boolean first = true;
        for (int n : SIZES) {
            for (AlgoCase c : cases) {
                int[] copy = java.util.Arrays.copyOfRange(full, 0, n);
                long t0 = System.nanoTime();
                c.fn.sort(copy);
                double secs = (System.nanoTime() - t0) / 1_000_000_000.0;
                if (!first) {
                    json.append(",\n");
                }
                first = false;
                json.append("  {");
                json.append("\"algorithm\":\"").append(escapeJson(c.name)).append("\",");
                json.append("\"language\":\"Java\",");
                json.append("\"n\":").append(n).append(",");
                json.append("\"timeSeconds\":").append(String.format(Locale.US, "%.9f", secs)).append(",");
                json.append("\"complexity\":\"").append(escapeJson(c.complexity)).append("\"");
                json.append("}");
            }
        }
        json.append("\n]\n");
        Files.writeString(outPath, json.toString(), StandardCharsets.UTF_8);
    }

    private static String escapeJson(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private static int[] loadAllInts(Path path) throws IOException {
        List<Integer> tmp = new ArrayList<>(1_000_000);
        try (BufferedReader br = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) {
                    continue;
                }
                tmp.add(Integer.parseInt(line));
            }
        }
        int[] out = new int[tmp.size()];
        for (int i = 0; i < tmp.size(); i++) {
            out[i] = tmp.get(i);
        }
        return out;
    }
}
