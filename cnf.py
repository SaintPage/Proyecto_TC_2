"""
Simplificacion de gramaticas y conversion a Forma Normal de Chomsky (CNF).

Pasos (en este orden):
  1. Eliminar producciones ε        (A -> e)
  2. Eliminar producciones unitarias (A -> B)
  3. Eliminar simbolos inutiles      (no generadores y luego no alcanzables)
  4. TERM: sustituir terminales dentro de cuerpos de longitud >= 2
  5. BIN:  partir cuerpos de longitud > 2 en cadenas de cuerpos binarios

Al terminar, toda produccion es de la forma A -> B C o A -> a.
Si el simbolo inicial era anulable, se marca g.acepta_vacia = True
(la CNF no puede representar ε, por eso se guarda aparte).
"""

from itertools import product

from gramatica import Gramatica


# Nombres legibles para no terminales nuevos que producen un simbolo terminal
NOMBRES_SIMBOLOS = {
    "(": "lpar", ")": "rpar", "[": "lcor", "]": "rcor", "{": "llave", "}": "rllave",
    "+": "mas", "-": "menos", "*": "por", "/": "div", "^": "pot", "=": "igual",
    ",": "coma", ";": "pyc", ".": "punto", ":": "dosp", "<": "menor", ">": "mayor",
    "|": "barra", "&": "y", "!": "neg", "?": "preg", "%": "mod",
}


#  paso 1: ε

def calcular_anulables(g):
    """Punto fijo: A es anulable si tiene un cuerpo formado solo por anulables."""
    anulables = set()
    cambio = True
    while cambio:
        cambio = False
        for cabeza, cuerpos in g.producciones.items():
            if cabeza in anulables:
                continue
            if any(all(s in anulables for s in cuerpo) for cuerpo in cuerpos):
                anulables.add(cabeza)
                cambio = True
    return anulables


def eliminar_epsilon(g):
    anulables = calcular_anulables(g)
    nuevas = {}
    for cabeza, cuerpos in g.producciones.items():
        lista = []
        for cuerpo in cuerpos:
            # Cada simbolo anulable puede quedarse o desaparecer: 2^k combinaciones
            opciones = [((s,), ()) if s in anulables else ((s,),) for s in cuerpo]
            for eleccion in product(*opciones):
                nuevo = tuple(s for parte in eleccion for s in parte)
                if nuevo:                      # se descartan los cuerpos vacios
                    lista.append(nuevo)
        nuevas[cabeza] = lista
    r = Gramatica(g.inicial, nuevas)
    r.acepta_vacia = g.acepta_vacia or g.inicial in anulables
    return r, anulables


#  paso 2: unitarias

def pares_unitarios(g):
    """Para cada A, conjunto de B tales que A =>* B usando solo reglas unitarias."""
    pares = {}
    for a in g.producciones:
        alcanzados = [a]                       # lista para conservar orden BFS
        i = 0
        while i < len(alcanzados):
            x = alcanzados[i]
            i += 1
            for cuerpo in g.producciones.get(x, []):
                if len(cuerpo) == 1 and g.es_no_terminal(cuerpo[0]) and cuerpo[0] not in alcanzados:
                    alcanzados.append(cuerpo[0])
        pares[a] = alcanzados
    return pares


def eliminar_unitarias(g):
    pares = pares_unitarios(g)
    nuevas = {}
    for a, alcanzados in pares.items():
        lista = []
        for b in alcanzados:                   # incluye (A, A)
            for cuerpo in g.producciones[b]:
                if not (len(cuerpo) == 1 and g.es_no_terminal(cuerpo[0])):
                    lista.append(cuerpo)
        nuevas[a] = lista
    r = Gramatica(g.inicial, nuevas)
    r.acepta_vacia = g.acepta_vacia
    return r, {a: [b for b in al if b != a] for a, al in pares.items()}


#  paso 3: inutiles

def calcular_generadores(g):
    generadores = set()
    cambio = True
    while cambio:
        cambio = False
        for cabeza, cuerpos in g.producciones.items():
            if cabeza in generadores:
                continue
            for cuerpo in cuerpos:
                if all((not g.es_no_terminal(s)) or s in generadores for s in cuerpo):
                    generadores.add(cabeza)
                    cambio = True
                    break
    return generadores


def calcular_alcanzables(g):
    alcanzables = {g.inicial}
    pila = [g.inicial]
    while pila:
        x = pila.pop()
        for cuerpo in g.producciones.get(x, []):
            for s in cuerpo:
                if g.es_no_terminal(s) and s not in alcanzables:
                    alcanzables.add(s)
                    pila.append(s)
    return alcanzables


def eliminar_inutiles(g):
    # 3a. quitar no generadores (y toda produccion que los use)
    generadores = calcular_generadores(g)
    nts = g.no_terminales
    nuevas = {}
    for cabeza, cuerpos in g.producciones.items():
        if cabeza not in generadores and cabeza != g.inicial:
            continue
        nuevas[cabeza] = [c for c in cuerpos
                          if all(s not in nts or s in generadores for s in c)]
    g1 = Gramatica(g.inicial, nuevas)
    g1.acepta_vacia = g.acepta_vacia

    # 3b. quitar no alcanzables desde el simbolo inicial
    alcanzables = calcular_alcanzables(g1)
    g2 = Gramatica(g.inicial, {a: c for a, c in g1.producciones.items() if a in alcanzables})
    g2.acepta_vacia = g.acepta_vacia

    no_generadores = sorted(nts - generadores)
    no_alcanzables = sorted(set(g1.producciones) - alcanzables)
    return g2, no_generadores, no_alcanzables


#  pasos 4 y 5: TERM, BIN

