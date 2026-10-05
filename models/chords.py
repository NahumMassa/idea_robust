"""
Parser de cifrado americano por compases, compatible con ChordPro.

Entrada (text_area del admin), con o sin corchetes:

    VERSO
    | G | C G | E- D | C |

    {c: PRE-CORO}
    | [C] | [D] | [Em] [E-], [D] | [C] |

Se guarda normalizado en ChordPro (secciones como {c: ...}, acordes entre
corchetes, menores con '-'):

    {c: VERSO}
    | [G] | [C] [G] | [E-] [D] | [C] |
"""

import re
from dataclasses import dataclass, field

NOTES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTES_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
NOTE_INDEX = {n: i for i, n in enumerate(NOTES_SHARP)} | {n: i for i, n in enumerate(NOTES_FLAT)}
NOTE_INDEX |= {"Cb": 11, "Fb": 4, "E#": 5, "B#": 0}

# tonos que se escriben con sostenidos; el resto (incluido C y A-) con bemoles
SHARP_MAJOR_KEYS = {"G", "D", "A", "E", "B", "F#", "C#"}
SHARP_MINOR_KEYS = {"E", "B", "F#", "C#", "G#", "D#", "A#"}

REPEAT_BAR = "%"  # repetir el compás anterior

_EXT = r"(?:maj|add|sus|[b#])?\d{1,2}"
CHORD_RE = re.compile(
    r"^(?P<root>[A-G][#b]?)"
    r"(?P<quality>maj|min|m(?!aj)|-|dim|°|ø|aug|\+)?"
    rf"(?P<ext>(?:{_EXT}|sus|alt|\({_EXT}(?:,\s?{_EXT})*\))*)"
    r"(?:/(?P<bass>[A-G][#b]?))?$"
)
DIRECTIVE_RE = re.compile(r"^\{\s*(?:c|comment|ci|comment_italic)\s*:\s*(?P<name>.*?)\s*\}$", re.IGNORECASE)


@dataclass
class Section:
    name: str | None
    rows: list[list[list[str]]] = field(default_factory=list)  # fila -> compases -> acordes


def normalize_chord(token: str) -> str:
    """'Em7' -> 'E-7', 'Bbmaj7/D' -> 'Bbmaj7/D'. Lanza ValueError si no es un acorde."""
    match = CHORD_RE.match(token)
    if not match:
        raise ValueError(f"acorde inválido '{token}'")
    quality = match["quality"] or ""
    if quality in ("m", "min"):
        quality = "-"
    bass = f"/{match['bass']}" if match["bass"] else ""
    return f"{match['root']}{quality}{match['ext']}{bass}"


def _parse_bar(bar: str) -> list[str]:
    # los corchetes son opcionales y la coma se pega al acorde anterior ("E-, D")
    raw = bar.replace("[", " ").replace("]", " ").replace(",", " , ").split()
    tokens = []
    for tok in raw:
        if tok == ",":
            if not tokens:
                raise ValueError("coma sin acorde antes")
            tokens[-1] += ","
        elif tok == REPEAT_BAR:
            tokens.append(tok)
        else:
            tokens.append(normalize_chord(tok))
    return tokens


def _is_chord_line(line: str) -> bool:
    tokens = line.replace("[", " ").replace("]", " ").replace(",", " ").split()
    return bool(tokens) and all(CHORD_RE.match(t) for t in tokens)


def parse_chart(text: str) -> list[Section]:
    """Convierte el texto en secciones. Lanza ValueError indicando la línea con error."""
    sections: list[Section] = []
    for n, line in enumerate((text or "").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            if "|" in line:
                # se ignoran los segmentos vacíos para tolerar "||" y barras en los extremos
                bars = [_parse_bar(seg) for seg in line.split("|") if seg.strip()]
                if not bars:
                    continue
                if not sections:
                    sections.append(Section(name=None))
                sections[-1].rows.append(bars)
            elif directive := DIRECTIVE_RE.match(line):
                sections.append(Section(name=directive["name"].upper()))
            elif _is_chord_line(line):
                raise ValueError("faltan las barras '|' para separar los compases")
            else:
                sections.append(Section(name=line.rstrip(":").strip().upper()))
        except ValueError as e:
            raise ValueError(f"Línea {n}: {e}") from None
    return sections


def _render(sections: list[Section], brackets: bool) -> str:
    def fmt(tok: str) -> str:
        if not brackets or tok == REPEAT_BAR:
            return tok
        chord, comma = (tok[:-1], ",") if tok.endswith(",") else (tok, "")
        return f"[{chord}]{comma}"

    blocks = []
    for section in sections:
        lines = [f"{{c: {section.name}}}" if brackets else section.name] if section.name else []
        for row in section.rows:
            lines.append("| " + " | ".join(" ".join(fmt(t) for t in bar) for bar in row) + " |")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def to_chordpro(sections: list[Section]) -> str:
    return _render(sections, brackets=True)


def to_plain(sections: list[Section]) -> str:
    """Formato rápido de escribir/leer, sin corchetes."""
    return _render(sections, brackets=False)


def normalize_chords(text: str) -> str:
    """Valida el texto y lo devuelve en ChordPro normalizado (lo que se guarda en la db)."""
    return to_chordpro(parse_chart(text))


def parse_tone(tone: str) -> tuple[int, bool]:
    """'E-' / 'Em' / 'C#-' -> (índice de la nota, es_menor)."""
    tone = tone.strip()
    minor = tone.endswith("-") or (tone.endswith("m") and len(tone) > 1)
    root = tone.rstrip("-m") if minor else tone
    if root not in NOTE_INDEX:
        raise ValueError(f"tono inválido '{tone}'")
    return NOTE_INDEX[root], minor


def uses_flats(tone: str) -> bool:
    index, minor = parse_tone(tone)
    keys = SHARP_MINOR_KEYS if minor else SHARP_MAJOR_KEYS
    return not any(NOTE_INDEX[k] == index for k in keys)


def transpose_chord(token: str, semitones: int, flats: bool) -> str:
    if token == REPEAT_BAR:
        return token
    chord, comma = (token[:-1], ",") if token.endswith(",") else (token, "")
    match = CHORD_RE.match(chord)
    if not match:
        raise ValueError(f"acorde inválido '{chord}'")
    names = NOTES_FLAT if flats else NOTES_SHARP

    def shift(note: str) -> str:
        return names[(NOTE_INDEX[note] + semitones) % 12]

    bass = f"/{shift(match['bass'])}" if match["bass"] else ""
    return f"{shift(match['root'])}{match['quality'] or ''}{match['ext']}{bass}{comma}"


def transpose_sections(sections: list[Section], from_tone: str, to_tone: str) -> list[Section]:
    from_index, from_minor = parse_tone(from_tone)
    to_index, to_minor = parse_tone(to_tone)
    if from_minor != to_minor:
        raise ValueError("solo se puede transponer entre tonos del mismo modo (mayor/menor)")
    semitones = to_index - from_index
    flats = uses_flats(to_tone)
    return [
        Section(
            name=s.name,
            rows=[[[transpose_chord(t, semitones, flats) for t in bar] for bar in row] for row in s.rows],
        )
        for s in sections
    ]
