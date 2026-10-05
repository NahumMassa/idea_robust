"""
Tests for models/chords.py (sin db ni Streamlit).

Run with:
    venv/bin/python -m pytest models/tests/test_chords.py -v
"""

import importlib.util
from pathlib import Path
import pytest

_chords_path = Path(__file__).resolve().parent.parent / "chords.py"
spec = importlib.util.spec_from_file_location("chords_module", _chords_path)
chords = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chords)


EXAMPLE = """VERSO
| G | C G | E- D | C |

PRE-CORO
| C | D | E- E-, D | C |
| A |"""

EXPECTED = """{c: VERSO}
| [G] | [C] [G] | [E-] [D] | [C] |

{c: PRE-CORO}
| [C] | [D] | [E-] [E-], [D] | [C] |
| [A] |"""


class TestNormalizeChord:
    @pytest.mark.parametrize("raw, expected", [
        ("G", "G"),
        ("Em", "E-"),
        ("E-", "E-"),
        ("F#m7", "F#-7"),
        ("Cmin7", "C-7"),
        ("Bbmaj7", "Bbmaj7"),
        ("Cmmaj7", "C-maj7"),
        ("D/F#", "D/F#"),
        ("Am7/G", "A-7/G"),
        ("Gsus4", "Gsus4"),
        ("C7b9", "C7b9"),
        ("Cadd9", "Cadd9"),
        ("Bdim", "Bdim"),
        ("B°7", "B°7"),
        ("C9(#11)", "C9(#11)"),
    ])
    def test_valid(self, raw, expected):
        assert chords.normalize_chord(raw) == expected

    @pytest.mark.parametrize("raw", ["H", "c", "Gx", "I", "vi", "G/H", ""])
    def test_invalid(self, raw):
        with pytest.raises(ValueError):
            chords.normalize_chord(raw)


class TestParseChart:
    def test_example_to_chordpro(self):
        assert chords.normalize_chords(EXAMPLE) == EXPECTED

    def test_brackets_and_m_are_tolerated(self):
        text = "{c: verso}\n| [G] | [C][G] | [Em] [D] | [C] |"
        assert chords.normalize_chords(text) == "{c: VERSO}\n| [G] | [C] [G] | [E-] [D] | [C] |"

    def test_idempotent(self):
        assert chords.normalize_chords(EXPECTED) == EXPECTED

    def test_round_trip_plain(self):
        assert chords.to_plain(chords.parse_chart(EXPECTED)) == EXAMPLE

    def test_header_colon_and_double_bars(self):
        sections = chords.parse_chart("Coro:\n|| G | % ||")
        assert sections[0].name == "CORO"
        assert sections[0].rows == [[["G"], ["%"]]]

    def test_bars_without_section(self):
        assert chords.normalize_chords("| G | C |") == "| [G] | [C] |"

    def test_empty(self):
        assert chords.normalize_chords("") == ""
        assert chords.normalize_chords("  \n\n") == ""

    def test_invalid_chord_reports_line(self):
        with pytest.raises(ValueError, match="Línea 2: acorde inválido 'H7'"):
            chords.parse_chart("VERSO\n| G | H7 |")

    def test_chords_without_bars(self):
        with pytest.raises(ValueError, match="faltan las barras"):
            chords.parse_chart("VERSO\nG C D")

    def test_leading_comma(self):
        with pytest.raises(ValueError, match="Línea 1"):
            chords.parse_chart("| , G |")


class TestTranspose:
    def test_tone_parsing(self):
        assert chords.parse_tone("E-") == (4, True)
        assert chords.parse_tone("Em") == (4, True)
        assert chords.parse_tone("C#-") == (1, True)
        assert chords.parse_tone("Bb") == (10, False)

    def test_g_to_a_uses_sharps(self):
        sections = chords.transpose_sections(chords.parse_chart(EXAMPLE), "G", "A")
        assert chords.to_plain(sections).splitlines()[1] == "| A | D A | F#- E | D |"

    def test_g_to_f_uses_flats(self):
        sections = chords.transpose_sections(chords.parse_chart("| G | C | D/F# |"), "G", "F")
        assert chords.to_plain(sections) == "| F | Bb | C/E |"

    def test_keeps_comma_and_repeat(self):
        sections = chords.transpose_sections(chords.parse_chart("| E-, D | % |"), "E-", "F#-")
        assert chords.to_plain(sections) == "| F#-, E | % |"

    def test_mode_mismatch(self):
        with pytest.raises(ValueError):
            chords.transpose_sections(chords.parse_chart("| G |"), "G", "E-")
