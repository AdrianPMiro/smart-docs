"""
Detector para archivos DOCX de datos.

Extrae las primeras líneas no vacías del documento y las imprime
para que puedas ajustar las palabras clave de detección.
Devuelve un string representando el tipo de documento
según coincidencias de palabras clave.
"""
from pathlib import Path
from typing import Tuple
from docx import Document
import re

# Palabras clave para cada tipo de DOCX
KEYWORDS_TO_KIND: Tuple[Tuple[str, str], ...] = (
    ("SOLICITUD DE INSCRIPCIÓN", "solicitud_bt"),
    # Añade aquí ("otra palabra", "otro_tipo") según tus documentos
)

def detect_docx_data_type_by_first_lines(docx_path: Path) -> str:
    """Lee las primeras líneas y clasifica el DOCX."""
    if not docx_path.exists() or docx_path.suffix.lower() != ".docx":
        print(f"[docx_detector] ❌ Ruta inválida o no es DOCX: {docx_path}")
        return "invalid_docx"

    try:
        doc = Document(docx_path)
    except Exception as e:
        print(f"[docx_detector] ⚠️  Error al abrir DOCX '{docx_path.name}': {e}")
        return "docx_read_error"

    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
            if len(lines) >= 5:
                break

    first_lines = "\n".join(lines)
    if not first_lines:
        print(f"[docx_detector] No se encontró texto en el documento: {docx_path.name}")
        return "no_text_found"

    print(f"\n[docx_detector] ► Primeras líneas de '{docx_path.name}':\n    {first_lines}\n")

    text_upper = first_lines.upper()
    for keyword, kind in KEYWORDS_TO_KIND:
        if re.search(keyword.upper(), text_upper):
            print(f"[docx_detector] → Tipo detectado: '{kind}' (keyword: '{keyword}')")
            return kind

    print(f"[docx_detector] → Tipo de DOCX desconocido para '{docx_path.name}'")
    return "unknown_docx"
