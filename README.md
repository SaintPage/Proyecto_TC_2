Proyecto 2 - Algoritmo CYK
Ángel Mérida - 23661 José Sanchéz 1221
Teoría de la Computación, Universidad del Valle de Guatemala


Descripción

Determina si una frase pertenece al lenguaje de una gramática libre de contexto usando el algoritmo CYK. Antes de correr CYK la gramática se simplifica y se convierte a Forma Normal de Chomsky. Para cada frase se muestra SÍ o NO, el tiempo del algoritmo, la tabla dinámica y el árbol de parseo.





Uso

    python main.py                                        modo interactivo con la gramática del enunciado
    python main.py -f "She eats a cake with a fork"       evalúa una frase (se puede repetir -f)
    python main.py -g gramaticas/1.txt -f "(id+id)*id"    usa otra gramática
    python main.py --pasos                                muestra cada paso de la conversión a CNF
    python main.py --sin-imagenes --sin-tabla             salida solo en consola
    python pruebas.py                                     pruebas automáticas
    python medir_tiempos.py                               gráfica de tiempo vs longitud de la frase


Archivos

    main.py            interfaz de consola
    gramatica.py       lectura y representación de la gramática
    cnf.py             simplificación y conversión a CNF (ε, unitarias, inútiles, TERM, BIN)
    cyk.py             algoritmo CYK, tokenización y reconstrucción del árbol
    dibujo.py          imágenes del árbol de parseo y de la tabla CYK (matplotlib)
    pruebas.py         frases dentro y fuera del lenguaje, equivalencia de gramáticas
    medir_tiempos.py   experimento de tiempos
    gramaticas/        ingles.txt (enunciado), 1.txt y 1-cnf.txt (ejemplos), ambigua.txt
    imagenes/          árboles, tablas y gráfica de tiempos generados
    salidas/           gramáticas en CNF generadas por el programa


Formato de las gramáticas

Una regla por línea con el formato A -> x y | z. Los símbolos se separan con espacios y la letra e representa la cadena vacía. El símbolo inicial es el lado izquierdo de la primera regla. Todo símbolo que no aparece a la izquierda de una regla es terminal. Las líneas que empiezan con # son comentarios.


Diseño de la aplicación

El programa se divide en etapas independientes, cada una en su archivo:

1. Lectura (gramatica.py). La gramática se guarda como un diccionario: no terminal -> lista de cuerpos, y cada cuerpo es una tupla de símbolos. Es terminal todo símbolo que nunca aparece a la izquierda de una regla, así que el archivo no necesita declarar el alfabeto.
2. Conversión a CNF (cnf.py). Se aplican cinco pasos en orden y cada uno devuelve una gramática nueva:
   - eliminar ε: se calculan los anulables por punto fijo y se generan las 2^k variantes de cada cuerpo;
   - eliminar unitarias: se calculan los pares unitarios (A =>* B) y se copian los cuerpos no unitarios;
   - eliminar inútiles: primero los no generadores y después los no alcanzables;
   - TERM: cada terminal dentro de un cuerpo largo se cambia por un no terminal T_a -> a (se reutiliza uno existente si ya hay);
   - BIN: un cuerpo X1 X2 ... Xn se parte en X1 C, C -> X2 ... Xn, compartiendo sufijos repetidos.
   El orden importa: quitar ε antes que las unitarias evita que reaparezcan reglas unitarias, y quitar inútiles antes de TERM/BIN evita crear símbolos auxiliares que luego se descartarían. Como la CNF no puede expresar ε, se guarda aparte la bandera acepta_vacia.
3. CYK (cyk.py). Programación dinámica con tabla[l][i] = conjunto de no terminales que derivan la subcadena que empieza en i y tiene longitud l. Cada entrada guarda un apuntador (corte k, B, C), con el que se reconstruye el árbol sin volver a buscar. También se cuenta cuántos árboles tiene cada celda, lo que permite avisar si la frase es ambigua. Se precalculan índices inversos (terminal -> cabezas, (B, C) -> cabezas) para no recorrer todas las reglas en cada celda. Complejidad O(n^3 · |G|).
4. Salida (main.py, dibujo.py). Imprime SÍ/NO, el tiempo, la tabla triangular y el árbol en texto, y genera las imágenes con matplotlib.

