# generador/lector_excel.py
import xlrd, unicodedata, re
from typing import Dict

def _norm(text: str) -> str:
    """Minimiza una cadena: minúsculas, sin acentos, sin espacios extra."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]", " ", text.lower())  # quita signos
    return re.sub(r"\s+", " ", text).strip()

def _buscar_valor(ws, patron: str, ancho: int = 5) -> str:

    patron = _norm(patron)
    for r in range(ws.nrows):
        for c in range(ws.ncols - 1):
            raw = ws.cell_value(r, c)
            if not isinstance(raw, str):
                continue
            if patron in _norm(raw):
                # avanzar hacia la derecha hasta encontrar valor
                for k in range(1, ancho + 1):
                    val = ws.cell_value(r, c + k)
                    if val not in ("", None):
                        return str(val).strip()
    return ""

def extraer_datos_excel(path: str) -> Dict[str, str]:
    wb = xlrd.open_workbook(path)
    ws = wb.sheet_by_index(0)

    datos = {
        "nif"      : _buscar_valor(ws, "nif"),
        "nombre"   : _buscar_valor(ws, "nombre razon social"),
        "apellido1": _buscar_valor(ws, "primer apellido"),
        "apellido2": _buscar_valor(ws, "segundo apellido"),
        "tipo_via" : _buscar_valor(ws, "tipo via"),
        "nom_via"  : _buscar_valor(ws, "nombre via"),
        "numero"   : _buscar_valor(ws, "movil"),
        "cp"       : _buscar_valor(ws, "cp"),
        "localidad": _buscar_valor(ws, "localidad"),
    }

    # construimos algunos campos combinados
    datos["direccion"] = f"{datos['tipo_via']} {datos['nom_via']} "
    return datos
