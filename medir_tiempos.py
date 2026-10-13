"""
Mide el tiempo del CYK en funcion de la longitud de la frase.
Ejecutar:  python medir_tiempos.py      (genera imagenes/tiempos_cyk.png)

Frases: "she eats a cake" + " with a fork" repetido k veces (todas aceptadas,
longitud n = 4 + 3k). Para cada n se toma la mediana de varias corridas.
"""

import os
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from gramatica import leer_gramatica
from cnf import a_cnf
from cyk import cyk, indices_gramatica, tokenizar

CORRIDAS = 15


def medir(max_k=20):
    g_cnf, _ = a_cnf(leer_gramatica("gramaticas/ingles.txt"))
    indices = indices_gramatica(g_cnf)
    filas = []
    for k in range(0, max_k + 1):
        frase = "she eats a cake" + " with a fork" * k
        tokens = tokenizar(frase, g_cnf.terminales)
        cyk(g_cnf, tokens, indices)  
        # calentamiento                   
        tiempos = [cyk(g_cnf, tokens, indices).tiempo for _ in range(CORRIDAS)]
        r = cyk(g_cnf, tokens, indices)
        filas.append((len(tokens), statistics.median(tiempos) * 1e3, r.aceptada))
    return filas


def graficar(filas, ruta):
    ns = [f[0] for f in filas]
    ms = [f[1] for f in filas]
    # referencia c * n^3 ajustada al ultimo punto
    c = ms[-1] / ns[-1] ** 3
    ref = [c * n ** 3 for n in ns]

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot(ns, ref, "--", color="#9a9a9a", lw=2, label="referencia  c · n³")
    ax.plot(ns, ms, "-o", color="#2f6db5", lw=2, ms=6, label="CYK medido (mediana)")
    ax.set_xlabel("longitud de la frase n (palabras)")
    ax.set_ylabel("tiempo (ms)")
    ax.set_title("Tiempo del algoritmo CYK vs longitud de la frase", fontsize=12)
    ax.grid(True, color="#e6e6e6", lw=0.8)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    filas = medir()
    print(f"{'n':>4}  {'tiempo (ms)':>12}  resultado")
    for n, ms, ok in filas:
        print(f"{n:>4}  {ms:>12.3f}  {'SÍ' if ok else 'NO'}")
    os.makedirs("imagenes", exist_ok=True)
    graficar(filas, os.path.join("imagenes", "tiempos_cyk.png"))
    print("Grafica: imagenes/tiempos_cyk.png")
