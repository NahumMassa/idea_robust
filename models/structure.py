"""
Parser de la estructura lineal de una canción.

Cada parte se separa con '-', con o sin espacios, y se toleran guiones
sobrantes al inicio o al final:

    "in - v1 - PC - PC'[2] - C2(2) - BR(4) - OUT -"

Se guarda normalizado en mayúsculas y separado por " - ":

    "IN - V1 - PC - PC'[2] - C2(2) - BR(4) - OUT"
"""

import re

# nombre de la parte (IN, V, PC, C, BR, OUT...), número opcional, primas
# opcionales y repeticiones opcionales entre [] o (): V1, PC', C2(2), PC'[2]
PART_RE = re.compile(r"^[A-Z]+\d*'*(?:\[\d+\]|\(\d+\))?$")


def parse_structure(text: str) -> list[str]:
    """Devuelve las partes en orden. Lanza ValueError si alguna no tiene el formato."""
    parts = [p.strip().upper() for p in (text or "").split("-")]
    parts = [p for p in parts if p]
    for n, part in enumerate(parts, 1):
        if not PART_RE.match(part):
            raise ValueError(f"Parte {n}: '{part}' no es válida (ej. IN, V1, PC', C2(2), BR[4])")
    return parts


def normalize_structure(text: str) -> str:
    """Valida la estructura y la devuelve como se guarda en la db."""
    return " - ".join(parse_structure(text))
