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
