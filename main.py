"""
Proyecto 2 - Teoria de la Computacion
Parsing de frases con el algoritmo CYK.

Uso:
    python main.py                                   (modo interactivo, gramatica en ingles)
    python main.py -f "She eats a cake with a fork"
    python main.py -g gramaticas/1.txt -f "id + id * id" --pasos
    python main.py --pasos --sin-imagenes

Salida por frase: SI / NO, tiempo del CYK, tabla dinamica y arbol de parseo.
Las imagenes se guardan en imagenes/ y la gramatica en CNF en salidas/.
"""

import argparse
import os
import re
import sys
import time

from gramatica import leer_gramatica, guardar_gramatica
from cnf import a_cnf, NOMBRES_SIMBOLOS
from cyk import (cyk, indices_gramatica, tokenizar, arbol_a_texto,
                 arbol_a_corchetes, tabla_a_texto)

CARPETA_IMAGENES = "imagenes"
CARPETA_SALIDAS = "salidas"


def nombre_archivo(frase):
    # los simbolos se cambian por su nombre para que "(id+id)*id" y "id+id*id" no choquen
    texto = "".join(f" {NOMBRES_SIMBOLOS[c]} " if c in NOMBRES_SIMBOLOS else c for c in frase.lower())
    limpio = re.sub(r"[^\w]+", "_", texto).strip("_")
    return (limpio or "vacia")[:60]


def formatear_tiempo(segundos):
    if segundos < 1e-3:
        return f"{segundos * 1e6:.1f} µs"
    return f"{segundos * 1e3:.3f} ms"


def mostrar_pasos(pasos):
    for titulo, g, detalle in pasos:
        print("\n" + titulo)
        print("-" * len(titulo))
        if detalle:
            print(detalle)
            print()
        print(g)


def procesar(frase, g_cnf, indices, nombre_gramatica, imagenes=True, mostrar_tabla=True):
    tokens = tokenizar(frase, g_cnf.terminales)
    resultado = cyk(g_cnf, tokens, indices)

    print("\nFrase:  ", frase)
    print("Tokens: ", tokens)
    print("Resultado:", "SÍ" if resultado.aceptada else "NO")
    print("Tiempo CYK:", formatear_tiempo(resultado.tiempo))

    if mostrar_tabla and tokens:
        print("\nTabla CYK (fila l = longitud de la subcadena):")
        print(tabla_a_texto(resultado))

    if resultado.aceptada:
        print("\nÁrbol de parseo:")
        print(arbol_a_texto(resultado.arbol))
        print("\nEn corchetes:", arbol_a_corchetes(resultado.arbol))
        if resultado.num_arboles > 1:
            print(f"Nota: hay {resultado.num_arboles} árboles distintos (frase ambigua); se muestra uno.")
    else:
        desconocidas = [t for t in tokens if t not in g_cnf.terminales]
        if desconocidas:
            print("Palabras que no están en la gramática:", ", ".join(desconocidas))

    if imagenes and tokens:
        from dibujo import dibujar_arbol, dibujar_tabla
        os.makedirs(CARPETA_IMAGENES, exist_ok=True)
        base = f"{nombre_gramatica}_{nombre_archivo(frase)}"
        ruta_tabla = os.path.join(CARPETA_IMAGENES, f"tabla_{base}.png")
        dibujar_tabla(resultado, g_cnf.inicial, ruta_tabla,
                      f"CYK: {' '.join(tokens)}  ->  {'SÍ' if resultado.aceptada else 'NO'}")
        print("\nImagen de la tabla:", ruta_tabla)
        if resultado.aceptada:
            ruta_arbol = os.path.join(CARPETA_IMAGENES, f"arbol_{base}.png")
            dibujar_arbol(resultado.arbol, ruta_arbol, " ".join(tokens))
            print("Imagen del árbol: ", ruta_arbol)
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Algoritmo CYK sobre una CFG")
    parser.add_argument("-g", "--gramatica", default=os.path.join("gramaticas", "ingles.txt"),
                        help="archivo .txt con la gramática (por defecto la del enunciado)")
    parser.add_argument("-f", "--frase", action="append",
                        help="frase a evaluar (se puede repetir); sin -f entra en modo interactivo")
    parser.add_argument("--pasos", action="store_true",
                        help="mostrar cada paso de la simplificación a CNF")
    parser.add_argument("--sin-imagenes", action="store_true", help="no generar imágenes")
    parser.add_argument("--sin-tabla", action="store_true", help="no imprimir la tabla CYK")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    g = leer_gramatica(args.gramatica)
    nombre = os.path.splitext(os.path.basename(args.gramatica))[0]

    t0 = time.perf_counter()
    g_cnf, pasos = a_cnf(g)
    t_cnf = time.perf_counter() - t0
    indices = indices_gramatica(g_cnf)

    os.makedirs(CARPETA_SALIDAS, exist_ok=True)
    ruta_cnf = os.path.join(CARPETA_SALIDAS, f"{nombre}-cnf-generada.txt")
    guardar_gramatica(g_cnf, ruta_cnf)

    if args.pasos:
        mostrar_pasos(pasos)
    else:
        print("Gramática en Forma Normal de Chomsky:")
        print(g_cnf)
    print(f"\nConversión a CNF: {formatear_tiempo(t_cnf)}  (guardada en {ruta_cnf})")
    print(f"Símbolo inicial: {g_cnf.inicial}" + ("   (acepta ε)" if g_cnf.acepta_vacia else ""))

    opciones = dict(imagenes=not args.sin_imagenes, mostrar_tabla=not args.sin_tabla)
    if args.frase:
        for frase in args.frase:
            procesar(frase, g_cnf, indices, nombre, **opciones)
        return

    print("\nEscriba una frase (línea vacía o 'salir' para terminar).")
    while True:
        try:
            frase = input("\nw = ").strip()
        except EOFError:
            break
        if not frase or frase.lower() == "salir":
            break
        procesar(frase, g_cnf, indices, nombre, **opciones)


if __name__ == "__main__":
    main()
