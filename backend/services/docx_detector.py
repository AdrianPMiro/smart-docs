"""
Detector de plantillas DOCX
---------------------------
Imprime las primeras líneas y devuelve el tipo de plantilla.

Las keywords son UNA sola frase (o palabra) que sabemos que no cambiará.
"""
from pathlib import Path
from typing import Tuple
from docx import Document
import re

# --------- Frase clave (mayúsculas/ minúsculas da igual) → tipo ----------
KEYWORDS_TO_KIND: Tuple[Tuple[str, str], ...] = (
    # Plantilla 1: “MTD + UNIFILAR Monofásico…”
    ("DIRECCIÓN GENERAL DE INDUSTRIA, ENERGÍA Y MINAS", "tpl_unifilar_monofasico"),

    # Plantilla 2: “NUEVA SOLICITUD_BT_GENERICA…”
    ("1.- DATOS DEL TITULAR DE LA INSTALACIÓN",          "tpl_solicitud_bt"),

    # Si tuvieras un tercer DOCX métele aquí su frase estable:
    # ("OTRA FRASE FIJA", "tpl_otro"),
)

def detect_docx_template_type(docx_path: Path) -> str:
    if not docx_path.exists() or docx_path.suffix.lower() != ".docx":
        print(f"[docx_detector] ❌ No es DOCX o no existe: {docx_path}")
        return "invalid_docx"

    try:
        doc = Document(docx_path)
    except Exception as e:
        print(f"[docx_detector] ⚠️  Error abriendo '{docx_path.name}': {e}")
        return "docx_open_error"

    # Tomamos las primeras 5 líneas no vacías
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()][:5]
    first_lines = "\n".join(lines)

    if not first_lines:
        print(f"[docx_detector] Documento vacío: {docx_path.name}")
        return "no_text_found"

    print(f"\n[docx_detector] ► Primeras líneas de '{docx_path.name}':")
    for ln in lines:
        print("   ", ln)
    print()

    upper = first_lines.upper()
    for kw, kind in KEYWORDS_TO_KIND:
        if kw.upper() in upper:
            print(f"[docx_detector] → Tipo detectado: '{kind}' (kw='{kw}')")
            return kind

    print(f"[docx_detector] → Tipo de DOCX desconocido para '{docx_path.name}'")
    return "unknown_docx"
