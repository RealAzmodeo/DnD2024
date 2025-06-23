import xml.etree.ElementTree as ET
import os
import re

# Mapeo de abreviaturas de escuelas a nombres completos y para nombres de archivo
SCHOOL_MAP = {
    "A": "Abjuration",
    "C": "Conjuration",
    "D": "Divination",
    "EN": "Enchantment",
    "EV": "Evocation",
    "I": "Illusion",
    "N": "Necromancy",
    "T": "Transmutation",
}

# Mapeo para nombres de archivo (minúsculas)
SCHOOL_FILENAME_MAP = {
    "A": "abjuration",
    "C": "conjuration",
    "D": "divination",
    "EN": "enchantment",
    "EV": "evocation",
    "I": "illusion",
    "N": "necromancy",
    "T": "transmutation",
}

def parse_material_components(components_str):
    """
    Parsea la cadena de componentes materiales para extraer descripción, costo y si se consume.
    Ejemplos:
    "V, S, M (a tiny ball of bat guano and sulfur)" -> description="a tiny ball of bat guano and sulfur", consumed=False, cost_gp=None
    "V, S, M (a diamond worth 50+ GP, which the spell consumes)" -> description="a diamond worth 50+ GP", cost_text="worth 50+ GP", consumed=True
    "V, S, M (incense worth 25+ GP, which the spell consumes)" -> description="incense worth 25+ GP", cost_text="worth 25+ GP", consumed=True
    "V, S, M (a pinch of diamond dust worth 25+ GP, which the spell consumes)" -> description="a pinch of diamond dust worth 25+ GP", cost_text="worth 25+ GP", consumed=True
    """
    materials = []
    if "M (" in components_str:
        m_part_full = components_str.split("M (", 1)[1].rsplit(")", 1)[0]

        # Manejar múltiples materiales dentro de un solo M (...) separados por "; "
        # o " or " (si no son parte de una frase como "powder or paste")
        # Esta es una heurística y puede necesitar ajuste.
        # Priorizar split por "; " que es un separador más fuerte.
        if "; " in m_part_full:
            individual_material_strs = m_part_full.split("; ")
        else:
            # Cuidado con " or " dentro de descripciones, ej. "a powder or paste"
            # Intentar un split más seguro si no hay "worth" o "GP" cerca del "or"
            # Por ahora, asumimos que " or " sin contexto de costo puede separar materiales.
            # Esto es delicado. Si un material es "X or Y, worth Z GP", no queremos dividirlo.
            # Si es "X, or Y (consumed)", probablemente son dos.
            # Para simplificar, por ahora no dividimos por " or " a menos que sea muy claro.
            # La lógica actual procesa m_part_full como un solo material si no hay ";".
            # Esto es generalmente seguro para PHB24.
            individual_material_strs = [m_part_full]

        for material_str_segment in individual_material_strs:
            material_desc = material_str_segment.strip()
            original_material_desc_for_cleaning = material_desc # Guardar para limpieza final

            consumed = "which the spell consumes" in material_desc or \
                       "which the spell consume" in material_desc # Común

            # Casos específicos de consumo
            if re.search(r" consumes the (?:diamond|incense|offering|gem)", material_desc, re.IGNORECASE):
                consumed = True


            cost_gp_val = None
            cost_text_str = None

            # Patrones de costo (priorizados)
            # 1. "worth at least X GP", "worth X+ GP", "worth X GP"
            worth_match = re.search(r"worth\s+(?:at least\s+)?([\d,]+)\+?\s*GP", material_desc, re.IGNORECASE)
            if worth_match:
                cost_gp_str = worth_match.group(1).replace(",", "")
                if cost_gp_str.isdigit():
                    cost_gp_val = cost_gp_str
                cost_text_str = worth_match.group(0) # Captura toda la frase "worth X GP"
            else:
                # 2. "an X GP diamond", "a X GP gem" (costo como adjetivo)
                #    "(X GP)" o "X GP" (costo directo)
                #    Evitar capturar "GP" si es parte de una palabra más larga.
                #    Asegurarse de que no sea parte de "worth X GP" ya capturado.
                direct_cost_match = re.search(r"(?<!worth\s)(?<!worth at least\s)(?:[\(]?)([\d,]+)\+?\s*GP(?:[\)]?)", material_desc, re.IGNORECASE)
                if direct_cost_match:
                    # Verificar que no sea parte de "worth..."
                    # La lookbehind negativa (?<!) ayuda, pero una verificación adicional puede ser útil.
                    # Ejemplo: "a component pouch (containing bat guano) or a spellcasting focus" - no queremos "pouch (containing bat guano) or a spellcasting focus" como costo.
                    # La regex actual es bastante buena para costos directos como "(25 GP)" o "50 GP".

                    # Evitar que "X GP" sea parte de una descripción más amplia si "worth" está presente en otro lugar.
                    # Esta condición es compleja. La regex actual es razonable.
                    cost_gp_str = direct_cost_match.group(1).replace(",", "")
                    if cost_gp_str.isdigit():
                        cost_gp_val = cost_gp_str
                    cost_text_str = direct_cost_match.group(0) # Captura "X GP" o "(X GP)"

            # Limpieza de la descripción del material
            # 1. Remover la frase de consumo
            clean_description = re.sub(r",?\s*which the spell consumes", "", material_desc, flags=re.IGNORECASE).strip()
            clean_description = re.sub(r",?\s*which the spell consume", "", clean_description, flags=re.IGNORECASE).strip()
            # Casos específicos de consumo
            clean_description = re.sub(r",?\s*the spell consumes the (?:diamond|incense|offering|gem)", "", clean_description, flags=re.IGNORECASE).strip()


            # 2. Remover la frase de costo si cost_gp_val fue encontrado
            if cost_gp_val and cost_text_str:
                # Crear un patrón para remover exactamente lo que se identificó como cost_text_str
                # Escapar caracteres especiales en cost_text_str para uso en regex
                # y hacerlo flexible a espacios.
                pattern_to_remove_str = re.escape(cost_text_str)
                pattern_to_remove_str = re.sub(r"\\ ", r"\\s*", pattern_to_remove_str) # flexibilizar espacios

                # Remover la frase de costo, cuidando no dejar espacios dobles o comas sueltas
                clean_description = re.sub(r"(?:,\s*)?" + pattern_to_remove_str + r"(?:\s*,)?", "", clean_description, flags=re.IGNORECASE).strip()
                clean_description = re.sub(r"\s\s+", " ", clean_description).strip() # normalizar espacios
                if clean_description.startswith(','): clean_description = clean_description[1:].strip()
                if clean_description.endswith(','): clean_description = clean_description[:-1].strip()
                if clean_description.endswith(' of'): # ej. "a diamond of"
                    clean_description = clean_description[:-3].strip()


            # Fallback si la limpieza resulta en una cadena vacía pero la original no lo era.
            if not clean_description and original_material_desc_for_cleaning:
                # Usar la descripción original menos la frase de consumo si es la única parte que se pudo quitar.
                temp_clean = re.sub(r",?\s*which the spell consumes", "", original_material_desc_for_cleaning, flags=re.IGNORECASE).strip()
                temp_clean = re.sub(r",?\s*which the spell consume", "", temp_clean, flags=re.IGNORECASE).strip()
                if temp_clean: # Si quitar solo el consumo deja algo, usarlo.
                    clean_description = temp_clean
                else: # Si no, algo salió mal, usar la descripción original como último recurso.
                    clean_description = original_material_desc_for_cleaning


            materials.append({
                "description": clean_description.strip(),
                "consumed": consumed,
                "cost_gp": cost_gp_val,
                "cost_text": cost_text_str if cost_text_str and not cost_gp_val else (cost_text_str if cost_gp_val and cost_text_str != f"{cost_gp_val} GP" and cost_text_str != f"({cost_gp_val} GP)" else None)
                # La idea es que cost_text solo se popule si es diferente de un simple "[cost_gp_val] GP"
                # o si cost_gp_val no se pudo determinar como número.
            })
    return materials

