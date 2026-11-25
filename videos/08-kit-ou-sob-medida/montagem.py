"""Vídeo 08 — Kit pronto ou sob medida. Ver ferramentas/fabrica.py para o uso."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ferramentas"))
from fabrica import produzir  # noqa: E402

produzir(__file__)
