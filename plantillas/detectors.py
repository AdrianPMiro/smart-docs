# -*- coding: utf-8 -*-
"""
Detección de tipo de fichero + debug de primera línea.
Siempre imprime la primera línea “útil” (sin saltos ni tags XML).
"""

from pathlib import Path
import re, zipfile, pdfplumber

# -------------------------------------------------------------------
# Utilidades internas
# -------------------------------------------------------------------
def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if clean:
            return clean
    return ""

def _read_pdf_text(path: Path, chars=3000) -> str:
    with pdfplumber.open(str(path)) as pdf:
        txt = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return txt[:chars]

def _read_docx_xml(path: Path, chars=4000) -> str:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode(errors="ignore")
    # quitar tags XML rápidos para la primera línea
    xml_no_tags = re.sub(r"<[^>]+>", " ", xml)
    return xml_no_tags[:chars]

# -------------------------------------------------------------------
# Detectores
# -------------------------------------------------------------------
def detect_data_type(pdf_path: Path) -> str:
    txt   = _read_pdf_text(pdf_path)
    first = _first_nonempty_line(txt)
    print(f"[detect_data_type] 1ª línea PDF → {first!r}")

    up = txt.upper()
    if "IMPORTE FACTURA" in up and "CURENERGÍA" in up:
        return "electricity_invoice"
    if "PROPUESTA DE INSTALACIÓN" in up and "PUNTO DE RECARGA" in up:
        return "budget_proposal"
    return "unknown_pdf"

def detect_template_type(tpl_path: Path) -> str:
    ext = tpl_path.suffix.lower()
    if ext in (".xls", ".xlsx"):
        print(f"[detect_template_type] 1ª línea EXCEL → <no text preview>")  # Excel preview no implementado
        return "budget_excel"

    xml  = _read_docx_xml(tpl_path)
    first = _first_nonempty_line(xml)
    print(f"[detect_template_type] 1ª línea DOCX → {first!r}")

    up = xml.upper()
    if "ANEXO IVE" in up or "ESQUEMA 4A" in up:
        return "anexo_ive"
    if "MEMORIA TÉCNICA DE DISEÑO" in up or "INFRAESTRUCTURA PARA PUNTO RECARGA" in up:
        return "mtd_unifilar"
    if "SOLICITUD DE INSCRIPCIÓN DE DOCUMENTACIÓN" in up and "BT" in up:
        return "solicitud_bt"
    return "unknown_tpl"
