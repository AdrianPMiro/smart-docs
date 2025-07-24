from pathlib import Path

# readers
from readers.pdf_reader import pdf_reader

# generators
from generators.excel_generator import excel_generator
from generators.docx_generator  import docx_generator

# detectores (si los usas)
from services.docx_detector import detect_docx_template_type

# Extensiones permitidas
DATA_EXTS_ALLOWED     = {".pdf"}
TEMPLATE_EXTS_ALLOWED = {".docx", ".xls", ".xlsx"}

def arch_orchestrator(datos_path: Path, plantilla_path: Path, salida_path: Path) -> dict:
    print(f"[arch_orchestrator] Recibidos: datos='{datos_path.name}', plantilla='{plantilla_path.name}'")

    # 1) Validación de extensiones
    ext_datos = datos_path.suffix.lower()
    ext_tpl   = plantilla_path.suffix.lower()

    if ext_datos not in DATA_EXTS_ALLOWED:
        raise ValueError(f"El archivo de datos debe ser PDF (recibido {ext_datos})")
    if ext_tpl not in TEMPLATE_EXTS_ALLOWED:
        raise ValueError(f"La plantilla debe ser .docx/.xlsx (recibido {ext_tpl})")

    # 2) Leer datos
    if ext_datos == ".pdf":
        datos = pdf_reader(datos_path)
    else:
        raise RuntimeError("Solo se admite PDF de momento")

    if datos is None:
        raise RuntimeError(f"No se pudieron leer los datos de '{datos_path.name}'")

    # 3) Generar salida según tipo de plantilla
    if ext_tpl == ".docx":
        docx_generator(plantilla_path, salida_path, datos)
    else:  # ".xls" o ".xlsx"
        excel_generator(datos, plantilla_path, salida_path)

    if not salida_path.exists():
        raise RuntimeError(f"No se creó '{salida_path.name}'")

    return {
        "detected_data_type": ext_datos,
        "output_path":        str(salida_path),
    }