Decisión de diseño: la gramática se convierte a CNF una sola vez al arrancar y se reutiliza para todas las frases. El tiempo reportado por frase mide solo CYK, no la conversión.


Discusión

Obstáculos encontrados
- ε en el símbolo inicial. La CNF estricta no permite S -> ε. Se resolvió marcando acepta_vacia en la gramática y consultándola solo cuando la cadena es vacía.
- Ciclos de unitarias (A -> B, B -> A). Un recorrido ingenuo no termina. Se resolvió con un recorrido BFS que recuerda los símbolos ya alcanzados.
- Nombres de los símbolos nuevos. TERM y BIN crean no terminales que pueden chocar con los existentes y los terminales como "(" o "+" no sirven como nombre. Se usa GeneradorNombres con una tabla de nombres (lpar, mas, ...) y sufijo numérico si hay colisión.
- Tokenización. En la gramática de expresiones no hay espacios ("id+id*id"), y en inglés hay mayúsculas ("She"). La tokenización usa la coincidencia más larga con los terminales y pasa a minúsculas solo si así existe en la gramática. Se ignora el punto o signo final si no es terminal.
- Verificar la conversión. Una CNF mal hecha da respuestas incorrectas sin avisar. Por eso las pruebas comparan contra una CNF dada (1-cnf.txt) y contra un reconocedor independiente que no usa CNF.

Recomendaciones
- CYK es O(n^3), así que sirve bien para frases cortas, pero crece rápido con la longitud (ver imagenes/tiempos_cyk.png generada con medir_tiempos.py).
- El número de reglas puede crecer al quitar ε (2^k variantes por cuerpo), por lo que conviene que las gramáticas no tengan cuerpos largos con muchos anulables.
- Las frases ambiguas se detectan por el conteo de árboles; el programa solo dibuja uno de ellos.
- Una mejora posible: mostrar todos los árboles de las frases ambiguas, no solo uno.


Ejemplos y pruebas realizadas

Todas se ejecutan con python pruebas.py, que termina con "todas las pruebas pasaron".

1. Gramática del enunciado (inglés): 9 frases que deben aceptarse y 10 que deben rechazarse.
   - Aceptadas: "She eats a cake with a fork", "The cat drinks the beer", "he cooks", "A fork drinks the cat" (correcta sintácticamente aunque sin sentido), "She cooks the soup in the oven with a spoon", etc.
   - Rechazadas: "She eats a cake with fork" (falta determinante), "cat drinks the beer", "The cat the beer" (sin verbo), "eats she the cake" (orden incorrecto), "She drinks a coffee" (palabra fuera del vocabulario) y la cadena vacía.
2. Gramática de expresiones (gramaticas/1.txt): 9 expresiones válidas ("id+id*id", "(id+id)*id", "((id))") y 9 inválidas ("id+", "(id", "()", "id*+id", ")(").
3. Equivalencia de CNF: la CNF generada para 1.txt se compara con 1-cnf.txt sobre las 97 655 cadenas de longitud 1 a 7 del alfabeto {id, +, *, (, )}: 0 diferencias (60 aceptadas por ambas). Además, 3 906 cadenas hasta longitud 5 se comparan contra el reconocedor de referencia sobre la gramática original.
4. Simplificación: una gramática con ε en el inicial, un ciclo unitario A <-> B, un símbolo no generador (C) y uno no alcanzable (D). Se comprueba que C y D se eliminan, que queda en CNF y que acepta ε. Se verifican 5 461 cadenas contra el reconocedor de referencia.

Ejemplo de ejecución:

    python main.py -f "She eats a cake with a fork" --sin-imagenes

    Resultado: SÍ
    [S [NP she] [VP [VP [V eats] [NP [Det a] [N cake]]] [PP [P with] [NP [Det a] [N fork]]]]]

Imágenes generadas de ejemplo en imagenes/: arbol_ingles_she_eats_a_cake_with_a_fork.png, tabla_ingles_she_eats_a_fork_cake.png (frase rechazada), arbol_ambigua_id_mas_id_por_id.png (frase ambigua) y tiempos_cyk.png.
