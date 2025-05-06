# main.py
import glob, os
from pathlib import Path
from datetime import datetime

from generador.lector_excel import extraer_datos_excel
from generador.modificar_docx import reemplazar_campos_docx

def arch_reader() -> dict:
    fichero = glob.glob(os.path.join("data", "*.xls"))[0]
    print("▶ Leyendo:", fichero)
    datos = extraer_datos_excel(fichero)

    for k, v in datos.items():
        print(f"{k:10}: {v}")
    return datos

def arch_generator(datos: dict):
    plantilla = Path("plantillas/NUEVA SOLICITUD_BT_GENERICA DGTEyEC 15042024.docx")
    hoy = datetime.today().strftime("%Y%m%d_%H%M%S")
    salida = Path(f"salidas/solicitud_rellenada_{hoy}.docx")
    salida.parent.mkdir(parents=True, exist_ok=True)

    # --- Mapeo literal_original → valor_nuevo ---
    reemplazos = {
        "53394761P"                : datos["nif"],
        "Magaña"                   : datos["apellido1"],
        "Alfonso"                  : datos["apellido2"],
        "Jaime"                    : datos["nombre"],
        "Jaimemagana@gmail.com"    : datos.get("email", ""),
        "C/ Sta Teresa 59"         : datos["direccion"].strip(),
        "28691"                    : datos["cp"],
        "Villanueva de la Cañada"  : datos["localidad"],
        "675 194 676"              : datos.get("telefono", ""),
    }

    reemplazar_campos_docx(plantilla, salida, reemplazos)

if __name__ == "__main__":
    data = arch_reader()
    arch_generator(data)
