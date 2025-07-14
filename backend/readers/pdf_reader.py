from typing import Dict, Union
import pdfplumber
import re
from pathlib import Path
import logging

logging.getLogger("pdfminer").setLevel(logging.ERROR)

# Mapeo de tipo de vía: clave = nombre completo, valor = abreviatura
TIPO_VIA_ABREVIATURAS = {
    "CALLE": "C/",
    "AVENIDA": "AVDA.",
    "PLAZA": "PZA.",
    "PASEO": "Pº.",
}
# Inverso: abreviatura → nombre completo en minúsculas
ABBR_TO_FULL = {abbr: full.lower() for full, abbr in TIPO_VIA_ABREVIATURAS.items()}


def pdf_reader(path: Path) -> Dict[str, str]:
    datos = {
        "NIF": None,
        "apellido1": None,
        "apellido2": None,
        "nombre": None,
        "email": None,
        "tipo_via": None,
        "nom_via": None,
        "numero": None,
        "localidad": None,
        "provincia": None,
        "cp": None,
        "telefono": None
    }

    patrones_principales = {
        r"Titular:\s*(.+)": "Titular",
        r"NIF:\s*([A-Z0-9]+)": "NIF",
        r"Descripción del suministro:\s*(.+)": "Descripción del suministro",
        r"Dirección de suministro:\s*(.+)": "Dirección de suministro",
        r"TIPO DE CONTRATO:\s*(.+)": "TIPO DE CONTRATO",
        r"No contador:\s*(\d+)": "No contador"
    }
    patrones_adicionales = {
        r"primer apellido:\s*(.+)": "apellido1",
        r"segundo apellido:\s*(.+)": "apellido2",
        r"nombre/razon social:\s*(.+)": "nombre",
        r"correo electronico:\s*(.+)": "email",
        r"tipo de via:\s*(.+)": "tipo_via",
        r"nombre via:\s*(.+)": "nom_via",
        r"numero:\s*(.+)": "numero",
        r"localidad:\s*(.+)": "localidad",
        r"provincia:\s*(.+)": "provincia",
        r"cp:\s*(\d{5})": "cp",
        r"telefono movil:\s*(\d+)": "telefono"
    }

    # 1) Leer todo el texto del PDF
    texto_total = ""
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                texto_total += "\n" + page_text
    texto_total = texto_total.replace("Nº", "No")

    # 2) Extraer patrones principales
    for patron, clave in patrones_principales.items():
        if match := re.search(patron, texto_total):
            datos[clave] = match.group(1).strip()

    # 3) Extraer patrones adicionales
    for patron, clave in patrones_adicionales.items():
        if match := re.search(patron, texto_total, re.IGNORECASE):
            datos[clave] = match.group(1).strip()

    # 4) Descomponer dirección
    descomponer_direccion(datos.get("Dirección de suministro"), datos)

    # 5) Estandarizar tipo_via
    if datos.get("tipo_via"):
        datos["tipo_via"] = estandarizar_tipo_via(datos["tipo_via"])

    # 6) Extraer nombre y apellidos del Titular si faltan
    extraer_nombre_apellidos(datos.get("Titular"), datos)

    # 7) **Asignar valores por defecto si faltan**
    if not datos.get("telefono"):
        datos["telefono"] = "675194676"
    if not datos.get("email"):
        datos["email"] = "Jaimemagana@gmail.com"

    # 8) Construir el resultado final
    resultado = {
        "nif": datos.get("NIF"),
        "nombre": datos.get("nombre"),
        "apellido1": datos.get("apellido1"),
        "apellido2": datos.get("apellido2"),
        "tipo_via": datos.get("tipo_via"),
        "nom_via": datos.get("nom_via"),
        "telefono": datos.get("telefono"),
        "email": datos.get("email"),
        "cp": datos.get("cp"),
        "localidad": datos.get("localidad"),
        # otros campos comentados si se necesitan en el futuro
    }
    return resultado


def descomponer_direccion(direccion: str, datos: dict):
    if not direccion:
        return
    patron = (
        r'(?P<tipo_via>C/|AVDA\.|PZA\.|Pº\.)\s+'
        r'(?P<nom_via>.+?),\s*'
        r'(?P<numero>\d+)\s+'
        r'(?P<cp>\d{5})\s+'
        r'(?P<localidad>.+?)\s+'
        r'\((?P<provincia>.+?)\)'
    )
    if match := re.search(patron, direccion, re.IGNORECASE):
        datos["tipo_via"] = match.group("tipo_via").strip()
        datos["nom_via"]   = match.group("nom_via").strip()
        datos["numero"]    = match.group("numero").strip()
        datos["cp"]        = match.group("cp").strip()
        datos["localidad"] = match.group("localidad").strip()
        datos["provincia"] = match.group("provincia").strip()


def extraer_nombre_apellidos(titular: Union[str, None], datos: dict):
    if not titular:
        return
    partes = titular.strip().split()
    if len(partes) >= 3:
        datos["nombre"]    = partes[0]
        datos["apellido1"] = partes[1]
        datos["apellido2"] = " ".join(partes[2:])


def estandarizar_tipo_via(tipo: str) -> str:
    clave_norm = tipo.strip().upper()
    return ABBR_TO_FULL.get(clave_norm, tipo.strip().lower())