def parse_duration(duration_str):
    """
    Parsea la cadena de duración para extraer valor, unidad y si es concentración.
    """
    concentration = "Concentration" in duration_str
    up_to = "up to" in duration_str

    # Remover "Concentration, " y "up to " para simplificar
    processed_str = duration_str.replace("Concentration, ", "").replace("up to ", "")

    value = None
    unit = None

    if processed_str.lower() == "instantaneous":
        value = "instantaneous"
    elif processed_str.lower() == "until dispelled":
        value = "until_dispelled"
    elif processed_str.lower() == "until triggered":
        value = "until_triggered"
    elif processed_str.lower() == "special":
        value = "special"
    else:
        parts = processed_str.split()
        if len(parts) >= 1 and parts[0].isdigit():
            value = parts[0]
            if len(parts) > 1:
                unit_candidate = parts[1].lower().replace("s", "") # plural a singular
                if unit_candidate in ["round", "minute", "hour", "day", "year"]:
                    unit = unit_candidate
                else: # Caso como "1 round" donde no hay plural
                    if unit_candidate in ["action", "bonusaction", "reaction"]: # improbable para duración pero por si acaso
                         unit = unit_candidate.replace("action","")
                    else: # Si no es una unidad conocida, podría ser parte de una descripción especial
                        value = "special" # Reclasificar como especial
                        unit = None
        elif concentration and not value : # si es solo "Concentration"
            value = "concentration" # Caso especial donde la duración es solo la concentración
        else:
            value = "special" # Si no es numérico ni palabra clave conocida

    return {
        "full_description": duration_str,
        "value": value,
        "unit": unit,
        "concentration": concentration,
        "up_to": up_to
    }

