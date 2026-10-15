"""
Pruebas del proyecto. Ejecutar:  python pruebas.py

1. Frases en ingles que deben y que no deben pertenecer al lenguaje.
2. Expresiones de la gramatica 1.txt.
3. Equivalencia: la CNF generada de 1.txt contra la CNF del ejemplo (1-cnf.txt)
   y contra un reconocedor independiente, para todas las cadenas hasta longitud 7.
4. Simplificacion con ε en el simbolo inicial, ciclos unitarios y simbolos inutiles.
"""

import itertools
import sys
import time

from gramatica import leer_gramatica, parsear_gramatica
from cnf import a_cnf
from cyk import cyk, indices_gramatica, tokenizar

fallos = 0


def verificar(condicion, mensaje):
    global fallos
    if not condicion:
        fallos += 1
        print("   FALLO:", mensaje)


def reconocedor_general(g, tokens):
    """
    Reconocedor independiente del CYK para cualquier CFG (con ε y unitarias),
    usado solo como referencia: punto fijo sobre hechos (A, i, j) = "A =>* w[i:j]".
    Es mucho mas lento, pero no depende de la conversion a CNF.
    """
    n = len(tokens)
    deriva = set()

    def cubre(cuerpo, i, j):
        # posiciones alcanzables despues de leer cada simbolo del cuerpo
        actuales = {i}
        for s in cuerpo:
            siguientes = set()
            for p in actuales:
                if g.es_no_terminal(s):
                    siguientes.update(q for q in range(p, j + 1) if (s, p, q) in deriva)
                elif p < j and tokens[p] == s:
                    siguientes.add(p + 1)
            actuales = siguientes
            if not actuales:
                return False
        return j in actuales

    cambio = True
    while cambio:
        cambio = False
        for i in range(n + 1):
            for j in range(i, n + 1):
                for a, cuerpos in g.producciones.items():
                    if (a, i, j) in deriva:
                        continue
                    if any(cubre(c, i, j) for c in cuerpos):
                        deriva.add((a, i, j))
                        cambio = True
    return (g.inicial, 0, n) in deriva


def evaluar(g_cnf, indices, frase):
    return cyk(g_cnf, tokenizar(frase, g_cnf.terminales), indices)


#  prueba 1

INGLES_SI = [
    "She eats a cake with a fork",
    "The cat drinks the beer",
    "he cooks",
    "the cat drinks",
    "He cuts the meat with a knife",
    "She cooks the soup in the oven with a spoon",
    "the dog eats in the oven",
    "A fork drinks the cat",                  # sintacticamente correcta, sin sentido
    "she eats a cake with a fork with a knife in the oven",
]

INGLES_NO = [
    "She eats a cake with fork",              # falta el determinante
    "cat drinks the beer",                    # sujeto sin determinante
    "she eats cake",
    "The cat the beer",                       # no hay verbo
    "he drinks the beer the",                 # incompleta
    "eats she the cake",                      # orden incorrecto
    "She drinks a coffee",                    # palabra fuera del vocabulario
    "with a fork she eats",
    "she he eats",
    "",                                       # cadena vacia
]


def prueba_ingles():
    print("\n1. Gramatica del enunciado (ingles)")
    g_cnf, _ = a_cnf(leer_gramatica("gramaticas/ingles.txt"))
    indices = indices_gramatica(g_cnf)
    print(f"   {'esperado':<9}{'obtenido':<9}{'tiempo':>10}  frase")
    for frases, esperado in ((INGLES_SI, True), (INGLES_NO, False)):
        for frase in frases:
            r = evaluar(g_cnf, indices, frase)
            print(f"   {'SÍ' if esperado else 'NO':<9}{'SÍ' if r.aceptada else 'NO':<9}"
                  f"{r.tiempo * 1e6:>8.1f}µs  {frase or '(vacia)'}")
            verificar(r.aceptada == esperado, frase)


#  prueba 2

EXPR_SI = ["id", "id+id", "id*id", "id+id*id", "(id)", "((id))", "(id+id)*id",
           "id*(id+id)*id", "id + id + id"]
EXPR_NO = ["+", "id+", "(id", "id)", "()", "id id", "id*+id", ")(", "(id+)id"]


