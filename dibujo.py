"""
Dibujo con matplotlib del arbol de parseo y de la tabla CYK.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

COLOR_NT = "#dbe8f6"
BORDE_NT = "#2f5d8a"
COLOR_T = "#fdf0d5"
BORDE_T = "#b07d1a"
COLOR_OK = "#d8f0d8"
BORDE_OK = "#2e7d32"
COLOR_NO = "#f7d9d9"
BORDE_NO = "#b23b3b"


#  arbol

def _posiciones(raiz):
    """
    Las hojas (palabras) se reparten de izquierda a derecha en la fila de abajo;
    cada nodo interno queda centrado sobre sus hijos. Asi no se cruzan aristas.
    """
    pos = {}
    profundidad_max = [0]
    hojas = [0]

    def profundidad(nodo, d):
        profundidad_max[0] = max(profundidad_max[0], d)
        for h in nodo.hijos:
            profundidad(h, d + 1)

    profundidad(raiz, 0)

    def colocar(nodo, d):
        if nodo.es_hoja():
            x = hojas[0]
            hojas[0] += 1
            pos[id(nodo)] = (x, -profundidad_max[0])   # todas las palabras alineadas abajo
            return x
        xs = [colocar(h, d + 1) for h in nodo.hijos]
        x = sum(xs) / len(xs)
        pos[id(nodo)] = (x, -d)
        return x

    colocar(raiz, 0)
    return pos, profundidad_max[0], hojas[0]


def dibujar_arbol(raiz, ruta, titulo=""):
    pos, prof, num_hojas = _posiciones(raiz)
    sep_x, sep_y = 1.6, 1.0
    ancho = max(4.0, num_hojas * sep_x * 0.95 + 1)
    alto = max(3.0, (prof + 1) * sep_y * 0.95 + 1.2)
    fig, ax = plt.subplots(figsize=(ancho, alto))

    def xy(nodo):
        x, y = pos[id(nodo)]
        return x * sep_x, y * sep_y

    def aristas(nodo):
        x0, y0 = xy(nodo)
        for h in nodo.hijos:
            x1, y1 = xy(h)
            estilo = "--" if h.es_hoja() and y0 - y1 > sep_y * 1.01 else "-"
            ax.plot([x0, x1], [y0, y1], estilo, color="#666666", lw=1.1, zorder=1)
            aristas(h)

    def nodos(nodo):
        x, y = xy(nodo)
        hoja = nodo.es_hoja()
        ax.text(x, y, nodo.simbolo, ha="center", va="center", zorder=3,
                fontsize=11, fontstyle="italic" if hoja else "normal",
                fontweight="normal" if hoja else "bold",
                color="#5a3e00" if hoja else "#1d3c5c",
                bbox=dict(boxstyle="round,pad=0.35",
                          fc=COLOR_T if hoja else COLOR_NT,
                          ec=BORDE_T if hoja else BORDE_NT, lw=1.2))
        for h in nodo.hijos:
            nodos(h)

    aristas(raiz)
    nodos(raiz)
    ax.set_xlim(-sep_x * 0.7, (num_hojas - 1) * sep_x + sep_x * 0.7)
    ax.set_ylim(-prof * sep_y - 0.6, 0.6)
    ax.axis("off")
    if titulo:
        ax.set_title(titulo, fontsize=12, pad=12)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)


#  tabla CYK

def _partir(simbolos, por_linea=2):
    simbolos = sorted(simbolos)
    if not simbolos:
        return "∅"
    filas = [", ".join(simbolos[i:i + por_linea]) for i in range(0, len(simbolos), por_linea)]
    return "\n".join(filas)


def dibujar_tabla(resultado, inicial, ruta, titulo=""):
    """
    Tabla triangular clasica: columna = posicion inicial, fila = longitud.
    La fila de abajo (l = 1) esta sobre las palabras; la celda de arriba (l = n)
    decide la respuesta y se pinta verde (SI) o roja (NO).
    """
    tokens = resultado.tokens
    n = len(tokens)
    if n == 0:
        return
    ancho_celda = 1.7
    alto_celda = 1.0
    max_lineas = max(_partir(resultado.tabla[l][i]).count("\n") + 1
                     for l in range(1, n + 1) for i in range(n - l + 1))
    alto_celda = max(alto_celda, 0.45 * max_lineas + 0.3)

    fig, ax = plt.subplots(figsize=(max(5, n * ancho_celda * 0.8 + 1.5),
                                    max(3, n * alto_celda * 0.8 + 1.5)))
    for l in range(1, n + 1):
        for i in range(n - l + 1):
            x, y = i * ancho_celda, (l - 1) * alto_celda
            celda = resultado.tabla[l][i]
            if l == n:
                fc, ec = (COLOR_OK, BORDE_OK) if resultado.aceptada else (COLOR_NO, BORDE_NO)
            else:
                fc, ec = ("#ffffff" if celda else "#f2f2f2"), "#888888"
            ax.add_patch(Rectangle((x, y), ancho_celda, alto_celda, fc=fc, ec=ec, lw=1.2))
            texto = _partir(celda)
            negrita = inicial in celda
            ax.text(x + ancho_celda / 2, y + alto_celda / 2, texto, ha="center", va="center",
                    fontsize=9, color="#222222" if celda else "#aaaaaa",
                    fontweight="bold" if negrita else "normal")
    # palabras debajo de la primera fila
    for i, t in enumerate(tokens):
        ax.text(i * ancho_celda + ancho_celda / 2, -0.35, t, ha="center", va="center",
                fontsize=10, fontstyle="italic", color="#5a3e00")
    # etiquetas de longitud a la izquierda
    for l in range(1, n + 1):
        ax.text(-0.25, (l - 1) * alto_celda + alto_celda / 2, f"l={l}", ha="right",
                va="center", fontsize=9, color="#555555")
    ax.set_xlim(-0.9, n * ancho_celda + 0.1)
    ax.set_ylim(-0.7, n * alto_celda + 0.1)
    ax.set_aspect("auto")
    ax.axis("off")
    if titulo:
        ax.set_title(titulo, fontsize=12, pad=10)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