def parse_casting_time(time_str):
    val = None
    unit = None
    condition = None

    time_str_lower = time_str.lower()

    action_match = re.match(r"(\d+)?\s*action", time_str_lower)
    bonus_match = re.match(r"(\d+)?\s*bonus action", time_str_lower)
    reaction_match = re.match(r"(\d+)?\s*reaction", time_str_lower)

    if action_match and "bonus" not in time_str_lower and "reaction" not in time_str_lower :
        unit = "action"
        val = action_match.group(1) or "1"
        # Extraer condición después de "action[s]," o "action[s] which"
        condition_match = re.search(r"action(?:s)?(?:,?\s*which|,)\s*(.*)", time_str, re.IGNORECASE)
        if condition_match:
            condition = condition_match.group(1).strip()
            # Limpiar si la condición empieza repitiendo el tipo de acción (debido a typos en origen)
            if condition.lower().startswith("action"):
                condition = re.sub(r"^action(?:s)?(?:,?\s*which|,)\s*","", condition, flags=re.IGNORECASE).strip()


    elif bonus_match:
        unit = "bonus_action"
        val = bonus_match.group(1) or "1"
        condition_match = re.search(r"bonus action(?:,?\s*which|,)\s*(.*)", time_str, re.IGNORECASE)
        if condition_match:
            condition = condition_match.group(1).strip()
            if condition.lower().startswith("bonus action"):
                 condition = re.sub(r"^bonus action(?:,?\s*which|,)\s*","", condition, flags=re.IGNORECASE).strip()

    elif reaction_match:
        unit = "reaction"
        val = reaction_match.group(1) or "1"
        condition_match = re.search(r"reaction(?:,?\s*which|,)\s*(.*)", time_str, re.IGNORECASE)
        if condition_match:
            condition = condition_match.group(1).strip()
            if condition.lower().startswith("reaction"):
                condition = re.sub(r"^reaction(?:,?\s*which|,)\s*","", condition, flags=re.IGNORECASE).strip()

    elif "minute" in time_str_lower:
        unit = "minute"
        match = re.match(r"(\d+)\s*minute", time_str_lower)
        if match:
            val = match.group(1)
    elif "hour" in time_str_lower:
        unit = "hour"
        match = re.match(r"(\d+)\s*hour", time_str_lower)
        if match:
            val = match.group(1)

    if not val and not unit: # Si no se pudo parsear, es especial
        unit = "special"

    return {"full_description": time_str, "value": val, "unit": unit, "condition": condition}

def parse_range(range_str):
    val = None
    unit = None
    shape = None
    shape_val = None

    range_str_lower = range_str.lower()

    if "self" == range_str_lower:
        val = "self"
    elif "touch" == range_str_lower:
        val = "touch"
    elif "sight" == range_str_lower:
        val = "sight"
    elif "unlimited" == range_str_lower:
        val = "unlimited"
    elif "special" == range_str_lower:
        val = "special"
    else:
        # Intentar extraer valor numérico y unidad
        match_feet = re.match(r"(\d+)\s*feet", range_str_lower)
        match_mile = re.match(r"(\d+)\s*mile", range_str_lower)
        if match_feet:
            val = match_feet.group(1)
            unit = "feet"
        elif match_mile:
            val = match_mile.group(1)
            unit = "mile"

        # Intentar extraer forma y valor de forma para casos como "Self (15-foot cone)"
        # o "60 feet (10-foot-radius sphere)"
        # Esta parte puede ser compleja y necesitar más refinamiento
        if "(" in range_str and ")" in range_str:
            shape_part_match = re.search(r"\((.*?)\)", range_str)
            if shape_part_match:
                shape_desc = shape_part_match.group(1).lower()
                # Extraer forma
                if "cone" in shape_desc: shape = "cone"
                elif "cube" in shape_desc: shape = "cube"
                elif "cylinder" in shape_desc: shape = "cylinder"
                elif "line" in shape_desc: shape = "line"
                elif "radius" in shape_desc: shape = "radius" # Podría ser esfera o radio directo
                elif "sphere" in shape_desc: shape = "sphere"

                # Extraer valor de la forma (ej: "15-foot" de "15-foot cone")
                shape_val_match = re.match(r"(\d+-foot)", shape_desc)
                if shape_val_match:
                    shape_val = shape_val_match.group(1)
                elif shape: # si hay forma pero no valor numérico claro, tomar toda la descripción
                    shape_val = shape_desc

                # Si el rango principal era 'Self' y hay forma, se mantiene 'Self' como valor principal
                if val == "self" and not unit:
                    pass # ya está bien
                elif not val and shape: # Si no se pudo parsear valor numérico antes de la forma, pero hay forma
                    if "self" in range_str_lower.split("(")[0]: # ej "Self (10-foot radius)"
                        val = "self"


    if not val and not unit and not shape: # Si nada se parseó, es especial
        val = "special"

    return {"full_description": range_str, "value": val, "unit": unit, "shape": shape, "shape_value": shape_val}


