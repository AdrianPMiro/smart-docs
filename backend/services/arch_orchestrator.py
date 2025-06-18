# backend/services/arch_orchestrator.py
from pathlib import Path

# --- readers / generators ---
from backend.readers.pdf_reader          import pdf_reader
from backend.generators.docx_generator   import docx_generator
from backend.generators.excel_generator  import excel_generator

# --- detectores ---
from backend.services.docx_template_detector import detect_docx_template_type

# --- extensiones permitidas ---
DATA_EXTS_ALLOWED     = {".pdf"}
TEMPLATE_EXTS_ALLOWED = {".docx", ".xlsx"}   # Word y Excel

def arch_orchestrator(datos_path: Path, plantilla_path: Path, salida_path: Path) -> dict:
    """Procesa un PDF y genera un documento final usando una plantilla DOCX o XLSX."""

    print(f"[arch_orchestrator] Recibidos: datos='{datos_path.name}', plantilla='{plantilla_path.name}'")

    # 1) Validación de extensiones
    ext_datos = datos_path.suffix.lower()
    ext_tpl   = plantilla_path.suffix.lower()

    if ext_datos not in DATA_EXTS_ALLOWED:
        raise ValueError(f"El archivo de datos debe ser PDF (recibido {ext_datos}).")
    if ext_tpl not in TEMPLATE_EXTS_ALLOWED:
        raise ValueError(f"La plantilla debe ser DOCX o XLSX (recibido {ext_tpl}).")

    # 2) Detección de sub-tipo
    data_kind = detect_pdf_data_type_by_first_line(datos_path)                 # siempre PDF
    tpl_kind  = detect_docx_template_type(plantilla_path) if ext_tpl == ".docx" else "excel_tpl"

    print(f"==> [arch_orchestrator] Tipo de DATOS:     '{data_kind}'")
    print(f"==> [arch_orchestrator] Tipo de PLANTILLA: '{tpl_kind}'")

    # 3) Lectura de datos (PDF → dict)
    datos = pdf_reader(datos_path)

    # 4) Generación según el tipo de plantilla
    if ext_tpl == ".docx":
        docx_generator(plantilla_path, salida_path, datos)
    else:  # ".xlsx"
        excel_generator(plantilla_path, salida_path, datos)

    if not salida_path.exists():
        raise RuntimeError(f"[arch_orchestrator] No se creó el archivo '{salida_path.name}'")

    # 5) Devolver metadatos útiles
    return {
        "detected_data_type":     data_kind,
        "detected_template_type": tpl_kind,
        "output_path":            str(salida_path)
    }
