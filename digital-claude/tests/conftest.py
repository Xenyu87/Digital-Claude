"""Configurazione pytest: aggiunge `scripts/` al path per importare moduli."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
