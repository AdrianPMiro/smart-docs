"""
Detector (muy simple) de tipo de PDF para Smart-Docs.

✔  Extrae la primera línea *no vacía* del PDF y la imprime en consola
✔  Devuelve un string que indica el «tipo» del PDF según palabras clave
    - "electricity_invoice"  → si detecta factura de luz (Curenergía / “FACTURA DE ELECTRICIDAD”)
    - "unknown_pdf"          → si no coinciden las palabras clave
⚠️  Este detector es deliberadamente minimalista: añade o ajusta entradas
    en KEYWORDS_TO_KIND cuando tengas más documentos de ejemplo.
"""
from pathlib import Path
from typing import Tuple
import pdfplumber
import logging
import re

logging.getLogger("pdfminer").setLevel(logging.ERROR)

# --- Palabras / frases → tipo asignado
KEYWORDS_TO_KIND: Tuple[Tuple[str, str], ...] = (
    ("FACTURA DE ELECTRICIDAD", "electricity_invoice"),
    ("CURENERGÍA",              "electricity_invoice"),
    # Añade aquí ("otra palabra clave", "otro_tipo") según tus PDFs
)

def detect_pdf_data_type_by_first_line(pdf_path: Path) -> str:
    """
    • Imprime la primera línea (útil para que veas el contenido exacto)
    • Devuelve un string con el tipo detectado o 'unknown_pdf'
    """
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        print(f"[pdf_detector] ❌ Ruta inválida o no es PDF: {pdf_path}")
        return "invalid_pdf"

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            if not pdf.pages:
                print(f"[pdf_detector] ⚠️  PDF vacío: {pdf_path.name}")
                return "empty_pdf"

            first_page_text = pdf.pages[0].extract_text() or ""
    except Exception as e:
        print(f"[pdf_detector] ⚠️  Error al abrir PDF '{pdf_path.name}': {e}")
        return "pdf_read_error"

    # Coger la primera línea no vacía
    first_line = ""
    for line in first_page_text.splitlines():
        line = line.strip()
        if line:
            first_line = line
            break

    if not first_line:
        print(f"[pdf_detector] No se encontró texto en la primera página: {pdf_path.name}")
        return "no_text_found"

    # --- DEBUG: imprime la primera línea para que ajustes tus keywords
    print(f"\n[pdf_detector] ► Primera línea de '{pdf_path.name}':\n    {first_line}\n")

    # Normalizamos a mayúsculas para comparar
    first_page_upper = first_page_text.upper()

    for keyword, kind in KEYWORDS_TO_KIND:
        if re.search(keyword.upper(), first_page_upper):
            print(f"[pdf_detector] → Tipo detectado: '{kind}' (keyword: '{keyword}')")
            return kind

    print(f"[pdf_detector] → Tipo de PDF desconocido para '{pdf_path.name}'")
    return "unknown_pdf"
