# generators/pdf_generator.py

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, Tuple, Optional

# Importar tu pdf_reader
from backend.readers.pdf_reader import pdf_reader

def _guess_font_properties_for_redact(page: fitz.Page, rect_of_interest: fitz.Rect) -> Tuple[str, float, int]:
    """
    Intenta adivinar el nombre de la fuente, tamaño y color (sRGB entero)
    del primer span de texto que se solapa significativamente con el rect_of_interest.
    Usado para add_redact_annot.
    Devuelve ("helv", 10, 0) como fallback (Helvetica, 10pt, Negro).
    """
    textpage_dict = page.get_text("dict", clip=rect_of_interest)
    best_match_span: Optional[Dict] = None
    max_intersection_area = 0.0

    for block in textpage_dict.get("blocks", []):
        if block.get("type") == 0:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_rect = fitz.Rect(span["bbox"])
                    intersection = span_rect.irect
                    intersection.intersect(rect_of_interest.irect)
                    area = intersection.width * intersection.height
                    if area > max_intersection_area:
                        max_intersection_area = area
                        best_match_span = span

    if best_match_span:
        font_name = best_match_span["font"]
        # PyMuPDF para add_redact_annot a veces prefiere nombres de fuente base o nombres PostScript
        # Simplificamos a las familias comunes. Si la fuente es muy específica, podría no funcionar.
        if "bold" in font_name.lower():
            if "helvetica" in font_name.lower() or "arial" in font_name.lower(): font_name = "helvb" # Helvetica Bold
            elif "times" in font_name.lower(): font_name = "timrb" # Times Bold
            elif "courier" in font_name.lower(): font_name = "courb" # Courier Bold
            else: font_name = "helvb" # Fallback bold
        elif "italic" in font_name.lower() or "oblique" in font_name.lower():
            if "helvetica" in font_name.lower() or "arial" in font_name.lower(): font_name = "helvi" # Helvetica Italic
            elif "times" in font_name.lower(): font_name = "timri" # Times Italic
            elif "courier" in font_name.lower(): font_name = "couri" # Courier Italic
            else: font_name = "helvi" # Fallback italic
        else: # Regular
            if "helvetica" in font_name.lower() or "arial" in font_name.lower(): font_name = "helv"
            elif "times" in font_name.lower(): font_name = "timr"
            elif "courier" in font_name.lower(): font_name = "cour"
            else: font_name = "helv" # Fallback regular

        font_size = float(best_match_span["size"])
        font_size = max(font_size, 6.0) # Mínimo 6pt
        color_srgb_int = best_match_span["color"] # Color como entero sRGB
        # print(f"DEBUG _guess_font_redact: Rect {rect_of_interest}, Span: {best_match_span['text'][:20]}, Font: {font_name}, Size: {font_size}, ColorInt: {color_srgb_int}")
        return font_name, font_size, color_srgb_int

    # print(f"WARN _guess_font_redact: No span para rect {rect_of_interest}. Fallback.")
    return "helv", 10.0, 0 # Helvetica, 10pt, Negro (0x000000)


