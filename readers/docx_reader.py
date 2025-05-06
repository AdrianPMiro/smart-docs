import unicodedata
import re
from docx import Document
from pathlib import Path
from typing import Dict, List, Set


def _norm(txt: str) -> str:
    if not isinstance(txt, str):
        txt = str(txt)
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", txt).strip().lower()


LABEL_TO_CAMPO_DOCX = {
    'nif': 'nif',
    'primer apellido': 'apellido1',
    'segundo apellido': 'apellido2',
    'nombre/razon social': 'nombre',
    'correo electronico': 'email',
    'tipo de via': 'tipo_via',
    'nombre via': 'nom_via',
    'n\u00ba': 'numero',  # da error
    # 'bloque': 'bloque',
    # 'portal': 'portal',
    # 'escalera': 'escalera'
    # 'piso': 'piso',
    # 'puerta': 'puerta',
    'localidad': 'localidad',
    'provincia': 'provincia',
    'cp': 'cp',
    # 'telefono fijo': 'telefono_fijo',
    'telefono movil': 'telefono',
}

TIPO_VIA_ABREVIATURAS = {
    "CALLE": "C/", "AVENIDA": "AVDA.", "PLAZA": "PZA.", "PASEO": "Pº.",
}

ALL_NORMALIZED_LABELS = set(LABEL_TO_CAMPO_DOCX.keys())


def _es_valor_docx(txt: str, todas_las_etiquetas_normalizadas: Set[str]) -> bool:
    return _norm(txt) not in todas_las_etiquetas_normalizadas


def _buscar_valor_en_celdas_derecha(
        cells: List[any],
        etiqueta_idx: int,
        todas_etiquetas_norm: Set[str],
        ancho_busqueda: int = 2
) -> str:
    for i in range(1, ancho_busqueda + 1):
        valor_idx = etiqueta_idx + i
        if valor_idx < len(cells):
            valor_candidato_texto = cells[valor_idx].text.strip()
            if valor_candidato_texto:
                if _es_valor_docx(valor_candidato_texto, todas_etiquetas_norm):
                    return valor_candidato_texto
        else:
            break
    return ""