def prueba_expresiones():
    print("\n2. Gramatica 1.txt (expresiones)")
    g_cnf, _ = a_cnf(leer_gramatica("gramaticas/1.txt"))
    indices = indices_gramatica(g_cnf)
    for frases, esperado in ((EXPR_SI, True), (EXPR_NO, False)):
        for frase in frases:
            r = evaluar(g_cnf, indices, frase)
            print(f"   {'SÍ' if esperado else 'NO':<9}{'SÍ' if r.aceptada else 'NO':<9}  {frase}")
            verificar(r.aceptada == esperado, frase)


#  prueba 3

def prueba_equivalencia(longitud_max=7):
    print(f"\n3. Equivalencia de 1.txt -> CNF generada vs 1-cnf.txt (cadenas hasta longitud {longitud_max})")
    original = leer_gramatica("gramaticas/1.txt")
    generada, _ = a_cnf(original)
    ejemplo = leer_gramatica("gramaticas/1-cnf.txt")
    verificar(generada.es_cnf(), "la CNF generada no cumple la forma")
    verificar(ejemplo.es_cnf(), "1-cnf.txt no cumple la forma")
    print(f"   Producciones: original {original.num_producciones()}, "
          f"generada {generada.num_producciones()}, ejemplo {ejemplo.num_producciones()}")

    ind_gen, ind_ej = indices_gramatica(generada), indices_gramatica(ejemplo)
    alfabeto = ["id", "+", "*", "(", ")"]
    total = aceptadas = diferencias = 0
    t0 = time.perf_counter()
    for n in range(1, longitud_max + 1):
        for tokens in itertools.product(alfabeto, repeat=n):
            tokens = list(tokens)
            a = cyk(generada, tokens, ind_gen).aceptada
            b = cyk(ejemplo, tokens, ind_ej).aceptada
            total += 1
            aceptadas += a
            if a != b:
                diferencias += 1
                verificar(False, f"difieren en {' '.join(tokens)}")
    print(f"   {total} cadenas comparadas, {aceptadas} aceptadas por ambas, "
          f"{diferencias} diferencias ({time.perf_counter() - t0:.1f} s)")

    # contra el reconocedor independiente (sobre la gramatica ORIGINAL, con ε)
    total_ref = 0
    for n in range(0, 6):
        for tokens in itertools.product(alfabeto, repeat=n):
            tokens = list(tokens)
            verificar(cyk(generada, tokens, ind_gen).aceptada == reconocedor_general(original, tokens),
                      f"CYK y reconocedor de referencia difieren en {' '.join(tokens)}")
            total_ref += 1
    print(f"   {total_ref} cadenas verificadas contra el reconocedor de referencia")


#  prueba 4

GRAMATICA_SIMPLIFICACION = """
S -> A B | a S b | e
A -> B | a
B -> A | b | C
C -> c C
D -> d
"""


def prueba_simplificacion():
    print("\n4. Simplificacion: ε en el inicial, ciclo unitario A <-> B, C no generador, D no alcanzable")
    g = parsear_gramatica(GRAMATICA_SIMPLIFICACION)
    g_cnf, pasos = a_cnf(g)
    for titulo, _, detalle in pasos[1:4]:
        print("   " + titulo + ": " + detalle.replace("\n", "; "))
    print("   CNF:", str(g_cnf).replace("\n", "  ;  "))
    verificar(g_cnf.es_cnf(), "no quedo en CNF")
    verificar("C" not in g_cnf.no_terminales, "C deberia eliminarse")
    verificar("D" not in g_cnf.no_terminales, "D deberia eliminarse")
    verificar(g_cnf.acepta_vacia, "S es anulable, ε debe aceptarse")

    indices = indices_gramatica(g_cnf)
    total = 0
    for n in range(0, 7):
        for tokens in itertools.product(["a", "b", "c", "d"], repeat=n):
            tokens = list(tokens)
            verificar(cyk(g_cnf, tokens, indices).aceptada == reconocedor_general(g, tokens),
                      f"difieren en '{' '.join(tokens)}'")
            total += 1
    print(f"   {total} cadenas verificadas contra el reconocedor de referencia")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    prueba_ingles()
    prueba_expresiones()
    prueba_equivalencia()
    prueba_simplificacion()
    print("\nResultado:", "todas las pruebas pasaron" if fallos == 0 else f"{fallos} fallos")
    sys.exit(1 if fallos else 0)
