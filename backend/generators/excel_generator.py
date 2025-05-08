
from pathlib import Path
from typing import Dict

# generators/excel_generator.py

import openpyxl  # Asegúrate de tenerlo instalado: pip install openpyxl
from pathlib import Path
from typing import Dict
import unicodedata
import re


def _excel_norm(txt: str) -> str:
    """Normaliza el texto para comparación (minúsculas, sin acentos, espacios simples)."""
    if not isinstance(txt, str):
        txt = str(txt)  # Convertir a string si no lo es (ej. números en celdas)
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", txt).strip().lower()


# Mapeo de etiquetas (normalizadas) esperadas en la PLANTILLA EXCEL
# a las claves del diccionario 'datos_de_entrada' (que viene del DOCX).
# DEBES AJUSTAR LAS CLAVES DE ESTE DICCIONARIO (lo que está antes de ':')
# para que coincidan con el texto de las etiquetas en tu plantilla Excel.
# Los valores (lo que está después de ':') deben ser las claves que usa tu 'docx_reader'.
LABEL_IN_EXCEL_TO_DATA_KEY = {
    _excel_norm("nif"): 'nif',
    _excel_norm("cif"): 'nif',  # Alternativa
    _excel_norm("identificación fiscal"): 'nif',  # Alternativa
    _excel_norm("primer apellido"): 'apellido1',
    _excel_norm("segundo apellido"): 'apellido2',
    _excel_norm("nombre"): 'nombre',
    _excel_norm("razon social"): 'nombre',  # Si 'nombre' en datos_de_entrada contiene la razón social
    _excel_norm("nombre/razon social"): 'nombre',
    _excel_norm("correo electronico"): 'email',
    _excel_norm("email"): 'email',
    _excel_norm("correo-e"): 'email',  # Como en la imagen del certificado
    _excel_norm("direccion completa"): 'direccion',  # Si la dirección es un solo campo en Excel
    _excel_norm("domicilio"): 'direccion',
    _excel_norm("tipo de via"): 'tipo_via',  # Si los componentes de dirección están separados en Excel
    _excel_norm("nombre de via"): 'nom_via',  # Y quieres llenarlos individualmente
    _excel_norm("numero"): 'numero',  # (requiere que docx_reader también los devuelva individualmente)
    _excel_norm("nº"): 'numero',
    _excel_norm("codigo postal"): 'cp',
    _excel_norm("cp"): 'cp',
    _excel_norm("localidad"): 'localidad',
    _excel_norm("poblacion"): 'localidad',
    _excel_norm("provincia"): 'provincia',
    _excel_norm("telefono movil"): 'telefono',
    _excel_norm("movil"): 'telefono',
    _excel_norm("telefono"): 'telefono',  # Si 'telefono' en datos_de_entrada es el principal a usar
    _excel_norm("telefono fijo"): 'telefono_fijo',
    # Campos del certificado de la imagen (si los necesitas en el Excel)
    # Asegúrate que tu docx_reader extrae estos campos con estas claves si los vas a usar.
    _excel_norm("identificador del cie"): "identificador_cie",
    _excel_norm("emplazamiento nombre via"): "emplazamiento_nom_via",  # Asumiendo claves en datos_de_entrada
    _excel_norm("emplazamiento tipo via"): "emplazamiento_tipo_via",
    _excel_norm("emplazamiento nº"): "emplazamiento_numero",
    _excel_norm("emplazamiento cp"): "emplazamiento_cp",
    _excel_norm("emplazamiento localidad"): "emplazamiento_localidad",
    _excel_norm("piso"): "piso",
    _excel_norm("puerta"): "puerta",
    _excel_norm("direccion del punto de suministro"): "direccion_suministro_completa",
    _excel_norm("cups"): "cups",
    _excel_norm("pot. max. adm."): "pot_max_adm",
    _excel_norm("tipo instalacion"): "tipo_instalacion_desc",
    _excel_norm("empresa distribuidora"): "empresa_distribuidora",
}


