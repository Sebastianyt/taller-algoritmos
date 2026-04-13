import java.io.BufferedReader;           // Para leer archivos de texto línea por línea de forma eficiente
import java.io.IOException;              // Para manejar excepciones de entrada/salida
import java.io.PrintStream;              // Para imprimir en consola con control de buffer y codificación
import java.nio.charset.StandardCharsets; // Para especificar codificaciones de texto estándar (UTF-8)
import java.nio.file.Files;              // Para operaciones modernas sobre archivos (leer, escribir, verificar existencia)
import java.nio.file.Path;               // Para representar rutas de archivos de forma multiplataforma
import java.util.ArrayList;              // Para usar listas dinámicas que acumulan los resultados
import java.util.Arrays;                 // Para operaciones sobre arreglos (copiar, redimensionar)
import java.util.List;                   // Interfaz base para listas en Java
import java.util.Locale;                 // Para formatear números con punto decimal en lugar de coma

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

    // Tamaños de arreglos a evaluar en el benchmark
    private static final int[] SIZES = { 10_000, 100_000, 1_000_000 };
    // Nombres de los archivos de arreglos ordenados correspondientes a cada tamaño
    private static final String[] ARR_FILES = {
        "searching_10000.txt",
        "searching_100000.txt",
        "searching_1000000.txt"
    };
    // Nombres de los archivos de queries (valores a buscar) correspondientes a cada tamaño
    private static final String[] Q_FILES = {
        "queries_10000.txt",
        "queries_100000.txt",
        "queries_1000000.txt"
    };

    @FunctionalInterface                   // Marca que esta interfaz tiene exactamente un método abstracto (permite lambdas)
    private interface SearchFn {
        int search(int[] a, int x);        // Contrato que deben cumplir todos los algoritmos: recibe el arreglo y el valor a buscar, retorna el índice encontrado
    }

    private record AlgoCase(String name, String complexity, SearchFn fn) {}
    // Record inmutable que agrupa el nombre del algoritmo, su complejidad teórica y la función que lo ejecuta

    private record ResultRow(String algorithm, String language, int n, double timeSeconds, String complexity) {}
    // Record inmutable que representa una fila de resultado con todos los datos de una ejecución

    public static void main(String[] args) throws IOException {
        if (args.length < 2) {                                                         // Verifica que se pasaron al menos 2 argumentos por línea de comandos
            System.err.println("Uso: java SearchingRunner <dir_datos> <salida.json>"); // Muestra el uso correcto si faltan argumentos
            System.exit(1);                                                            // Termina el programa con código de error 1
        }

        Path dataDir = Path.of(args[0]);                                // Convierte el primer argumento en la ruta del directorio de datos
        Path outPath = Path.of(args[1]);                                // Convierte el segundo argumento en la ruta del archivo JSON de salida
        if (outPath.getParent() != null) outPath.getParent().toFile().mkdirs();
        // Si el archivo de salida tiene directorio padre, lo crea si no existe (evita error al escribir)

        PrintStream out = new PrintStream(System.out, true, "UTF-8");  // Crea un PrintStream con autoflush activado y codificación UTF-8

        out.println("============================================================"); // Línea decorativa de separación
        out.println("  BENCHMARK DE BUSQUEDA - JAVA");                               // Título del benchmark
        out.println("============================================================"); // Línea decorativa de separación

        AlgoCase[] cases = {
            new AlgoCase("Binary Search",  "O(log n)",   BinarySearch::search),
            // Búsqueda binaria clásica usando referencia al método estático search
            new AlgoCase("Ternary Search", "O(log n)",   TernarySearch::search),
            // Búsqueda ternaria (divide en 3 partes) usando referencia al método estático search
            new AlgoCase("Jump Search",    "O(sqrt(n))", JumpSearch::search),
            // Búsqueda por saltos de raíz cuadrada usando referencia al método estático search
        };

        List<ResultRow> rows = new ArrayList<>();       // Lista que acumulará todas las filas de resultados para el CSV
        StringBuilder json = new StringBuilder("[\n"); // Inicia la construcción del JSON como array abierto
        boolean first = true;                           // Bandera para controlar si es el primer elemento (para omitir la coma inicial)

        for (int si = 0; si < SIZES.length; si++) {    // Itera sobre cada tamaño de arreglo definido
            int n = SIZES[si];                          // Obtiene el tamaño actual
            Path arrPath = dataDir.resolve(ARR_FILES[si]); // Construye la ruta completa al archivo del arreglo ordenado
            Path qPath   = dataDir.resolve(Q_FILES[si]);   // Construye la ruta completa al archivo de queries

            if (!Files.exists(arrPath) || !Files.exists(qPath)) { // Verifica que ambos archivos existan antes de continuar
                System.err.println("  [ERROR] Faltan archivos de datos en: " + dataDir);       // Informa que faltan archivos
                System.err.println("  Necesarios: " + arrPath + " y " + qPath);                // Muestra exactamente qué archivos faltan
                System.err.println("  Ejecuta primero: python scripts/generate_searching_data.py"); // Indica cómo generarlos
                System.exit(1);                                                                 // Termina el programa con error
            }

            out.println("\n  -- n = " + String.format("%,d", n) + " --"); // Imprime el separador visual con el tamaño formateado con comas
            out.print("    Cargando arreglo ...");           // Indica que está comenzando la carga del arreglo ordenado
            out.flush();                                     // Vacía el buffer para que el mensaje aparezca de inmediato
            int[] arr = loadInts(arrPath, n);                // Carga hasta n enteros desde el archivo del arreglo ordenado
            out.println(" OK (" + arr.length + " elementos)"); // Confirma la carga exitosa con la cantidad real de elementos

            out.print("    Cargando queries ...");           // Indica que está comenzando la carga de los valores a buscar
            out.flush();                                     // Vacía el buffer para que el mensaje aparezca de inmediato
            int[] queries = loadInts(qPath, Integer.MAX_VALUE); // Carga TODOS los queries del archivo (sin límite de cantidad)
            out.println(" OK (" + queries.length + " consultas)"); // Confirma la carga exitosa con la cantidad de queries

            for (AlgoCase c : cases) {                       // Itera sobre cada algoritmo de búsqueda definido
                out.println("    [" + c.name() + "] ejecutando ..."); // Indica que el algoritmo está por comenzar
                out.flush();                                 // Vacía el buffer para que el mensaje aparezca de inmediato

                long checksum = 0;                           // Acumulador de resultados para verificar corrección y evitar optimizaciones del compilador
                long t0 = System.nanoTime();                 // Registra el tiempo exacto de inicio de todas las búsquedas
                for (int q : queries) {                      // Itera sobre cada valor a buscar en el arreglo
                    checksum += c.fn().search(arr, q);       // Ejecuta la búsqueda y acumula el índice retornado en el checksum
                }
                double secs = (System.nanoTime() - t0) / 1_000_000_000.0; // Calcula el tiempo total de todas las búsquedas en segundos

                String label = secs < 1.0
                    ? String.format(Locale.US, "%.2f ms", secs * 1000) // Si tardó menos de 1s, muestra en milisegundos con 2 decimales
                    : String.format(Locale.US, "%.3f s",  secs);       // Si tardó 1s o más, muestra en segundos con 3 decimales
                out.println("    [" + c.name() + "] OK " + label + " (checksum=" + checksum + ")"); // Imprime resultado con tiempo y checksum
                out.flush();                                 // Vacía el buffer para que el resultado aparezca de inmediato

                rows.add(new ResultRow(c.name(), "Java", n, secs, c.complexity())); // Agrega la fila de resultado a la lista para el CSV

                if (!first) json.append(",\n"); // Si no es el primer elemento, agrega coma separadora antes del nuevo objeto JSON
                first = false;                  // Marca que ya no es el primer elemento
                json.append("  {");             // Abre el objeto JSON para este resultado
                json.append("\"algorithm\":\"").append(esc(c.name())).append("\",");              // Agrega el nombre del algoritmo escapado
                json.append("\"language\":\"Java\",");                                             // Agrega el lenguaje fijo como "Java"
                json.append("\"n\":").append(n).append(",");                                       // Agrega el tamaño del arreglo
                json.append("\"timeSeconds\":").append(String.format(Locale.US, "%.9f", secs)).append(","); // Agrega el tiempo con 9 decimales
                json.append("\"complexity\":\"").append(esc(c.complexity())).append("\"");         // Agrega la complejidad teórica escapada
                json.append("}");               // Cierra el objeto JSON
            }
        }

        json.append("\n]\n");                                            // Cierra el array JSON y agrega salto de línea final
        Files.writeString(outPath, json.toString(), StandardCharsets.UTF_8); // Escribe el JSON completo en el archivo de salida en UTF-8

        Path csvPath = toCsvPath(outPath);                               // Genera la ruta del CSV reemplazando la extensión .json por .csv
        writeCsv(csvPath, rows);                                         // Escribe todos los resultados en formato CSV

        out.println("\n  Resultados guardados en:");                      // Informa que los archivos fueron guardados
        out.println("    JSON: " + outPath);                             // Muestra la ruta del JSON generado
        out.println("    CSV:  " + csvPath);                             // Muestra la ruta del CSV generado

        out.println("\n============================================================"); // Línea decorativa de cierre
        out.println("  BENCHMARK JAVA COMPLETADO");                                    // Mensaje final de éxito
        out.println("============================================================");   // Última línea decorativa
    }

    private static String esc(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\""); // Escapa barras invertidas y comillas dobles para producir JSON válido
    }

    private static String csvEsc(String s) {
        if (s == null) return "";                              // Si el valor es nulo, retorna cadena vacía para evitar NullPointerException
        boolean needsQuotes = s.contains(",") || s.contains("\"") || s.contains("\n") || s.contains("\r");
        // Determina si el valor necesita comillas: si contiene coma, comilla doble o saltos de línea
        String v = s.replace("\"", "\"\"");                   // Escapa las comillas dobles duplicándolas (estándar CSV RFC 4180)
        return needsQuotes ? ("\"" + v + "\"") : v;           // Envuelve en comillas si es necesario, o retorna el valor limpio
    }

    private static Path toCsvPath(Path jsonPath) {
        String name = jsonPath.getFileName().toString();       // Obtiene solo el nombre del archivo JSON sin la ruta completa
        String base = name.endsWith(".json") ? name.substring(0, name.length() - 5) : name;
        // Elimina la extensión .json del nombre si la tiene, para construir el nombre base sin extensión
        return jsonPath.resolveSibling(base + ".csv");         // Construye la ruta del CSV en el mismo directorio que el JSON
    }

    private static void writeCsv(Path path, List<ResultRow> rows) throws IOException {
        StringBuilder sb = new StringBuilder();
        sb.append("algorithm,language,n,timeSeconds,complexity\n"); // Escribe la fila de encabezados del CSV (sin columna timedOut porque búsqueda no tiene timeout)
        for (ResultRow r : rows) {                             // Itera sobre cada resultado para escribir una fila
            sb.append(csvEsc(r.algorithm())).append(",");      // Agrega el nombre del algoritmo escapado para CSV
            sb.append(csvEsc(r.language())).append(",");       // Agrega el lenguaje escapado para CSV
            sb.append(r.n()).append(",");                       // Agrega el tamaño del arreglo
            sb.append(String.format(Locale.US, "%.9f", r.timeSeconds())).append(","); // Agrega el tiempo con 9 decimales y punto decimal
            sb.append(csvEsc(r.complexity()));                 // Agrega la complejidad teórica escapada (última columna, sin coma al final)
            sb.append("\n");                                   // Salto de línea para la siguiente fila
        }
        Files.writeString(path, sb.toString(), StandardCharsets.UTF_8); // Escribe todo el contenido CSV en el archivo en UTF-8
    }

    private static int[] loadInts(Path path, int maxCount) throws IOException {
        int cap = maxCount == Integer.MAX_VALUE ? 1_000_000 : maxCount;
        // Si no hay límite (Integer.MAX_VALUE), usa 1.000.000 como capacidad inicial del buffer
        int[] buf = new int[Math.min(cap, 1_000_000)];        // Crea el buffer inicial con la capacidad calculada (máximo 1.000.000)
        int idx = 0;                                           // Índice para rastrear cuántos enteros se han leído
        try (BufferedReader br = Files.newBufferedReader(path, StandardCharsets.UTF_8)) { // Abre el archivo con buffer y UTF-8, se cierra automáticamente
            String line;
            while ((line = br.readLine()) != null) {           // Lee línea por línea hasta llegar al final del archivo
                line = line.trim();                            // Elimina espacios y saltos de línea alrededor del valor
                if (line.isEmpty()) continue;                  // Salta las líneas vacías sin procesarlas
                if (idx == buf.length) {                       // Si el buffer está lleno...
                    buf = Arrays.copyOf(buf, buf.length * 2); // ...lo duplica de tamaño para seguir leyendo (estrategia de crecimiento dinámico)
                }
                buf[idx++] = Integer.parseInt(line);           // Convierte la línea a entero y lo almacena en la siguiente posición del buffer
                if (idx >= maxCount) break;                    // Si se alcanzó el límite máximo de elementos, detiene la lectura
            }
        }
        return Arrays.copyOf(buf, idx);                        // Retorna una copia recortada al tamaño real de elementos leídos (sin posiciones vacías)
    }
}