def docx_reader(doc_path: Path) -> Dict[str, str]:
    # Campos finales que el usuario desea
    desired_final_fields = [
        'nif', 'nombre', 'apellido1', 'apellido2', 'email', 'direccion',
        'cp', 'localidad', 'provincia', 'telefono',
        'tipo_via', 'nom_via', 'numero'
    ]

    address_component_fields = ['tipo_via', 'nom_via', 'numero', 'bloque', 'portal', 'escalera', 'piso', 'puerta']

    try:
        doc = Document(doc_path)
    except Exception as e:
        print(f"Error al abrir o leer el documento DOCX: {doc_path}")
        print(f"Detalle del error: {e}")
        return {field_key: "" for field_key in desired_final_fields}

    raw_extracted_data: Dict[str, str] = {}
    addr_parts_temp: Dict[str, str] = {
        key: "" for key in address_component_fields  # Inicializar todos los componentes de dirección
    }

    for table_idx, table in enumerate(doc.tables):
        for row_idx, row in enumerate(table.rows):
            cells = row.cells
            c_idx = 0
            while c_idx < len(cells):
                raw_label_text = cells[c_idx].text.strip()
                normalized_label = _norm(raw_label_text)

                if normalized_label in LABEL_TO_CAMPO_DOCX:
                    target_field_name = LABEL_TO_CAMPO_DOCX[normalized_label]

                    extracted_value = _buscar_valor_en_celdas_derecha(
                        cells, c_idx, ALL_NORMALIZED_LABELS, ancho_busqueda=2
                    )

                    # --- Debug para 'numero' ---
                    # if normalized_label == 'nº':
                    #     print(f"DEBUG: Etiqueta='{raw_label_text}', Norm='{normalized_label}', Target='{target_field_name}'")
                    #     print(f"DEBUG: Valor extraído para Nº: '{extracted_value}'")
                    #     if c_idx + 1 < len(cells):
                    #         print(f"DEBUG: Texto celda adyacente: '{cells[c_idx+1].text.strip()}'")
                    # --- Fin Debug ---

                    if extracted_value:
                        if target_field_name in addr_parts_temp:
                            if not addr_parts_temp.get(target_field_name):
                                addr_parts_temp[target_field_name] = extracted_value
                        else:
                            if not raw_extracted_data.get(target_field_name):
                                raw_extracted_data[target_field_name] = extracted_value
                    c_idx += 2
                else:
                    c_idx += 1

    # --- Ensamblaje de la dirección ---
    tipo_via_original = addr_parts_temp.get("tipo_via", "")
    tipo_via_abrev = TIPO_VIA_ABREVIATURAS.get(tipo_via_original.upper(), tipo_via_original)

    nom_via_original = addr_parts_temp.get("nom_via", "")
    processed_nom_via = nom_via_original
    if nom_via_original.upper().startswith("SANTO "):
        processed_nom_via = "Sto " + nom_via_original[len("SANTO "):]
    elif nom_via_original.upper().startswith("SAN "):
        processed_nom_via = "S " + nom_via_original[len("SAN "):]
    elif nom_via_original.upper().startswith("SANTA "):
        parts = nom_via_original.split(" ")
        if len(parts) >= 2:
            processed_nom_via = "Sta " + parts[1]
        elif len(parts) == 1:
            processed_nom_via = "Sta"

    numero_calle = addr_parts_temp.get('numero', '')  # Obtener el número de la calle
    direccion_parts_list = [
        tipo_via_abrev,
        processed_nom_via,
        numero_calle
    ]
    full_direccion_str = " ".join(part for part in direccion_parts_list if part)
    raw_extracted_data['direccion'] = re.sub(r"\s+", " ", full_direccion_str).strip()

    # --- Preparar el diccionario final con solo los campos deseados ---
    final_output_data: Dict[str, str] = {}
    for field_key in desired_final_fields:
        if field_key == 'direccion':
            final_output_data[field_key] = raw_extracted_data.get('direccion', '')
        elif field_key in raw_extracted_data:  # Campos generales
            final_output_data[field_key] = raw_extracted_data[field_key]
        elif field_key in addr_parts_temp:  # Componentes de dirección (como 'tipo_via', 'nom_via', 'numero')
            final_output_data[field_key] = addr_parts_temp[field_key]
        else:
            final_output_data[field_key] = ""  # Para campos deseados no encontrados

    return final_output_data




if __name__ == '__main__':
    test_doc_path = Path("input_file_0.docx")  # Reemplaza con el nombre de tu archivo DOCX

    print(f"Intentando leer datos del documento: {test_doc_path}")

    if test_doc_path.exists():
        datos_extraidos = docx_reader(test_doc_path)

        print("\n--- Datos Extraídos del DOCX (Campos Seleccionados) ---")
        if datos_extraidos:
            # Imprimir solo los campos que el usuario quiere, en el orden que especificó
            print(f"nif         : {datos_extraidos.get('nif')}")
            print(f"nombre      : {datos_extraidos.get('nombre')}")
            print(f"apellido1   : {datos_extraidos.get('apellido1')}")
            print(f"apellido2   : {datos_extraidos.get('apellido2')}")
            print(f"email       : {datos_extraidos.get('email')}")
            print(f"direccion   : {datos_extraidos.get('direccion')}")  # Debe incluir el número si 'numero' se extrae
            print(f"cp          : {datos_extraidos.get('cp')}")
            print(f"localidad   : {datos_extraidos.get('localidad')}")
            print(f"provincia   : {datos_extraidos.get('provincia')}")
            print(f"telefono    : {datos_extraidos.get('telefono')}")
            # Los siguientes son componentes, útiles para depurar la dirección
            print(f"tipo_via    : {datos_extraidos.get('tipo_via')}")
            print(f"nom_via     : {datos_extraidos.get('nom_via')}")
            print(f"numero      : {datos_extraidos.get('numero')}")  # Este es el que estamos tratando de arreglar
        else:
            print("No se extrajeron datos o hubo un error.")

    else:
        print(f"\n⚠️  El archivo de prueba '{test_doc_path}' no se encontró.")
        print("Por favor, sube tu archivo DOCX y ajusta la variable 'test_doc_path' en el código.")