def create_spell_xml_element(spell_data, root_compendium):
    """
    Crea un elemento XML <spell> a partir de los datos del hechizo parseados.
    """
    spell_el = ET.Element("spell")

    ET.SubElement(spell_el, "name").text = spell_data.get("name")
    ET.SubElement(spell_el, "level").text = spell_data.get("level")

    school_code = spell_data.get("school_code")
    school_el = ET.SubElement(spell_el, "school", code=school_code)
    school_el.text = SCHOOL_MAP.get(school_code, school_code) # Nombre completo

    if spell_data.get("ritual") == "YES":
        ET.SubElement(spell_el, "ritual", available="true")

    # Casting Time
    ct_data = parse_casting_time(spell_data.get("time", ""))
    ct_el = ET.SubElement(spell_el, "casting_time", description=ct_data["full_description"])
    if ct_data["value"]: ET.SubElement(ct_el, "value").text = ct_data["value"]
    if ct_data["unit"]: ET.SubElement(ct_el, "unit").text = ct_data["unit"]
    if ct_data["condition"]: ET.SubElement(ET.SubElement(ct_el, "condition"), "text").text = ct_data["condition"]

    # Range
    r_data = parse_range(spell_data.get("range", ""))
    r_el = ET.SubElement(spell_el, "range", description=r_data["full_description"])
    if r_data["value"]: ET.SubElement(r_el, "value").text = r_data["value"]
    if r_data["unit"]: ET.SubElement(r_el, "unit").text = r_data["unit"]
    if r_data["shape"]: ET.SubElement(r_el, "shape").text = r_data["shape"]
    if r_data["shape_value"]: ET.SubElement(r_el, "shape_value").text = r_data["shape_value"]

    # Components
    comp_str = spell_data.get("components", "")
    if comp_str:
        comps_el = ET.SubElement(spell_el, "components")
        if "V" in comp_str.split(",")[0] or (len(comp_str.split(",")) > 1 and "V" in comp_str.split(",")[1].strip()): # Maneja "V, S" y "S, V"
             if not re.search(r"[a-zA-Z]V", comp_str): # Evitar que 'EV' se tome como 'V'
                ET.SubElement(comps_el, "verbal")
        if "S" in comp_str:
             ET.SubElement(comps_el, "somatic")

        materials = parse_material_components(comp_str)
        for mat in materials:
            mat_el = ET.SubElement(comps_el, "material")
            mat_el.text = mat["description"]
            if mat["consumed"]: mat_el.set("consumed", "true")
            if mat["cost_gp"]: mat_el.set("cost_gp", mat["cost_gp"])
            if mat["cost_text"] and not mat["cost_gp"]: # Solo si no hay cost_gp para evitar redundancia
                 mat_el.set("cost_text", mat["cost_text"])
            elif mat["cost_text"] and mat["cost_gp"] and mat["cost_text"] != f"{mat['cost_gp']}+ GP" and mat["cost_text"] != f"{mat['cost_gp']} GP":
                 # Si cost_text es más específico que solo el valor numérico de GP
                 mat_el.set("cost_text", mat["cost_text"])


    # Duration
    dur_data = parse_duration(spell_data.get("duration", ""))
    dur_el = ET.SubElement(spell_el, "duration", description=dur_data["full_description"])
    if dur_data["value"]: ET.SubElement(dur_el, "value").text = dur_data["value"]
    if dur_data["unit"]: ET.SubElement(dur_el, "unit").text = dur_data["unit"]
    if dur_data["concentration"]:
        conc_el = ET.SubElement(dur_el, "concentration", available="true")
        if dur_data["up_to"]:
            conc_el.set("up_to", "true")

    # Description
    desc_text = spell_data.get("text", "")
    desc_el = ET.SubElement(spell_el, "description")
    if desc_text:
        # Dividir el texto en bloques que pueden ser párrafos o listas
        # Un bloque es separado por uno o más saltos de línea.
        # Luego, cada bloque se procesa para ver si es una lista o un párrafo.
        blocks = re.split(r'\n\s*\n+', desc_text.strip()) # Uno o más saltos de línea como separador
        for block_text in blocks:
            block_text = block_text.strip()
            if not block_text:
                continue

            # Intentar detectar si el bloque es una lista (líneas empiezan con *, -, o número seguido de punto)
            lines = block_text.split('\n')
            is_list = False
            if len(lines) > 1: # Una lista debe tener al menos dos items para ser claramente una lista
                is_list = all(re.match(r"^\s*(\*|-|\d+\.)\s+", line.strip()) for line in lines if line.strip())
            elif len(lines) == 1 and re.match(r"^\s*(\*|-|\d+\.)\s+", lines[0].strip()):
                # Considerar una sola línea con viñeta como un párrafo normal por ahora,
                # a menos que se decida que debe ser una lista de un solo item.
                # Por simplicidad, lo trataremos como párrafo.
                pass


            if is_list:
                list_el = ET.SubElement(desc_el, "list")
                # Determinar tipo de lista (bullet o ordered) - heurística simple
                if any(re.match(r"^\s*\d+\.\s+", line.strip()) for line in lines if line.strip()):
                    list_el.set("type", "ordered")
                else:
                    list_el.set("type", "bullet")

                for line in lines:
                    line_content = line.strip()
                    if line_content:
                        # Remover el marcador de lista (asterisco, guion, número. )
                        item_text = re.sub(r"^\s*(\*|-|\d+\.)\s*", "", line_content).strip()
                        ET.SubElement(list_el, "item").text = item_text
            else:
                # Si no es una lista, tratar el bloque como un párrafo (o múltiples si hay solo \n)
                # La división original por \n\s*\n|\n\t ya maneja párrafos separados por tabulación.
                # Aquí, block_text es un párrafo.
                # Si block_text aún contiene \n (pero no \n\s*\n), son saltos de línea suaves.
                # Por ahora, el glosario no especifica manejo de <br/>, así que tratamos el bloque como un solo <p>.
                # Si se necesita más granularidad, se podría dividir block_text por \n y crear múltiples <p>.
                # Sin embargo, la división inicial de `paragraphs` en `create_spell_xml_element` ya hace esto.
                # Esta nueva lógica de `blocks` reemplaza la anterior.
                # Cada `block_text` aquí es un párrafo.
                ET.SubElement(desc_el, "p").text = block_text.replace("\t"," ")


    # Classes
    classes_text = spell_data.get("classes", "")
    classes_el = ET.SubElement(spell_el, "classes", text_original=classes_text)
    raw_class_list = classes_text.replace("School: ", "").split(", ") # Quitar "School: " si está
    parsed_classes = set()
    for c_item in raw_class_list:
        c_item_clean = c_item.strip()
        if not c_item_clean: continue

        # Extraer nombre de clase base y posible información de subclase
        # Ej: "Bard [2024]", "Cleric [2024] (Life Domain)", "Wizard"

        subclass_name = None
        subclass_match = re.search(r'\((.*?)\)', c_item_clean)
        if subclass_match:
            subclass_name = subclass_match.group(1).strip()
            # Remover la parte de la subclase del item para obtener el nombre de clase limpio
            c_name_part = c_item_clean.split("(")[0].strip()
        else:
            c_name_part = c_item_clean

        # Remover el año y corchetes si existen, ej. "[2024]"
        class_name_base = re.sub(r'\s*\[.*?\]', '', c_name_part).strip()

        if class_name_base and class_name_base not in SCHOOL_MAP.values() and class_name_base.lower() != school_code.lower():
            if class_name_base not in parsed_classes:
                ET.SubElement(classes_el, "class_name").text = class_name_base
                parsed_classes.add(class_name_base)

            if subclass_name:
                # Verificar si la subclase ya fue añadida para esta clase (evitar duplicados si el formato es redundante)
                # Esto requiere chequear los hijos existentes de classes_el, un poco más complejo.
                # Por ahora, asumimos que no habrá duplicados exactos de subclase por clase en la entrada.
                ET.SubElement(classes_el, "subclass_restriction", for_class=class_name_base, name=subclass_name)

    # Source
    source_text = spell_data.get("source_info", "")
    if source_text:
        # Regex mejorada para capturar nombres de fuente con espacios y opcionalmente "Source: "
        source_match = re.search(r"(?:Source:\s*)?(.*?)\s*p\.\s*(\d+)", source_text, re.IGNORECASE)
        if source_match:
            book_name = source_match.group(1).strip()
            page_num = source_match.group(2).strip()
            ET.SubElement(spell_el, "source", name=book_name, page=page_num)
        elif "SRD" in source_text.upper(): # Caso para SRD sin número de página
             ET.SubElement(spell_el, "source", name="SRD")


    # Rolls
    if "rolls" in spell_data and spell_data["rolls"]:
        for roll_info in spell_data["rolls"]:
            roll_el = ET.SubElement(spell_el, "roll", description=roll_info.get("description",""))
            # Asumir type=damage si no se especifica otra cosa
            roll_el.set("type", roll_info.get("type", "damage"))
            ET.SubElement(roll_el, "dice").text = roll_info.get("dice")
            if "damage_type" in roll_info:
                 ET.SubElement(roll_el, "damage_type").text = roll_info["damage_type"]
            # Aquí se podría añadir más detalle para los rolls si es necesario

    # At Higher Levels
    ahl_el = ET.SubElement(spell_el, "at_higher_levels")
    raw_desc_text_for_ahl = spell_data.get("text_for_ahl", "") # Usar el texto antes de quitar AHL

    # Limpiar el texto de AHL de la información de la fuente ANTES de parsear
    raw_desc_text_for_ahl = raw_desc_text_for_ahl.split("Source:")[0].strip()

    cantrip_upgrade_match = re.search(r"Cantrip Upgrade:\s*(.*)", raw_desc_text_for_ahl, re.IGNORECASE | re.DOTALL)
    higher_level_match = re.search(r"Using a Higher-Level Spell Slot:\s*(.*)", raw_desc_text_for_ahl, re.IGNORECASE | re.DOTALL)

    parsed_structured_ahl = False

    if cantrip_upgrade_match:
        text_content = cantrip_upgrade_match.group(1).strip()

        # Regex mejorada para capturar múltiples niveles de escalado de cantrip de forma más robusta.
        # Busca "level X (efecto)" o "levels X (efecto), Y (efecto), and Z (efecto)"
        # Patrón para un solo nivel de escalado: levels? (\d+)\s*\((.*?)\)
        # El uso de DOTALL es importante si el efecto tiene saltos de línea.

        # Primero, intentar un patrón más simple que busca "level X (description)" repetidamente.
        # Usamos finditer para capturar todos los escalados.
        scaling_entries = re.finditer(r"level(?:s)?\s*(\d+)\s*\((.*?)\)(?=[,.]?|$|\s*level|\s*and)", text_content, re.IGNORECASE | re.DOTALL)

        count_scalings_found = 0
        for entry in scaling_entries:
            count_scalings_found +=1
            level = entry.group(1).strip()
            effect_text = entry.group(2).strip()

            # Limpiar efecto de frases como "and at level..." si la regex las incluye accidentalmente
            effect_text = re.sub(r",?\s*and\s+at\s+level.*$", "", effect_text, flags=re.IGNORECASE | re.DOTALL).strip()

            if level and effect_text:
                scaling_el = ET.SubElement(ahl_el, "scaling", level=level)
                ET.SubElement(scaling_el, "effect", description=effect_text)
                parsed_structured_ahl = True

        # Si no se parseó nada estructurado pero había texto de Cantrip Upgrade, usar text_block
        if not parsed_structured_ahl and text_content:
            ET.SubElement(ahl_el, "text_block", title="Cantrip Upgrade").text = text_content
        # Si se parseó algo pero queda texto residual significativo, añadirlo.
        # Esto es más complejo de determinar. Por ahora, priorizamos la estructura.

    elif higher_level_match:
        text_content = higher_level_match.group(1).strip()
        processed_text_for_block = text_content # Texto que podría ir al text_block si no se parsea nada más.

        # 1. Parsear "For each slot level above X..."
        #    Regex mejorada para capturar la descripción del efecto de forma más completa.
        #    Captura (descripción del incremento) for each slot level above (nivel base).
        #    Ej: "The damage increases by 1d8 for each slot level above 1st."
        #    Ej: "You can target one additional creature for each slot level above 2nd."
        per_slot_pattern = re.compile(
            r"(.+?)\s+for\s+each\s+(?:spell\s+slot\s+level|slot\s+level)\s+above\s+(\d+)(?:st|nd|rd|th)?\.?",
            re.IGNORECASE | re.DOTALL
        )

        for match in per_slot_pattern.finditer(text_content):
            effect_description = match.group(1).strip()
            base_level = match.group(2).strip()

            per_slot_el = ET.SubElement(ahl_el, "per_slot_above", base_level=base_level)
            effect_el = ET.SubElement(per_slot_el, "effect", description=effect_description)
            parsed_structured_ahl = True

            # Intentar extraer sub-elementos del effect_description
            roll_increase_match = re.search(r"(?:increases\s+by|add)\s*(\d+d\d+)", effect_description, re.IGNORECASE)
            if roll_increase_match:
                ET.SubElement(effect_el, "roll_increase", increase_dice=roll_increase_match.group(1))

            additional_target_match = re.search(r"(?:target|affect)\s*(one|two|an|\d+)\s*additional\s*(?:creature|target|object|bolt|dart|ray|missile|foe|enemy|ally|construct|corpse|skeleton|zombie|ghoul|wight|mummy|beam|stone|gem|construct|weapon|item|glyph|symbol|trap|ward|illusion|duplicate|image|manifestation|servant|spirit|guardian|elemental|fiend|celestial|fey|undead|plant|beast|ooze|swarm|humanoid|giant|dragon|aberration|monstrosity|construct|undead|celestial|fiend|elemental|fey|plant|beast|ooze|swarm|humanoid|giant|dragon|aberration|monstrosity)s?", effect_description, re.IGNORECASE)
            if additional_target_match:
                count_str = additional_target_match.group(1).lower()
                num_additional = "1"
                if count_str == "two": num_additional = "2"
                elif count_str.isdigit(): num_additional = count_str
                elif count_str == "an": num_additional = "1"
                ET.SubElement(effect_el, "additional_targets", count=num_additional)

            duration_increase_match = re.search(r"duration\s+increases\s+by\s*(\d+)\s*(hour|minute|round|day|week|month|year)s?", effect_description, re.IGNORECASE)
            if duration_increase_match:
                ET.SubElement(effect_el, "duration_increase", value=duration_increase_match.group(1), unit=duration_increase_match.group(2).lower())

            # Remover el texto procesado del `processed_text_for_block`
            processed_text_for_block = processed_text_for_block.replace(match.group(0), "").strip()


        # 2. Parsear "When you cast this spell using a spell slot of Xth level or higher, Y happens."
        #    o "If you use a level X spell slot, Y happens."
        #    Esta regex es compleja. Priorizar frases completas.
        specific_slot_pattern = re.compile(
            r"(?:When\s+you\s+cast\s+this\s+spell\s+using|If\s+you\s+use)\s+a\s+(?:spell\s+slot\s+of\s+|level\s+)?(\d+)(?:st|nd|rd|th)?(?:-level)?(?:\s+level)?(?:\s+or\s+higher)?(?:,\s*|\s+spell\s+slot,\s*|\s*slot,\s*)(.*?)\.(?=\s*(?:When|If|Using|$))",
            re.IGNORECASE | re.DOTALL
        )

        for match in specific_slot_pattern.finditer(text_content): # Iterar sobre el text_content original para no perder matches
            slot_level = match.group(1).strip()
            effect_description = match.group(2).strip()

            specific_el = ET.SubElement(ahl_el, "specific_slot", level=slot_level)
            ET.SubElement(specific_el, "effect", description=effect_description)
            parsed_structured_ahl = True

            # Remover el texto procesado del `processed_text_for_block`
            # Cuidado aquí si los matches se solapan. finditer ayuda.
            processed_text_for_block = processed_text_for_block.replace(match.group(0), "").strip()

        # Si queda texto en processed_text_for_block después de los parseos estructurados,
        # o si no se parseó nada estructurado pero había contenido de AHL.
        processed_text_for_block = processed_text_for_block.strip(' .') # limpiar puntos o espacios residuales
        if processed_text_for_block:
            ET.SubElement(ahl_el, "text_block", title="General Higher Level Effects").text = processed_text_for_block
        elif not parsed_structured_ahl and text_content: # Si no se parseó nada estructurado pero había texto
             ET.SubElement(ahl_el, "text_block", title="Using a Higher-Level Spell Slot").text = text_content


    # Si ahl_el no tiene hijos (ni <scaling>, ni <per_slot_above>, ni <specific_slot>, ni <text_block>), removerlo.
    if not list(ahl_el):
        spell_el.remove(ahl_el)

    # Saving Throw (extracción a nivel de hechizo si se encuentra un patrón general)
    # Esto es una heurística y puede necesitar refinamiento.
    # Buscar patrones como "Each creature in [area] must make a [Ability] saving throw."
    # o "[Target] must succeed on a [Ability] saving throw or [effect]."

    # Primero, buscar en la descripción general del hechizo.
    # Se asume que spell_data["text"] contiene la descripción principal sin AHL.
    main_desc_text = spell_data.get("text", "")
    saving_throw_match = re.search(
        r"(?:Each creature|The target|A creature|Each target|Any creature)(?:.*?)(must make|must succeed on) an?\s+(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s+saving throw(?:.*?)(?:or|On a failed save,|On a failure,)([^.]+)\.(?:\s*On a successful save(?:,|.)\s*([^.]+)\.?)?",
        main_desc_text, re.IGNORECASE | re.DOTALL
    )

    if saving_throw_match:
        ability = saving_throw_match.group(2).capitalize()
        # effect_on_failure = saving_throw_match.group(4).strip() if saving_throw_match.group(4) else "See description"
        # effect_on_success = saving_throw_match.group(5).strip() if saving_throw_match.group(5) else "None or see description"

        # Simplificado por ahora: solo capturar la habilidad si el patrón es claro.
        # La DC y efectos detallados son más complejos de extraer de forma genérica y confiable del texto libre.
        # El glosario también menciona dc_formula="caster's spell save DC" como un posible valor.

        # Evitar añadir <saving_throw> si ya hay <roll><save_details> que lo cubran.
        # Esta lógica es compleja de integrar aquí sin conocer el contexto completo de los rolls.
        # Por ahora, añadimos si encontramos un patrón claro en el texto.

        # Chequear si ya existe un saving_throw para no duplicar (aunque la lógica actual no lo haría)
        if not spell_el.find("saving_throw"):
            st_el = ET.SubElement(spell_el, "saving_throw", ability=ability)
            # Podríamos añadir dc_formula="[8+ProficiencyBonus+SPELL]" por defecto si no se especifica.
            # st_el.set("effect_on_failure", effect_on_failure)
            # st_el.set("effect_on_success", effect_on_success)
            # Notas pueden ser útiles aquí.

    return spell_el

