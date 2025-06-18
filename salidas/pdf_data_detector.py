# backend/services/pdf_data_detector.py

from pathlib import Path
import fitz  # PyMuPDF
from typing import Optional  # Mantenemos Optional por si lo usas en otros detectores

# --- Lista de identificadores únicos para cada tipo de PDF de DATOS ---
# ESTO LO LLENARÁS DESPUÉS DE VER LA SALIDA DEL SCRIPT DE PRUEBA
# (texto_unico_a_buscar, tipo_a_devolver)
PDF_DATA_IDENTIFIERS = [
    # Ejemplo: ("TEXTO EXACTO DE LA PRIMERA LÍNEA DEL PDF TIPO 1", "pdf_tipo_1_factura"),
    # Ejemplo: ("TEXTO EXACTO DE LA PRIMERA LÍNEA DEL PDF TIPO 2", "pdf_tipo_2_propuesta"),
]


def detect_pdf_data_type_by_first_line(pdf_path: Path) -> str:  # Cambiado para devolver solo string
    """
    Detecta el tipo de un PDF de datos basado en cadenas de texto únicas
    encontradas en su contenido inicial.
    Imprime el texto inicial para ayudar a definir los identificadores.
    """
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        print(f"[pdf_detector] Archivo no es PDF o no existe: {pdf_path}")
        return "pdf_invalido"

    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            doc.close()
            print(f"[pdf_detector] PDF vacío (sin páginas): {pdf_path}")
            return "pdf_vacio"

        page = doc[0]  # Primera página

        # Extraer una porción inicial de texto de la página
        # Suficiente para capturar identificadores de la primera línea o del inicio.
        # Clip a los primeros 150 puntos de altura, tomar hasta 300 caracteres.
        initial_text_raw = page.get_text("text", clip=fitz.Rect(0, 0, page.rect.width, 150))[:300]
        doc.close()

        if not initial_text_raw or not initial_text_raw.strip():
            print(f"[pdf_detector] No se pudo extraer texto inicial de la primera página: {pdf_path}")
            return "pdf_sin_texto_inicial"

        # Limpiar un poco para la comparación y para mostrarlo
        text_to_check = " ".join(initial_text_raw.strip().splitlines()).strip()

        # --- ¡IMPRESIÓN CLAVE PARA TI! ---
        print(f"\n[pdf_detector] -------- TEXTO INICIAL PARA '{pdf_path.name}' --------")
        print(text_to_check)
        print(f"[pdf_detector] -------- FIN TEXTO INICIAL PARA '{pdf_path.name}' --------\n")
        # También el repr() puede ser útil para ver caracteres ocultos
        # print(f"[pdf_detector] repr(text_to_check): {repr(text_to_check)}\n")

        # La lógica de detección real se basará en lo que veas arriba.
        # Por ahora, solo comprobamos si los identificadores están definidos.
        if not PDF_DATA_IDENTIFIERS:
            print("[pdf_detector] ADVERTENCIA: PDF_DATA_IDENTIFIERS está vacío. No se puede detectar tipo específico.")
            print("[pdf_detector] Por favor, define los identificadores basados en la salida de 'TEXTO INICIAL'.")
            return "pdf_configurar_identificadores"

        for identifier_text, pdf_type in PDF_DATA_IDENTIFIERS:
            # Comparación insensible a mayúsculas/minúsculas
            if identifier_text.upper() in text_to_check.upper():
                print(
                    f"[pdf_detector] Tipo detectado para '{pdf_path.name}': '{pdf_type}' (basado en: '{identifier_text}')")
                return pdf_type

    except Exception as e:
        print(f"Error al procesar PDF {pdf_path} para detección de tipo: {e}")
        return "pdf_error_procesamiento"

    print(f"[pdf_detector] Tipo de PDF desconocido para '{pdf_path.name}' (ningún identificador coincidió).")
    return "pdf_tipo_desconocido"