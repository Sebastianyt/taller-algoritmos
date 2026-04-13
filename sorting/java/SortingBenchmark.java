import java.io.BufferedReader;        // Para leer archivos de texto línea por línea de forma eficiente
import java.io.IOException;           // Para manejar excepciones de entrada/salida
import java.io.PrintStream;           // Para imprimir en consola con control de buffer
import java.nio.charset.StandardCharsets; // Para especificar codificaciones de texto estándar (UTF-8, ASCII)
import java.nio.file.Files;           // Para operaciones modernas sobre archivos (leer, escribir, verificar existencia)
import java.nio.file.Path;            // Para representar rutas de archivos de forma multiplataforma
import java.util.Arrays;              // Para operaciones sobre arreglos (copiar, etc.)
import java.util.ArrayList;           // Para usar listas dinámicas de resultados
import java.util.Locale;              // Para formatear números con punto decimal en lugar de coma
import java.util.Timer;               // Para ejecutar tareas periódicas (reporte de progreso)
import java.util.TimerTask;           // Para definir la tarea que ejecuta el Timer
import java.util.List;                // Interfaz base para listas en Java

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

    // Tamaños de arreglos a evaluar en el benchmark
    private static final int[]    SIZES     = { 10_000, 100_000, 1_000_000 };
    // Nombres de los archivos de datos correspondientes a cada tamaño
    private static final String[] FILENAMES = {
        "sorting_10000.txt",
        "sorting_100000.txt",
        "sorting_1000000.txt"
    };

    @FunctionalInterface               // Marca que esta interfaz tiene exactamente un método abstracto (permite lambdas)
    private interface SortFn {
        void sort(int[] a);            // Contrato que deben cumplir todas las funciones de ordenamiento: recibe un arreglo y lo ordena in-place
    }

    private record AlgoCase(String name, String complexity, SortFn fn) {}
    // Record inmutable que agrupa el nombre del algoritmo, su complejidad teórica y la función que lo ejecuta

    private record ResultRow(String algorithm, String language, int n, double timeSeconds, String complexity) {}
    // Record que representa una fila de resultado sin información de timeout (versión sin timedOut)

    private record ResultRow2(String algorithm, String language, int n, double timeSeconds, String complexity, boolean timedOut) {}
    // Record extendido que representa una fila de resultado incluyendo si hubo timeout

    // ─────────────────────────────────────────────────────────────────────────
    public static void main(String[] args) throws IOException {
        if (args.length < 2) {                                                    // Verifica que se pasaron al menos 2 argumentos por línea de comandos
            System.err.println("Uso: java SortingBenchmark <dir_datos> <salida.json>"); // Muestra el uso correcto si faltan argumentos
            System.exit(1);                                                       // Termina el programa con código de error 1
        }

        Path dataDir = Path.of(args[0]);              // Convierte el primer argumento en la ruta del directorio de datos
        Path outPath = Path.of(args[1]);              // Convierte el segundo argumento en la ruta del archivo JSON de salida
        outPath.getParent().toFile().mkdirs();         // Crea los directorios padres del archivo de salida si no existen

        // Forzar stdout sin buffer para ver progreso en tiempo real
        PrintStream out = new PrintStream(System.out, true, "UTF-8"); // Crea un PrintStream con autoflush activado y codificación UTF-8

        out.println("============================================================"); // Línea decorativa de separación
        out.println("  BENCHMARK DE ORDENAMIENTO - JAVA");                           // Título del benchmark
        out.println("============================================================"); // Línea decorativa de separación

        AlgoCase[] cases = {
            new AlgoCase("Shaker Sort",          "O(n^2)",              a -> new ShakerSort().cocktailSort(a, 600_000L)),
            // Shaker Sort con timeout de 600.000 ms (10 minutos), instancia nueva de ShakerSort por ejecución
            new AlgoCase("Dual-Pivot QuickSort", "O(n log n) promedio", DualPivotQuickSort::sort),
            // QuickSort con doble pivote usando referencia al método estático sort
            new AlgoCase("Heap Sort",            "O(n log n)",          HeapSort::sort),
            // Heap Sort usando referencia al método estático sort
            new AlgoCase("Merge Sort",           "O(n log n)",          MergeSort::sort),
            // Merge Sort usando referencia al método estático sort
            new AlgoCase("Radix Sort",           "O(d * n), d=8",       RadixSort::sort),
            // Radix Sort con 8 dígitos de base usando referencia al método estático sort
        };

        StringBuilder json = new StringBuilder("[\n"); // Inicia la construcción del JSON como array abierto
        boolean first = true;                           // Bandera para controlar si es el primer elemento (para omitir la coma inicial)
        List<ResultRow2> rows = new ArrayList<>();      // Lista que acumulará todas las filas de resultados

        for (int si = 0; si < SIZES.length; si++) {    // Itera sobre cada tamaño de arreglo definido
            int n = SIZES[si];                          // Obtiene el tamaño actual
            Path dataFile = dataDir.resolve(FILENAMES[si]); // Construye la ruta completa al archivo de datos del tamaño actual

            if (!Files.exists(dataFile)) {              // Verifica si el archivo de datos existe
                System.err.println("  [ERROR] No existe el archivo: " + dataFile);          // Informa el error con la ruta exacta
                System.err.println("  Ejecuta primero: python scripts/generate_sorting_data.py"); // Indica cómo generar los datos
                System.exit(1);                         // Termina el programa con error si falta el archivo
            }

            out.println("\n  -- n = " + String.format("%,d", n) + " --"); // Imprime el separador visual con el tamaño formateado con comas
            out.print("    Cargando datos ...");         // Indica que está comenzando la carga de datos
            out.flush();                                 // Fuerza el vaciado del buffer para que aparezca inmediatamente en consola
            int[] full = loadInts(dataFile, n);         // Carga hasta n enteros desde el archivo
            out.println(" OK (" + full.length + " elementos)"); // Confirma la carga exitosa con la cantidad real de elementos

            for (AlgoCase c : cases) {                   // Itera sobre cada algoritmo definido
                final int[] copy = Arrays.copyOfRange(full, 0, n); // Crea una copia independiente del arreglo para no alterar el original
                out.println("    [" + c.name() + "] ejecutando ..."); // Informa que el algoritmo está por comenzar
                out.flush();                             // Vacía el buffer para mostrar el mensaje de inmediato

                // Timer que imprime cada 10 s mientras el algoritmo corre
                long[] startRef = { System.nanoTime() }; // Arreglo de un elemento para guardar el tiempo de inicio (permite acceso desde clase anónima)
                Timer timer = new Timer(true);            // Crea un Timer daemon (se cierra solo cuando termina el programa principal)
                timer.scheduleAtFixedRate(new TimerTask() { // Programa una tarea que se repite periódicamente
                    @Override public void run() {
                        long elapsed = (System.nanoTime() - startRef[0]) / 1_000_000_000L; // Calcula los segundos transcurridos desde el inicio del sort
                        out.println("      [RUNNING] " + c.name() + " sigue corriendo... " + elapsed + "s transcurridos"); // Imprime el progreso
                        out.flush();                      // Vacía el buffer para mostrar el mensaje de inmediato
                    }
                }, 10_000L, 10_000L); // Primer aviso a los 10s de inicio, luego cada 10s adicionales

                boolean timedOut = false;                 // Bandera para marcar si el algoritmo superó el tiempo límite
                double secs = -1.0;                       // Tiempo de ejecución inicial en -1 (indica "no ejecutado exitosamente")
                startRef[0] = System.nanoTime();          // Registra el tiempo exacto de inicio del sort
                try {
                    c.fn().sort(copy);                    // Ejecuta la función de ordenamiento sobre la copia del arreglo
                    secs = (System.nanoTime() - startRef[0]) / 1_000_000_000.0; // Calcula el tiempo de sort en segundos
                } catch (ShakerSort.ShakerSortTimeout ex) { // Captura la excepción específica de timeout del Shaker Sort
                    timedOut = true;                      // Marca que el algoritmo no terminó a tiempo
                } finally {
                    timer.cancel();                       // Cancela el timer de progreso sin importar si hubo error o no
                }

                String label;                             // Variable para almacenar la etiqueta de tiempo formateada
                if (timedOut) {
                    out.println("    [" + c.name() + "] TIMEOUT (600s)"); // Informa del timeout en consola
                } else {
                    if (secs < 0.001)      label = String.format(Locale.US, "%.2f ms", secs * 1000); // Menos de 1ms: muestra en milisegundos con 2 decimales
                    else if (secs < 1.0)   label = String.format(Locale.US, "%.4f s",  secs);        // Entre 1ms y 1s: muestra en segundos con 4 decimales
                    else                   label = String.format(Locale.US, "%.3f s",   secs);        // Más de 1s: muestra en segundos con 3 decimales
                    out.println("    [" + c.name() + "] OK " + label); // Imprime el resultado exitoso con el tiempo formateado
                }
                out.flush(); // Vacía el buffer para que el resultado aparezca en consola inmediatamente

                if (!first) json.append(",\n"); // Si no es el primer elemento, agrega una coma separadora antes del nuevo objeto JSON
                first = false;                  // Marca que ya no es el primer elemento
                json.append("  {");             // Abre el objeto JSON para este resultado
                json.append("\"algorithm\":\"").append(esc(c.name())).append("\",");              // Agrega el nombre del algoritmo escapado
                json.append("\"language\":\"Java\",");                                             // Agrega el lenguaje fijo como "Java"
                json.append("\"n\":").append(n).append(",");                                       // Agrega el tamaño del arreglo
                json.append("\"timeSeconds\":").append(String.format(Locale.US, "%.9f", secs)).append(","); // Agrega el tiempo con 9 decimales
                json.append("\"complexity\":\"").append(esc(c.complexity())).append("\"");         // Agrega la complejidad teórica escapada
                json.append(",\"timedOut\":").append(timedOut);                                    // Agrega si hubo timeout como booleano
                json.append("}");               // Cierra el objeto JSON

                rows.add(new ResultRow2(c.name(), "Java", n, secs, c.complexity(), timedOut)); // Agrega la fila de resultado a la lista para el CSV
            }
        }

        json.append("\n]\n");                           // Cierra el array JSON y agrega salto de línea final
        Files.writeString(outPath, json.toString(), StandardCharsets.UTF_8); // Escribe el JSON completo en el archivo de salida en UTF-8

        Path csvPath = toCsvPath(outPath);              // Genera la ruta del CSV reemplazando la extensión .json por .csv
        writeCsv(csvPath, rows);                        // Escribe todos los resultados en formato CSV

        out.println("\n  Resultados guardados en:");    // Informa que los archivos fueron guardados
        out.println("    JSON: " + outPath);            // Muestra la ruta del JSON generado
        out.println("    CSV:  " + csvPath);            // Muestra la ruta del CSV generado
        out.println("\n============================================================"); // Línea decorativa de cierre
        out.println("  BENCHMARK JAVA COMPLETADO");                                    // Mensaje final de éxito
        out.println("============================================================");   // Última línea decorativa
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    private static String esc(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\""); // Escapa barras invertidas y comillas dobles para JSON válido
    }

    private static String csvEsc(String s) {
        if (s == null) return "";                             // Si el valor es nulo, retorna cadena vacía
        boolean needsQuotes = s.contains(",") || s.contains("\"") || s.contains("\n") || s.contains("\r");
        // Determina si el valor necesita comillas: si contiene coma, comilla doble o saltos de línea
        String v = s.replace("\"", "\"\"");                  // Escapa las comillas dobles duplicándolas (estándar CSV)
        return needsQuotes ? ("\"" + v + "\"") : v;          // Envuelve en comillas si es necesario, o retorna el valor limpio
    }

    private static Path toCsvPath(Path jsonPath) {
        String name = jsonPath.getFileName().toString();      // Obtiene solo el nombre del archivo JSON sin la ruta
        String base = name.endsWith(".json") ? name.substring(0, name.length() - 5) : name;
        // Elimina la extensión .json del nombre si la tiene, para construir el nombre base
        return jsonPath.resolveSibling(base + ".csv");        // Construye la ruta del CSV en el mismo directorio que el JSON
    }

    private static void writeCsv(Path path, List<ResultRow2> rows) throws IOException {
        StringBuilder sb = new StringBuilder();
        sb.append("algorithm,language,n,timeSeconds,complexity,timedOut\n"); // Escribe la fila de encabezados del CSV
        for (ResultRow2 r : rows) {                           // Itera sobre cada resultado para escribir una fila
            sb.append(csvEsc(r.algorithm())).append(",");     // Agrega el nombre del algoritmo escapado para CSV
            sb.append(csvEsc(r.language())).append(",");      // Agrega el lenguaje escapado para CSV
            sb.append(r.n()).append(",");                      // Agrega el tamaño del arreglo
            sb.append(String.format(Locale.US, "%.9f", r.timeSeconds())).append(","); // Agrega el tiempo con 9 decimales y punto decimal
            sb.append(csvEsc(r.complexity())).append(",");    // Agrega la complejidad teórica escapada para CSV
            sb.append(r.timedOut());                          // Agrega el valor booleano de timeout
            sb.append("\n");                                  // Salto de línea para la siguiente fila
        }
        Files.writeString(path, sb.toString(), StandardCharsets.UTF_8); // Escribe todo el contenido CSV en el archivo en UTF-8
    }

    /** Lee hasta maxCount enteros desde archivo de texto plano. */
    private static int[] loadInts(Path path, int maxCount) throws IOException {
        int[] buf = new int[maxCount];  // Crea un buffer del tamaño máximo esperado para evitar redimensionamientos
        int idx = 0;                    // Índice para rastrear cuántos enteros se han leído
        try (BufferedReader br = Files.newBufferedReader(path, StandardCharsets.UTF_8)) { // Abre el archivo con buffer y UTF-8, se cierra automáticamente
            String line;
            while ((line = br.readLine()) != null && idx < maxCount) { // Lee línea por línea hasta EOF o hasta alcanzar el máximo
                line = line.trim();                                     // Elimina espacios y saltos de línea alrededor del valor
                if (!line.isEmpty()) {                                  // Ignora líneas vacías o que solo tenían espacios
                    buf[idx++] = Integer.parseInt(line);                // Convierte la línea a entero y lo almacena en el buffer
                }
            }
        }
        return idx == maxCount ? buf : Arrays.copyOf(buf, idx); // Si se llenó el buffer retorna tal cual; si no, recorta al tamaño real leído
    }
}