def main():
    input_file = "deprecated/spells-phb24.xml"
    output_dir = "01_Core/01_Players_Handbook_2024/"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    tree = ET.parse(input_file)
    root = tree.getroot()

    # Diccionario para almacenar hechizos por escuela
    spells_by_school = {code: [] for code in SCHOOL_MAP.keys()}

    for spell_node in root.findall("spell"):
        data = {}
        data["name"] = spell_node.find("name").text if spell_node.find("name") is not None else ""
        data["level"] = spell_node.find("level").text if spell_node.find("level") is not None else ""
        data["school_code"] = spell_node.find("school").text if spell_node.find("school") is not None else ""
        data["ritual"] = spell_node.find("ritual").text if spell_node.find("ritual") is not None else "NO"
        data["time"] = spell_node.find("time").text if spell_node.find("time") is not None else ""
        data["range"] = spell_node.find("range").text if spell_node.find("range") is not None else ""
        data["components"] = spell_node.find("components").text if spell_node.find("components") is not None else ""
        data["duration"] = spell_node.find("duration").text if spell_node.find("duration") is not None else ""

        full_text_orig = spell_node.find("text").text if spell_node.find("text") is not None else ""
        data["text_for_ahl"] = full_text_orig # Guardar el texto original para parsear AHL

        # Separar la información de la fuente y AHL del texto principal
        source_info_match = re.search(r"Source:\s*(.*?)(?:\n|$)", full_text_orig, re.DOTALL)

        text_to_parse_for_desc = full_text_orig
        if source_info_match:
            data["source_info"] = source_info_match.group(0).strip()
            text_to_parse_for_desc = text_to_parse_for_desc.replace(data["source_info"], "").strip()
        else:
            data["source_info"] = ""

        # Remover las secciones de AHL del texto que va a la descripción principal
        text_to_parse_for_desc = re.sub(r"Cantrip Upgrade:.*?(?=\n\n|Source:|$)", "", text_to_parse_for_desc, flags=re.IGNORECASE | re.DOTALL).strip()
        text_to_parse_for_desc = re.sub(r"Using a Higher-Level Spell Slot:.*?(?=\n\n|Source:|$)", "", text_to_parse_for_desc, flags=re.IGNORECASE | re.DOTALL).strip()

        data["text"] = text_to_parse_for_desc.strip()


        data["classes"] = spell_node.find("classes").text if spell_node.find("classes") is not None else ""

        data["rolls"] = []
        for roll_node in spell_node.findall("roll"):
            roll_data = {"dice": roll_node.text}
            if "description" in roll_node.attrib:
                roll_data["description"] = roll_node.attrib["description"]

            # Heurística simple para tipo de daño desde descripción
            desc_lower = roll_data.get("description","").lower()
            if "acid" in desc_lower: roll_data["damage_type"] = "Acid"
            elif "cold" in desc_lower: roll_data["damage_type"] = "Cold"
            elif "fire" in desc_lower: roll_data["damage_type"] = "Fire"
            elif "force" in desc_lower: roll_data["damage_type"] = "Force"
            elif "lightning" in desc_lower: roll_data["damage_type"] = "Lightning"
            elif "necrotic" in desc_lower: roll_data["damage_type"] = "Necrotic"
            elif "piercing" in desc_lower: roll_data["damage_type"] = "Piercing"
            elif "poison" in desc_lower: roll_data["damage_type"] = "Poison"
            elif "psychic" in desc_lower: roll_data["damage_type"] = "Psychic"
            elif "radiant" in desc_lower: roll_data["damage_type"] = "Radiant"
            elif "slashing" in desc_lower: roll_data["damage_type"] = "Slashing"
            elif "thunder" in desc_lower: roll_data["damage_type"] = "Thunder"
            elif "bludgeoning" in desc_lower: roll_data["damage_type"] = "Bludgeoning"
            elif "elemental damage" in desc_lower: roll_data["damage_type"] = "Elemental (Choose)" # Para Chromatic Orb

            if "heal" in desc_lower: roll_data["type"] = "healing"
            if "subtract from roll" in desc_lower: roll_data["type"] = "effect"
            if "add to roll" in desc_lower: roll_data["type"] = "effect"


            data["rolls"].append(roll_data)

        if data["school_code"] in spells_by_school:
            spells_by_school[data["school_code"]].append(data)
        else:
            print(f"Advertencia: Escuela desconocida '{data['school_code']}' para el hechizo '{data['name']}'. Se omitirá.")

    # Crear archivos XML por escuela
    for school_code, spell_list in spells_by_school.items():
        if not spell_list:
            continue

        school_filename_part = SCHOOL_FILENAME_MAP.get(school_code)
        if not school_filename_part:
            print(f"Error: No se encontró mapeo de nombre de archivo para la escuela {school_code}")
            continue

        output_filename = os.path.join(output_dir, f"spells-{school_filename_part}-phb24.xml")

        # Crear el elemento raíz del compendio para este archivo de escuela
        school_compendium_root = ET.Element("compendium", version="5", auto_indent="NO")

        for spell_data_item in spell_list:
            spell_xml_el = create_spell_xml_element(spell_data_item, school_compendium_root)
            school_compendium_root.append(spell_xml_el)

        # Escribir el árbol XML al archivo
        tree_out = ET.ElementTree(school_compendium_root)
        ET.indent(tree_out, space="  ", level=0) # Para indentación bonita
        tree_out.write(output_filename, encoding="UTF-8", xml_declaration=True)
        print(f"Archivo de hechizos creado: {output_filename}")

if __name__ == "__main__":
    main()
    print("Parseo de hechizos completado.")
