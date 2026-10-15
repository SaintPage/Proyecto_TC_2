"""
Representacion de una gramatica libre de contexto (CFG) y lectura desde archivo.

Formato de archivo (igual que los ejemplos del curso):
    E -> T X
    X -> + T X | e
Cada simbolo va separado por espacios. "e" (o "ε") representa la cadena vacia.
El simbolo inicial es el lado izquierdo de la primera regla.
Las lineas vacias y las que empiezan con # se ignoran.
"""

EPSILON = {"e", "ε", "epsilon", "λ"}


class Gramatica:
    """
    producciones: dict  no_terminal -> lista de tuplas de simbolos
    La tupla vacia () representa la produccion epsilon.
    """

    def __init__(self, inicial, producciones):
        self.inicial = inicial
        self.producciones = {}
        for cabeza, cuerpos in producciones.items():
            # dict.fromkeys elimina duplicados conservando el orden
            self.producciones[cabeza] = list(dict.fromkeys(tuple(c) for c in cuerpos))
        # True si la cadena vacia pertenece al lenguaje (se decide al quitar ε)
        self.acepta_vacia = False

    @property
    def no_terminales(self):
        return set(self.producciones)

    @property
    def terminales(self):
        nts = self.no_terminales
        return {s for cuerpos in self.producciones.values()
                for cuerpo in cuerpos for s in cuerpo if s not in nts}

    def es_no_terminal(self, simbolo):
        return simbolo in self.producciones

    def copia(self):
        g = Gramatica(self.inicial, {a: list(c) for a, c in self.producciones.items()})
        g.acepta_vacia = self.acepta_vacia
        return g

    def num_producciones(self):
        return sum(len(c) for c in self.producciones.values())

    def es_cnf(self):
        """Verifica que toda produccion sea A -> B C o A -> a."""
        for cuerpos in self.producciones.values():
            for cuerpo in cuerpos:
                if len(cuerpo) == 1 and not self.es_no_terminal(cuerpo[0]):
                    continue
                if len(cuerpo) == 2 and all(self.es_no_terminal(s) for s in cuerpo):
                    continue
                return False
        return True

    def __str__(self):
        lineas = []
        for cabeza, cuerpos in self.producciones.items():
            alternativas = [" ".join(c) if c else "e" for c in cuerpos]
            lineas.append(f"{cabeza} -> {' | '.join(alternativas)}")
        return "\n".join(lineas)


def leer_gramatica(ruta):
    with open(ruta, encoding="utf-8") as f:
        return parsear_gramatica(f.read())


def parsear_gramatica(texto):
    producciones = {}
    inicial = None
    for num, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        linea = linea.replace("→", "->")
        if "->" not in linea:
            raise ValueError(f"Linea {num}: falta '->' en '{linea}'")
        cabeza, cuerpo = linea.split("->", 1)
        cabeza = cabeza.strip()
        if not cabeza or len(cabeza.split()) != 1:
            raise ValueError(f"Linea {num}: lado izquierdo invalido '{cabeza}'")
        if inicial is None:
            inicial = cabeza
        lista = producciones.setdefault(cabeza, [])
        for alternativa in cuerpo.split("|"):
            simbolos = alternativa.split()
            if not simbolos:
                raise ValueError(f"Linea {num}: alternativa vacia (use 'e' para epsilon)")
            if len(simbolos) == 1 and simbolos[0] in EPSILON:
                lista.append(())
            else:
                lista.append(tuple(s for s in simbolos if s not in EPSILON))
    if inicial is None:
        raise ValueError("La gramatica esta vacia")
    return Gramatica(inicial, producciones)


def guardar_gramatica(g, ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(str(g) + "\n")
