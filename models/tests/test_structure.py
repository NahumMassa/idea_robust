"""
Tests for models/structure.py (sin db ni Streamlit).

Run with:
    venv/bin/python -m pytest models/tests/test_structure.py -v
"""

import importlib.util
from pathlib import Path
import pytest

_structure_path = Path(__file__).resolve().parent.parent / "structure.py"
spec = importlib.util.spec_from_file_location("structure_module", _structure_path)
structure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(structure)


class TestParseStructure:
    def test_example_with_trailing_dash(self):
        assert structure.parse_structure("C1 - V1 -") == ["C1", "V1"]

    def test_without_spaces(self):
        assert structure.parse_structure("IN-V1-PC-C") == ["IN", "V1", "PC", "C"]

    def test_full_placeholder(self):
        text = "IN - V1 - PC - PC - C - V - PC'[2] - C2(2) - BR(4) - C - C - OUT"
        assert structure.parse_structure(text) == [
            "IN", "V1", "PC", "PC", "C", "V", "PC'[2]", "C2(2)", "BR(4)", "C", "C", "OUT",
        ]

    def test_lowercase_and_extra_dashes(self):
        assert structure.parse_structure("- in --  v1 - pc' -") == ["IN", "V1", "PC'"]

    def test_empty(self):
        assert structure.parse_structure("") == []
        assert structure.parse_structure(" - ") == []

    @pytest.mark.parametrize("text", ["IN - V 1", "IN - V1[", "IN - C(2", "IN - 1V", "IN - V1 x2"])
    def test_invalid(self, text):
        with pytest.raises(ValueError, match="Parte 2"):
            structure.parse_structure(text)


class TestNormalizeStructure:
    def test_normalized(self):
        assert structure.normalize_structure("c1-v1 -  br(4)-") == "C1 - V1 - BR(4)"

    def test_idempotent(self):
        text = "IN - V1 - PC'[2] - OUT"
        assert structure.normalize_structure(text) == text
