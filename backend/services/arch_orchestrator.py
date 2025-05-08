# backend/services/arch_orchestrator.py

from pathlib import Path
from typing import Dict
from backend.readers.excel_reader import excel_reader
from backend.readers.docx_reader import docx_reader
from backend.readers.pdf_reader import pdf_reader
from backend.generators.excel_generator import excel_generator
from backend.generators.docx_generator import docx_generator
from backend.generators.pdf_generator import pdf_generator


def arch_orchestrator(
    plantilla_path: Path,
    datos_path:     Path,
    salida_path:    Path
) -> None:
    # --- 1) Leer datos ---
    ext_datos = datos_path.suffix.lower()
    if ext_datos in ('.xls', '.xlsx'):
        datos: Dict[str,str] = excel_reader(datos_path)
    elif ext_datos == '.docx':
        datos = docx_reader(datos_path)
    elif ext_datos == '.pdf':
        datos = pdf_reader(datos_path)
    else:
        raise ValueError(f"[arch_orchestrator] Formato de datos no soportado: {ext_datos}")

    # --- 2) Generar salida ---
    ext_tpl = plantilla_path.suffix.lower()

    # Aseguramos que el directorio padre de salida existe
    salida_path.parent.mkdir(parents=True, exist_ok=True)

    if ext_tpl == '.docx':
        docx_generator(plantilla_path, salida_path, datos)
    elif ext_tpl in ('.xls', '.xlsx'):
        excel_generator(datos, plantilla_path, salida_path)
    elif ext_tpl == '.pdf':
        # pdf_generator devuelve True/False si quieres controlar el flujo
        success = pdf_generator(plantilla_path, salida_path, datos)
        if not success:
            raise RuntimeError(f"[arch_orchestrator] pdf_generator falló para {plantilla_path}")
    else:
        raise ValueError(f"[arch_orchestrator] Formato de plantilla no soportado: {ext_tpl}")
