"""
Algoritmo CYK (Cocke-Younger-Kasami) con programacion dinamica.

Tabla:  tabla[l][i]  = { A : apuntador }   para la subcadena que empieza en i
                                           y tiene longitud l (1 <= l <= n)
        A pertenece a la celda si y solo si  A =>* w[i .. i+l-1]

Apuntador (backpointer) guardado en cada celda:
        hoja:     ("hoja", palabra)            por la regla A -> palabra
        interno:  (k, B, C)                    por la regla A -> B C, donde
                                               B cubre w[i .. i+k-1] y C el resto
Con los apuntadores se reconstruye el arbol de parseo sin volver a buscar.
Ademas se cuenta cuantos arboles distintos hay (para detectar ambiguedad).

Complejidad: O(n^3 * |G|)
"""

import re
import time
from dataclasses import dataclass, field


@dataclass
class Nodo:
    simbolo: str
    hijos: list = field(default_factory=list)   # vacio en las hojas (palabras)

    def es_hoja(self):
        return not self.hijos


@dataclass
class ResultadoCYK:
    tokens: list
    aceptada: bool
    tabla: list            # tabla[l][i] -> dict A -> apuntador
    conteo: list           # conteo[l][i] -> dict A -> numero de arboles
    tiempo: float          # segundos que tarda el algoritmo CYK
    arbol: Nodo = None
    num_arboles: int = 0


#  tokenizacion

def tokenizar(frase, terminales):
    """
    Separa la frase en terminales de la gramatica.
    - Palabras (letras/digitos) son un token cada una; se pasan a minusculas
      si asi existen en la gramatica ("She" -> "she").
    - Secuencias de simbolos se parten por coincidencia mas larga con los
      terminales ("id+id" -> id, +, id ; "(id)" -> (, id, ) ).
    - El punto, signo de interrogacion o exclamacion final se ignora
      si no es terminal de la gramatica.
    """
    frase = frase.strip()
    while frase and frase[-1] in ".!?" and frase[-1] not in terminales:
        frase = frase[:-1].rstrip()

    simbolos_terminales = sorted((t for t in terminales if not t.isalnum()), key=len, reverse=True)
    tokens = []
    for pieza in re.findall(r"\w+|[^\w\s]+", frase):
        if pieza[0].isalnum() or pieza[0] == "_":
            if pieza not in terminales and pieza.lower() in terminales:
                pieza = pieza.lower()
            tokens.append(pieza if pieza in terminales else pieza.lower())
        else:
            i = 0
            while i < len(pieza):
                for t in simbolos_terminales:
                    if pieza.startswith(t, i):
                        tokens.append(t)
                        i += len(t)
                        break
                else:
                    tokens.append(pieza[i])     # simbolo desconocido: hara fallar CYK
                    i += 1
    return tokens


#  CYK

def indices_gramatica(g):
    """Indices inversos: palabra -> [A]   y   (B, C) -> [A]."""
    por_terminal, por_par = {}, {}
    for cabeza, cuerpos in g.producciones.items():
        for cuerpo in cuerpos:
            if len(cuerpo) == 1:
                por_terminal.setdefault(cuerpo[0], []).append(cabeza)
            else:
                por_par.setdefault(cuerpo, []).append(cabeza)
    return por_terminal, por_par


def cyk(g, tokens, indices=None):
    """g debe estar en CNF. Devuelve un ResultadoCYK."""
    inicio = time.perf_counter()

    por_terminal, por_par = indices or indices_gramatica(g)
    n = len(tokens)
    # tabla[0] queda vacia para que el indice coincida con la longitud
    tabla = [[{} for _ in range(n - l + 1)] for l in range(n + 1)]
    conteo = [[{} for _ in range(n - l + 1)] for l in range(n + 1)]

    # Caso base, longitud 1: reglas A -> a
    for i, palabra in enumerate(tokens):
        for a in por_terminal.get(palabra, ()):
            tabla[1][i][a] = ("hoja", palabra)
            conteo[1][i][a] = 1

    # Longitudes 2..n: reglas A -> B C combinando dos subcadenas ya resueltas
    for l in range(2, n + 1):
        for i in range(n - l + 1):
            celda, cuenta = tabla[l][i], conteo[l][i]
            for k in range(1, l):                       # punto de corte
                izquierda, derecha = tabla[k][i], tabla[l - k][i + k]
                if not izquierda or not derecha:
                    continue
                for b in izquierda:
                    for c in derecha:
                        for a in por_par.get((b, c), ()):
                            if a not in celda:
                                celda[a] = (k, b, c)
                                cuenta[a] = 0
                            cuenta[a] += conteo[k][i][b] * conteo[l - k][i + k][c]

    if n == 0:
        aceptada = g.acepta_vacia
    else:
        aceptada = g.inicial in tabla[n][0]

    tiempo = time.perf_counter() - inicio

    r = ResultadoCYK(tokens, aceptada, tabla, conteo, tiempo)
    if aceptada and n > 0:
        r.arbol = construir_arbol(tabla, g.inicial, 0, n)
        r.num_arboles = conteo[n][0][g.inicial]
    elif aceptada:
        r.arbol = Nodo(g.inicial, [Nodo("ε")])
        r.num_arboles = 1
    return r


def construir_arbol(tabla, simbolo, i, l):
    apuntador = tabla[l][i][simbolo]
    if apuntador[0] == "hoja":
        return Nodo(simbolo, [Nodo(apuntador[1])])
    k, b, c = apuntador
    return Nodo(simbolo, [construir_arbol(tabla, b, i, k),
                          construir_arbol(tabla, c, i + k, l - k)])


#  impresion

def arbol_a_texto(nodo, prefijo="", ultimo=True, raiz=True):
    lineas = []
    if raiz:
        lineas.append(nodo.simbolo)
    else:
        lineas.append(prefijo + ("└── " if ultimo else "├── ") + nodo.simbolo)
        prefijo += "    " if ultimo else "│   "
    for j, hijo in enumerate(nodo.hijos):
        lineas.extend(arbol_a_texto(hijo, prefijo, j == len(nodo.hijos) - 1, False))
    return lineas if not raiz else "\n".join(lineas)


def arbol_a_corchetes(nodo):
    if nodo.es_hoja():
        return nodo.simbolo
    return "[" + nodo.simbolo + " " + " ".join(arbol_a_corchetes(h) for h in nodo.hijos) + "]"


def tabla_a_texto(resultado):
    """Tabla triangular: la fila de abajo es longitud 1, la de arriba longitud n."""
    n = len(resultado.tokens)
    if n == 0:
        return "(cadena vacia)"
    celdas = {}
    for l in range(1, n + 1):
        for i in range(n - l + 1):
            celdas[(l, i)] = "{" + ",".join(sorted(resultado.tabla[l][i])) + "}" \
                if resultado.tabla[l][i] else "∅"
    ancho = max(max(len(v) for v in celdas.values()), max(len(t) for t in resultado.tokens)) + 2
    lineas = []
    for l in range(n, 0, -1):
        fila = "".join(celdas[(l, i)].center(ancho) for i in range(n - l + 1))
        lineas.append(f"l={l:<3}" + fila)
    lineas.append("     " + "".join(t.center(ancho) for t in resultado.tokens))
    return "\n".join(lineas)