def excel_generator(
        datos_de_entrada: Dict[str, str],  # Datos del DOCX (leídos por docx_reader)
        plantilla_excel_path: Path,  # Ruta a la plantilla .xlsx
        salida_excel_path: Path,  # Ruta para el archivo Excel de salida
        sheet_to_modify_idx: int = 0,  # Índice de la hoja a modificar (0 para la primera)
        label_value_offset: int = 1  # Celda del valor está 'offset' columnas a la derecha de la etiqueta
) -> None:
    """
    Modifica una plantilla Excel (.xlsx) reemplazando valores basados en etiquetas.

    Args:
        datos_de_entrada: Diccionario con los nuevos datos a insertar.
        plantilla_excel_path: Ruta al archivo de plantilla Excel.
        salida_excel_path: Ruta donde se guardará el archivo Excel modificado.
        sheet_to_modify_idx: Índice de la hoja de cálculo a modificar.
        label_value_offset: Desplazamiento de columna desde la etiqueta a la celda de valor.
    """
    print(f"ℹ️  [excel_generator] Iniciando generación de Excel a partir de plantilla: {plantilla_excel_path}")
    try:
        # Cargar el libro de trabajo existente
        workbook = openpyxl.load_workbook(plantilla_excel_path)
        # Seleccionar la hoja a modificar
        if sheet_to_modify_idx < len(workbook.sheetnames):
            sheet = workbook.worksheets[sheet_to_modify_idx]
        else:
            print(f"❌ [excel_generator] Índice de hoja {sheet_to_modify_idx} fuera de rango. Usando la primera hoja.")
            sheet = workbook.active
    except FileNotFoundError:
        print(f"❌ [excel_generator] Archivo de plantilla Excel no encontrado: {plantilla_excel_path}")
        return
    except Exception as e:
        print(f"❌ [excel_generator] Error al abrir la plantilla Excel: {plantilla_excel_path}. Detalle: {e}")
        return

    modified_cells_count = 0

    # Iterar por cada fila y luego por cada celda en la fila
    for r_idx, row in enumerate(sheet.iter_rows(), start=1):  # openpyxl es 1-indexed para filas/columnas
        for c_idx, cell in enumerate(row, start=1):
            if cell.value is not None:
                # Normalizar el texto de la celda actual (potencial etiqueta)
                current_cell_text_norm = _excel_norm(str(cell.value))

                # Verificar si esta celda es una etiqueta que conocemos
                if current_cell_text_norm in LABEL_IN_EXCEL_TO_DATA_KEY:
                    data_key = LABEL_IN_EXCEL_TO_DATA_KEY[current_cell_text_norm]

                    # Si la clave de datos correspondiente existe en nuestros datos de entrada
                    if data_key in datos_de_entrada:
                        nuevo_valor = datos_de_entrada[data_key]

                        # Localizar la celda de valor (a la derecha de la etiqueta)
                        value_cell_col_idx = cell.column + label_value_offset
                        value_cell_row_idx = cell.row

                        try:
                            target_value_cell = sheet.cell(row=value_cell_row_idx, column=value_cell_col_idx)

                            # Solo escribir si el nuevo valor es diferente al actual para evitar cambios innecesarios
                            # y para contar correctamente las modificaciones.
                            # Convertir a string para comparación, ya que openpyxl puede tener tipos numéricos.
                            current_target_value_str = str(
                                target_value_cell.value) if target_value_cell.value is not None else ""
                            nuevo_valor_str = str(nuevo_valor)

                            if current_target_value_str != nuevo_valor_str:
                                target_value_cell.value = nuevo_valor  # Escribir el nuevo valor
                                modified_cells_count += 1
                                # print(f"DEBUG: Etiqueta '{cell.value}' ({cell.coordinate}) -> "
                                #       f"Celda valor ({target_value_cell.coordinate}) actualizada a '{nuevo_valor}'")
                        except Exception as e:
                            print(
                                f"⚠️  [excel_generator] Error al intentar escribir en la celda de valor para la etiqueta '{cell.value}'."
                                f" Celda objetivo: fila {value_cell_row_idx}, col {value_cell_col_idx}. Error: {e}")
                    # else:
                    # print(f"ⓘ  [excel_generator] Etiqueta '{cell.value}' encontrada, pero la clave de datos '{data_key}' no está en los datos de entrada.")

    if modified_cells_count > 0:
        print(f"ℹ️  [excel_generator] Se modificaron {modified_cells_count} celdas en la hoja '{sheet.title}'.")
    else:
        print(
            f"⚠️  [excel_generator] No se realizaron modificaciones en la hoja '{sheet.title}' (o los valores ya coincidían).")

    try:
        workbook.save(salida_excel_path)
        print(f"✅ [excel_generator] Documento Excel modificado guardado en: {salida_excel_path}")
    except Exception as e:
        print(f"❌ [excel_generator] Error al guardar el documento Excel modificado: {salida_excel_path}. Detalle: {e}")