class GeneradorNombres:
    def __init__(self, usados):
        self.usados = set(usados)
        self.contador = 0

    def _reservar(self, nombre):
        base, n = nombre, 2
        while nombre in self.usados:
            nombre = f"{base}{n}"
            n += 1
        self.usados.add(nombre)
        return nombre

    def para_terminal(self, t):
        sufijo = t if t.isalnum() else NOMBRES_SIMBOLOS.get(t, "sim")
        return self._reservar(f"T_{sufijo}")

    def para_cadena(self):
        while True:
            self.contador += 1
            nombre = f"C{self.contador}"
            if nombre not in self.usados:
                self.usados.add(nombre)
                return nombre


def term(g, nombres):
    """Cada terminal a que aparece en un cuerpo largo se reemplaza por T_a -> a."""
    # Reutiliza un no terminal ya existente cuya UNICA produccion sea A -> a
    para_terminal = {}
    for cabeza, cuerpos in g.producciones.items():
        if cabeza != g.inicial and len(cuerpos) == 1 and len(cuerpos[0]) == 1 \
                and not g.es_no_terminal(cuerpos[0][0]):
            para_terminal.setdefault(cuerpos[0][0], cabeza)

    nuevas = {a: [] for a in g.producciones}
    agregados = {}
    for cabeza, cuerpos in g.producciones.items():
        for cuerpo in cuerpos:
            if len(cuerpo) >= 2:
                nuevo = []
                for s in cuerpo:
                    if g.es_no_terminal(s):
                        nuevo.append(s)
                    else:
                        if s not in para_terminal:
                            nt = nombres.para_terminal(s)
                            para_terminal[s] = nt
                            agregados[nt] = [(s,)]
                        nuevo.append(para_terminal[s])
                cuerpo = tuple(nuevo)
            nuevas[cabeza].append(cuerpo)
    nuevas.update(agregados)
    r = Gramatica(g.inicial, nuevas)
    r.acepta_vacia = g.acepta_vacia
    return r


def binarizar(g, nombres):
    """A -> X1 X2 ... Xn (n > 2)  se convierte en  A -> X1 C,  C -> X2 ... Xn (recursivo)."""
    nuevas = {a: [] for a in g.producciones}
    agregados = {}
    # sufijo:no terminal que lo genera
    memo = {}                                  

    def nt_para(sufijo):
        if sufijo not in memo:
            nt = nombres.para_cadena()
            memo[sufijo] = nt
            if len(sufijo) == 2:
                agregados[nt] = [sufijo]
            else:
                agregados[nt] = [(sufijo[0], nt_para(sufijo[1:]))]
        return memo[sufijo]

    for cabeza, cuerpos in g.producciones.items():
        for cuerpo in cuerpos:
            if len(cuerpo) > 2:
                cuerpo = (cuerpo[0], nt_para(cuerpo[1:]))
            nuevas[cabeza].append(cuerpo)
    # Los nuevos se agregan en orden de creacion
    for nt in sorted(agregados, key=lambda x: int(x[1:]) if x[1:].isdigit() else 0):
        nuevas[nt] = agregados[nt]
    r = Gramatica(g.inicial, nuevas)
    r.acepta_vacia = g.acepta_vacia
    return r


#  todo junto

def a_cnf(g):
    """
    Devuelve (gramatica_cnf, pasos) donde pasos es una lista de
    (titulo, gramatica, detalle) para poder mostrar la simplificacion paso a paso.
    """
    pasos = [("Gramatica original", g, "")]

    g1, anulables = eliminar_epsilon(g)
    detalle = "Anulables: { " + ", ".join(sorted(anulables)) + " }" if anulables else "No hay simbolos anulables"
    if g1.acepta_vacia:
        detalle += f"\n{g.inicial} es anulable: ε pertenece al lenguaje (se marca aparte)"
    pasos.append(("1. Eliminacion de producciones ε", g1, detalle))

    g2, pares = eliminar_unitarias(g1)
    lineas = [f"{a} =>* {', '.join(bs)}" for a, bs in pares.items() if bs]
    detalle = "Pares unitarios:\n" + "\n".join(lineas) if lineas else "No hay producciones unitarias"
    pasos.append(("2. Eliminacion de producciones unitarias", g2, detalle))

    g3, no_gen, no_alc = eliminar_inutiles(g2)
    detalle = ("No generadores: { " + ", ".join(no_gen) + " }\n" if no_gen else "Todos son generadores\n")
    detalle += ("No alcanzables: { " + ", ".join(no_alc) + " }" if no_alc else "Todos son alcanzables")
    pasos.append(("3. Eliminacion de simbolos inutiles", g3, detalle))

    nombres = GeneradorNombres(g3.no_terminales | g3.terminales | set(g.producciones))
    g4 = term(g3, nombres)
    nuevos = sorted(g4.no_terminales - g3.no_terminales)
    detalle = "Nuevos: " + ", ".join(f"{n} -> {g4.producciones[n][0][0]}" for n in nuevos) if nuevos \
        else "No hay terminales en cuerpos de longitud >= 2"
    pasos.append(("4. TERM: terminales en cuerpos largos", g4, detalle))

    g5 = binarizar(g4, nombres)
    nuevos = [n for n in g5.producciones if n not in g4.producciones]
    detalle = "Nuevos: " + ", ".join(f"{n} -> {' '.join(g5.producciones[n][0])}" for n in nuevos) if nuevos \
        else "Todos los cuerpos ya tenian longitud <= 2"
    pasos.append(("5. BIN: cuerpos de longitud > 2", g5, detalle))

    assert g5.es_cnf(), "La gramatica resultante no esta en CNF"
    return g5, pasos