def pdf_generator(plantilla_path: Path, salida_path: Path, datos_nuevos: Dict[str, str]) -> None:
    print(f"--- [pdf_generator] Iniciando para plantilla: {plantilla_path} ---")
    # ... (impresión de datos_nuevos) ...
    if datos_nuevos: [print(f"'{k}': '{v}'") for k, v in datos_nuevos.items()]
    else: print("Diccionario datos_nuevos está vacío.")
    print("--- [pdf_generator] FIN DATOS NUEVOS ---\n")

    try:
        datos_originales_plantilla = pdf_reader(plantilla_path)
    except Exception as e:
        print(f"❌ ERROR CRÍTICO al llamar a pdf_reader para plantilla '{plantilla_path}': {e}")
        # ... (copiar y salir) ...
        return

    print("--- [pdf_generator] DATOS ORIGINALES DE PLANTILLA (leídos por pdf_reader) ---")
    # ... (impresión de datos_originales_plantilla) ...
    if datos_originales_plantilla: [print(f"'{k}': '{v}'") for k, v in datos_originales_plantilla.items()]
    else: print("datos_originales_plantilla es None o está vacío.")
    print("--- [pdf_generator] FIN DATOS ORIGINALES DE PLANTILLA ---\n")

    reemplazos_map: Dict[str, str] = {} # {texto_original_EN_PDF_UPPER: nuevo_texto_FORMATEADO_UPPER}

    if datos_originales_plantilla and datos_nuevos:
        # Definir cómo se construyen los textos VIEJOS (a buscar) y los textos NUEVOS (a poner)
        # Basado en las claves que devuelve tu pdf_reader y las que tienes en datos_nuevos

        # Nombre Completo
        viejo_nombre = str(datos_originales_plantilla.get("nombre", "")).strip()
        viejo_ap1 = str(datos_originales_plantilla.get("apellido1", "")).strip()
        viejo_ap2 = str(datos_originales_plantilla.get("apellido2", "")).strip()
        viejo_nombre_completo = " ".join(filter(None, [viejo_nombre, viejo_ap1, viejo_ap2])).upper()

        nuevo_nombre = str(datos_nuevos.get("nombre", "")).strip()
        nuevo_ap1 = str(datos_nuevos.get("apellido1", "")).strip()
        nuevo_ap2 = str(datos_nuevos.get("apellido2", "")).strip()
        nuevo_nombre_completo_val = " ".join(filter(None, [nuevo_nombre, nuevo_ap1, nuevo_ap2])).upper()

        if viejo_nombre_completo and nuevo_nombre_completo_val and viejo_nombre_completo != nuevo_nombre_completo_val:
            reemplazos_map[viejo_nombre_completo] = nuevo_nombre_completo_val

        # NIF
        viejo_nif = str(datos_originales_plantilla.get("nif", "")).strip().upper()
        nuevo_nif_val = str(datos_nuevos.get("nif", "")).strip().upper()
        if viejo_nif and nuevo_nif_val and viejo_nif != nuevo_nif_val:
            reemplazos_map[viejo_nif] = nuevo_nif_val

        # Dirección Completa (ejemplo, podrías necesitar más campos)
        # TU pdf_reader NO devuelve "direccion" directamente, sino sus componentes.
        # Si quieres reemplazar una dirección completa, necesitas reconstruirla desde pdf_reader
        # O, si tu pdf_reader SÍ extrae la línea de dirección completa, usa esa clave.
        # Ejemplo ASUMIENDO que pdf_reader extrae 'direccion_completa_raw' de la plantilla:
        # viejo_direccion_raw = str(datos_originales_plantilla.get("direccion_completa_raw", "")).strip().upper()
        # nuevo_direccion_val = str(datos_nuevos.get("direccion", "")).strip().upper() # 'direccion' de datos_nuevos
        # if viejo_direccion_raw and nuevo_direccion_val and viejo_direccion_raw != nuevo_direccion_val:
        #     reemplazos_map[viejo_direccion_raw] = nuevo_direccion_val

        # Campos individuales (si se buscan y reemplazan individualmente)
        campos_individuales = {"cp": "cp", "localidad": "localidad"} # pdf_reader_key: datos_nuevos_key
        for pdf_key, nuevo_key in campos_individuales.items():
            viejo_val = str(datos_originales_plantilla.get(pdf_key, "")).strip().upper()
            nuevo_val = str(datos_nuevos.get(nuevo_key, "")).strip().upper()
            # Quitar ".0" de los nuevos valores si vienen de floats
            if nuevo_val.endswith(".0"):
                nuevo_val = nuevo_val[:-2]

            if viejo_val and nuevo_val and viejo_val != nuevo_val:
                reemplazos_map[viejo_val] = nuevo_val
            elif viejo_val and not nuevo_val: # Borrar
                reemplazos_map[viejo_val] = ""


    if not reemplazos_map:
        print("⚠️  [pdf_generator] No hay textos para reemplazar (mapa vacío).")
        # ... (copiar original y salir) ...
        return

    print("--- [pdf_generator] MAPA DE REEMPLAZOS CONSTRUIDO ---")
    [print(f"Reemplazar '{k}' con '{v}'") for k,v in reemplazos_map.items()]
    print("--- [pdf_generator] FIN MAPA DE REEMPLAZOS ---\n")

    try:
        doc = fitz.open(str(plantilla_path))
    except Exception as e:
        print(f"❌ Error al abrir la plantilla PDF '{plantilla_path}' con PyMuPDF: {e}")
        return

    total_text_instances_replaced_overall = 0

    for page_num, page in enumerate(doc):
        page_modifications_this_page = 0
        print(f"\n--- [pdf_generator] PROCESANDO PÁGINA {page_num + 1} ---")

        for old_text_to_find, new_text_to_insert in reemplazos_map.items():
            if not old_text_to_find: # No buscar cadena vacía
                continue

            print(f"  Buscando en PÁG {page_num+1} el texto: '{old_text_to_find}'")
            # Usar search_for. Por defecto es sensible a mayúsculas.
            # Como old_text_to_find ya está en .upper(), esto es lo que queremos.
            rects_found = page.search_for(old_text_to_find)

            if not rects_found:
                print(f"    -> NO ENCONTRADO: '{old_text_to_find}'")
                continue

            print(f"    -> ENCONTRADO: '{old_text_to_find}' en {len(rects_found)} instancia(s).")
            for idx, rect in enumerate(rects_found):
                print(f"      Instancia {idx+1} en Rect: {rect}")

                fontname, fontsize, fontcolor_srgb_int = _guess_font_properties_for_redact(page, rect)
                print(f"        Propiedades para add_redact_annot: Font='{fontname}', Size={fontsize:.2f}, ColorInt={fontcolor_srgb_int}")

                page.add_redact_annot(
                    rect,
                    text=new_text_to_insert, # PyMuPDF intentará ajustar esto en el rect
                    fontname=fontname,
                    fontsize=fontsize,
                    fill=(1,1,1),         # Fondo blanco para la redacción
                    # text_color=fontcolor_srgb_int, # Color del texto nuevo (entero sRGB)
                    # Dejar que PyMuPDF use el color del span si es posible,
                    # o forzar negro si fontcolor_srgb_int es 0
                    text_color=0 if fontcolor_srgb_int == 0 else fontcolor_srgb_int, # Forzar negro si el color original era negro
                    align=fitz.TEXT_ALIGN_LEFT # O TEXT_ALIGN_CENTER según necesidad
                )
                page_modifications_this_page += 1

        if page_modifications_this_page > 0:
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE) # Aplicar todas las redacciones de la página
            print(f"ℹ️  [pdf_generator] {page_modifications_this_page} anotaciones de redacción aplicadas en página {page_num + 1}.")
            total_text_instances_replaced_overall += page_modifications_this_page
        else:
            print(f"  No se aplicaron redacciones en la página {page_num + 1}.")

    # ... (Lógica de guardado final como antes) ...
    try:
        if total_text_instances_replaced_overall > 0 : # O si simplemente el doc ha sido modificado
            doc.save(str(salida_path), garbage=4, deflate=True, linear=True)
            print(f"✅ [pdf_generator] PDF modificado guardado en: {salida_path}")
        else:
            import shutil
            if plantilla_path.resolve() != salida_path.resolve():
                 shutil.copy(plantilla_path, salida_path)
                 print(f"ⓘ  [pdf_generator] No se realizaron reemplazos/redacciones. Copia del original guardada en: {salida_path}")
            else:
                 print(f"ⓘ  [pdf_generator] No se realizaron reemplazos y el archivo de salida es el mismo. No se guarda.")
    except Exception as e:
        print(f"❌ Error al guardar el PDF modificado '{salida_path}': {e}")
    finally:
        doc.close()

def _estimate_font_size_from_words_in_rect(page: fitz.Page, rect: fitz.Rect) -> float:
    """Estima fontsize basado en la altura promedio de palabras dentro del rect."""
    words = page.get_text("words", clip=rect)  # (x0,y0,x1,y1,word,...)
    if not words:
        return 10.0  # Fallback size

    word_heights = [w[3] - w[1] for w in words if w[3] > w[1]]  # y1 - y0, asegurar altura positiva
    if not word_heights:
        return 10.0

    avg_word_height = sum(word_heights) / len(word_heights)

    # *** HEURÍSTICA CLAVE PARA AJUSTAR ***
    estimated_fontsize = avg_word_height * 0.75  # Probar diferentes multiplicadores (0.7, 0.8, 0.85...)
    estimated_fontsize = max(estimated_fontsize, 6.0)  # Mínimo 6pt

    # print(f"DEBUG _estimate_font_size_words: Rect {rect}, AvgWordH {avg_word_height:.2f} -> Est.Size {estimated_fontsize:.2f}")
    return estimated_fontsize