# main.py
import sys
from pathlib import Path
from datetime import datetime

from config import DATA_DIR, TEMPLATE_DIR, OUTPUT_DIR
from readers.lector_excel import excel_reader
from readers.docx_reader   import docx_reader
from readers.pdf_reader    import pdf_reader
from generators.excel_generator import excel_generator
from generators.docx_generator  import docx_generator
from generators.pdf_generator   import pdf_generator

def arch_reader() -> dict:
    """Extrae los datos del primer archivo de data_files/ y devuelve un dict."""
    if not DATA_DIR.exists():
        print("❌ Carpeta 'data_files/' no encontrada."); sys.exit(1)

    archivos = sorted(DATA_DIR.iterdir())
    if not archivos:
        print("⚠️  No hay archivos en 'data_files/' para procesar."); sys.exit(0)

    input_path = archivos[0]
    ext = input_path.suffix.lower()

    if ext in ('.xls', '.xlsx'):
        return excel_reader(input_path)
    if ext == '.docx':
        return docx_reader(input_path)
    if ext == '.pdf':
        return pdf_reader(input_path)

    print(f"❌ Formato '{ext}' no soportado"); sys.exit(1)

def arch_generator(datos: dict) -> None:
    """Genera un documento usando la primera plantilla de plantillas/."""
    if not TEMPLATE_DIR.exists():
        print("❌ Carpeta 'plantillas/' no encontrada."); sys.exit(1)
    plantillas = sorted(TEMPLATE_DIR.iterdir())
    if not plantillas:
        print("⚠️  No hay plantillas en 'plantillas/' para procesar."); sys.exit(0)

    tpl_path = plantillas[0]
    ext = tpl_path.suffix.lower()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%d_%H%M%S')
    output_file = OUTPUT_DIR / f"salida_{ts}{ext}"

    if ext == '.docx':
        docx_generator(tpl_path, output_file, datos)

    elif ext in ('.xls', '.xlsx'):
        excel_generator(datos, output_file)

    elif ext == '.pdf':
        pdf_generator(tpl_path, output_file)

    else:
        print(f"❌ Extensión '{ext}' no soportada"); sys.exit(1)

    print(f"✅ Documento generado en: {output_file}")

if __name__ == '__main__':
    datos = arch_reader()
    #print(datos)
    for k, v in datos.items():
        print(f"{k:12}: {v}")
    arch_generator(datos)
