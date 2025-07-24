from pathlib import Path

# readers
from backend.readers.pdf_reader import pdf_reader

from backend.generators.excel_generator import excel_generator

# generators
from backend.generators.docx_generator  import docx_generator
# from backend.generators.excel_generator import excel_generator # Se elimina si la salida es solo docx

# detectores
# from backend.services.pdf_detector    import detect_pdf_data_type_by_first_line
from backend.services.docx_detector import detect_docx_template_type

# 2. EXTENSIONES PERMITIDAS
DATA_EXTS_ALLOWED     = {".pdf"}
TEMPLATE_EXTS_ALLOWED = {".docx", ".xls", ".xlsx"}

def arch_orchestrator(datos_path: Path, plantilla_path: Path, salida_path: Path) -> dict:
    print(f"[arch_orchestrator] Recibidos: datos='{datos_path.name}', plantilla='{plantilla_path.name}'")

    # 1) Validación de extensiones
    ext_datos = datos_path.suffix.lower()
    ext_tpl   = plantilla_path.suffix.lower()

    if ext_datos not in DATA_EXTS_ALLOWED:
        # 3. CORREGIR MENSAJE DE ERROR
        raise ValueError(f"El archivo de datos debe ser PDF o Excel (recibido {ext_datos})")
    if ext_tpl not in TEMPLATE_EXTS_ALLOWED:
        raise ValueError(f"La plantilla debe ser .docx (recibido {ext_tpl})")

    # 2) Detectar tipo de plantilla
    #tpl_kind  = detect_docx_template_type(plantilla_path)
    #print(f"==> [arch_orchestrator] Tipo de PLANTILLA: '{tpl_kind}'")

    # 3) Leer datos
    datos = None
    if ext_datos == ".pdf":
        datos = pdf_reader(datos_path)

    print(f"[arch_orchestrator] Datos leídos: {datos is not None}")
    print(f"[arch_orchestrator] Salida: {salida_path}")
    if datos is None:
        raise RuntimeError(f"No se pudieron leer los datos del archivo '{datos_path.name}'")
    print(f"datos: {datos}")

    #elif ext_datos in (".xls", ".xlsx"):
    #    datos = excel_reader(datos_path)

    if datos is None:
        raise RuntimeError(f"No se pudieron leer los datos del archivo '{datos_path.name}'")

        # 4) Generar salida según tipo de plantilla
    if ext_tpl == ".docx":
        docx_generator(plantilla_path, salida_path, datos)
    else:  # ".xls" o ".xlsx"
        excel_generator(datos, plantilla_path, salida_path)

    if not salida_path.exists():
        raise RuntimeError(f"[arch_orchestrator] No se creó '{salida_path.name}'")

    # 5) Devuelve metainformación para logs / front
    return {
        "detected_data_type":     ext_datos, # Usar la extensión directamente
        "output_path":            str(salida_path)
    }