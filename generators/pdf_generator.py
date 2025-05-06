


from pathlib import Path
from typing import Dict

def pdf_generator(plantilla: Path, salida: Path, reemplazos: Dict[str, str]) -> None:
    print("Generando excel...")