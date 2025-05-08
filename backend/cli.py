# backend/cli.py

import sys
from pathlib import Path
from datetime import datetime
from services.arch_orchestrator import arch_orchestrator

def main():
    if len(sys.argv) != 3:
        print("Uso: python cli.py <ruta_plantilla> <ruta_datos>")
        sys.exit(1)

    tpl = Path(sys.argv[1])
    datos = Path(sys.argv[2])
    if not tpl.exists() or not datos.exists():
        print("❌ Alguno de los archivos no existe.")
        sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    salida = Path("salidas") / f"salida_{ts}{tpl.suffix}"
    print(f"Plantilla: {tpl}")
    print(f"Datos:      {datos}")
    print(f"Salida:     {salida}\n")

    try:
        arch_orchestrator(tpl, datos, salida)
        print(f"\n✅ Documento generado en: {salida}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
