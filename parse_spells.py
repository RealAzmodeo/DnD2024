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
        m_part = components_str.split("M (", 1)[1].rsplit(")", 1)[0]
        # Dividir por ", and " o " and " si hay múltiples materiales con costos separados (raro para PHB pero posible)
        # Por ahora, asumimos un único bloque de material complejo o varios simples.
        # Esta lógica necesitará ser más robusta si hay múltiples materiales con costos individuales dentro del mismo paréntesis.

        material_desc = m_part
        consumed = "which the spell consumes" in m_part or "which the spell consume" in m_part

        # Re-evaluación de costos:
        cost_gp = None
        cost_text = None

        # Prioridad 1: "worth X+ GP" o "worth X GP" (incluyendo comas en números)
        m_worth = re.search(r"worth\s*([\d,]+)\+?\s*GP", material_desc, re.IGNORECASE)
        if m_worth:
            cost_gp_str = m_worth.group(1).replace(",", "")
            if cost_gp_str.isdigit():
                cost_gp = cost_gp_str
            cost_text = f"worth {m_worth.group(1)}{'+' if '+' in m_worth.group(0) else ''} GP"
        else:
            # Prioridad 2: "(X GP)" o "(X+ GP)" o "X GP" o "X+ GP" (para costos directos sin "worth")
            # Primero buscar con paréntesis, ya que es más específico para costos.
            m_gp_direct = re.search(r"\(([\d,]+)\+?\s*GP\)", material_desc, re.IGNORECASE) # Busca (X GP) o (X+ GP)
            if not m_gp_direct: # Si no encuentra con paréntesis, busca sin ellos
                 m_gp_direct = re.search(r"([\d,]+)\+?\s*GP", material_desc, re.IGNORECASE) # Busca X GP o X+ GP

            if m_gp_direct:
                # Verificar que "worth" no esté inmediatamente antes para evitar solapamiento con la Prioridad 1
                # (aunque la estructura if/else ya debería prevenir esto, es una doble seguridad)
                preceding_text_window = material_desc[max(0, m_gp_direct.start() - 7):m_gp_direct.start()].lower()
                if "worth" not in preceding_text_window:
                    cost_gp_str = m_gp_direct.group(1).replace(",", "")
                    if cost_gp_str.isdigit():
                        cost_gp = cost_gp_str
                    cost_text = f"{m_gp_direct.group(1)}{'+' if '+' in m_gp_direct.group(0) else ''} GP"

        # Si cost_text no se estableció (es decir, no hay "worth X GP" ni "X GP" claro como costo)
        # pero hay alguna mención de GP en el texto, la capturamos como parte de cost_text.
        # Esto es para casos como "a statuette of the target made from a material worth 100 GP"
        # donde el "100 GP" no es el costo directo del *material* sino una cualidad.
        if not cost_text:
            gp_mention_match = re.search(r"([\d,]+\+?\s*GP)", material_desc, re.IGNORECASE)
            if gp_mention_match:
                cost_text = gp_mention_match.group(1) # ej. "100 GP"

        # Limpiar la descripción del material de la frase de consumo.
        # La limpieza del costo es más compleja y se manejará al asignar al XML.
        clean_description = re.sub(r",?\s*which the spell consumes", "", material_desc, flags=re.IGNORECASE).strip()
        if clean_description.endswith(','):
            clean_description = clean_description[:-1].strip()

        # Si cost_gp se encontró, intentar refinar la descripción para no incluir el costo exacto.
        if cost_gp and cost_text:
            # Construir un patrón regex para la parte del costo que se encontró.
            # Ejemplo: cost_text = "worth 1,000+ GP" -> pattern = r"worth\s*1,000\+\s*GP"
            # Ejemplo: cost_text = "50 GP" -> pattern = r"50\s*GP"
            # Ejemplo: cost_text = "(25+ GP)" -> pattern = r"\(\s*25\+\s*GP\s*\)"

            pattern_to_remove_str = re.escape(cost_text)
            # Hacer el patrón más flexible con espacios
            pattern_to_remove_str = re.sub(r"\\ ", r"\\s*", pattern_to_remove_str)
            pattern_to_remove_str = re.sub(r"worth\\s\*", r"worth\\s*", pattern_to_remove_str, flags=re.IGNORECASE)

            # Intentar remover la frase de costo de la descripción
            temp_desc = re.sub(r",?\s*" + pattern_to_remove_str, "", clean_description, flags=re.IGNORECASE).strip()

            # Si la descripción cambió y no está vacía, usarla. Sino, usar la original menos la frase de consumo.
            if temp_desc and temp_desc != clean_description:
                clean_description = temp_desc

            # Quitar comas residuales al inicio o final
            if clean_description.startswith(','): clean_description = clean_description[1:].strip()
            if clean_description.endswith(','): clean_description = clean_description[:-1].strip()

        materials.append({
            "description": clean_description if clean_description else material_desc.replace(", which the spell consumes","").strip(), # Fallback
            "consumed": consumed,
            "cost_gp": cost_gp,
            "cost_text": cost_text
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

    # Description (simple por ahora, solo párrafos)
    desc_text = spell_data.get("text", "")
    desc_el = ET.SubElement(spell_el, "description")
    if desc_text:
        # Dividir el texto en párrafos basados en saltos de línea dobles o tabulaciones iniciales
        paragraphs = re.split(r'\n\s*\n|\n\t', desc_text.strip())
        for p_text in paragraphs:
            if p_text.strip():
                ET.SubElement(desc_el, "p").text = p_text.strip().replace("\t"," ")

    # Classes
    classes_text = spell_data.get("classes", "")
    classes_el = ET.SubElement(spell_el, "classes", text_original=classes_text)
    # Simple parse for now, can be improved
    raw_class_list = classes_text.replace("School: ", "").split(", ")
    parsed_classes = set()
    for c_item in raw_class_list:
        c_name = c_item.split("[")[0].strip() # "Sorcerer [2024]" -> "Sorcerer"
        if c_name and c_name not in SCHOOL_MAP.values() and c_name != school_code: # Evitar añadir la escuela como clase
            if c_name not in parsed_classes:
                 ET.SubElement(classes_el, "class_name").text = c_name
                 parsed_classes.add(c_name)
        # Podría añadirse lógica para subclases aquí
        if "[" in c_item and "(" in c_item: # Ej: "Druid [2024] (Tropical Land)"
            subclass_match = re.search(r'\((.*?)\)', c_item)
            if subclass_match:
                subclass_name = subclass_match.group(1)
                parent_class = c_item.split("[")[0].strip()
                ET.SubElement(classes_el, "subclass_restriction", for_class=parent_class, name=subclass_name)


    # Source (asumiendo que está en el texto del hechizo)
    source_text = spell_data.get("source_info", "") # Esto vendrá de parsear el final del <text>
    if source_text:
         source_match = re.search(r"Source:\s*(.*?)\s*p\.\s*(\d+)", source_text)
         if source_match:
             ET.SubElement(spell_el, "source", name=source_match.group(1).strip(), page=source_match.group(2).strip())


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

    cantrip_upgrade_match = re.search(r"Cantrip Upgrade:\s*(.*)", raw_desc_text_for_ahl, re.IGNORECASE)
    higher_level_match = re.search(r"Using a Higher-Level Spell Slot:\s*(.*)", raw_desc_text_for_ahl, re.IGNORECASE)

    if cantrip_upgrade_match:
        text_content = cantrip_upgrade_match.group(1).strip()
        text_content = text_content.split("Source:")[0].strip() # Remover la parte de "Source:"

        scaling_matches = re.findall(r"levels?\s*(\d+)\s*\((.*?)\)(?:,\s*(\d+)\s*\((.*?)\))?(?:,\s*and\s*(\d+)\s*\((.*?)\))?", text_content, re.IGNORECASE)

        parsed_specific_cantrip_scaling = False
        if scaling_matches:
            for match_group in scaling_matches:
                levels_effects_pairs = []
                if match_group[0] and match_group[1]: levels_effects_pairs.append((match_group[0], match_group[1]))
                if match_group[2] and match_group[3]: levels_effects_pairs.append((match_group[2], match_group[3]))
                if match_group[4] and match_group[5]: levels_effects_pairs.append((match_group[4], match_group[5]))

                if levels_effects_pairs: # Solo si encontramos pares válidos
                    parsed_specific_cantrip_scaling = True
                    for level, effect_text in levels_effects_pairs:
                        level = level.strip()
                        effect_text = effect_text.strip()
                        scaling_el = ET.SubElement(ahl_el, "scaling", level=level)
                        ET.SubElement(scaling_el, "effect", description=effect_text)

        if not parsed_specific_cantrip_scaling and text_content:
            # Si no se encontraron patrones de escalado específicos, o si los patrones no dieron resultados,
            # añadir el texto completo como un text_block.
            ET.SubElement(ahl_el, "text_block", title="Cantrip Upgrade").text = text_content
        elif parsed_specific_cantrip_scaling and not all(m is None or m == '' for m in match_group for match_group in scaling_matches): # Si se parsearon algunos, pero quiza no todo
            # Podríamos añadir el text_block original si la regex no capturó toda la frase,
            # pero por ahora, si `scaling_matches` tuvo éxito, preferimos las etiquetas <scaling>.
            # Si se quiere el text_block como fallback incluso si hay <scaling>, se puede añadir aquí.
            # Para evitar redundancia total, no lo añadimos si scaling_matches es exitoso.
            pass



    elif higher_level_match:
        text_content = higher_level_match.group(1).strip()
        text_content = text_content.split("Source:")[0].strip() # Remover la parte de "Source:"

        # Intentar dividir por "for each spell slot level above X"
        per_slot_matches = re.finditer(r"(?:The damage|The healing|The effect|You can target|The (?:Temporary Hit Points|Cold damage|duration|radius|damage and healing|healing and damage|number of unexpended Hit Dice|amount of ammunition|extra damage|damage for both effects|initial damage|Bludgeoning damage|base damage|Cold or Acid damage|number of creatures the vine can grapple) increases by|You animate or reassert control over|one additional bolt leaps from the first target to another target for|The Sphere's radius increases by|The number of unexpended Hit Dice you can roll increases by|The Temporary Hit Points and the Cold damage both increase by|The orb can leap a maximum number of times equal to|The bonus to attack rolls increases to \+(\d+) and the extra damage increases to (\dd\d) for|Your Concentration can last longer with a spell slot of level \d+ \((.*?)\), \d+ \((.*?)\), or \d+\+ \((.*?)\)|The duration is longer with a spell slot of level \d+ \((.*?)\), \d+ \((.*?)\), or \d+ \((.*?)\)|You can alter the target's memories of an event that took place up to (.*?) ago|You can increase the size of the Cube by (\d+ feet) for|The damage of an explosive rune increases by|If you use a level (\d+(?:-\d+)?(?: or \d+)?\+?) spell slot, (.*?)\.)\s*(.*?)\s*for each spell slot level above\s*(\d+)\.", text_content, re.IGNORECASE)

        processed_text = text_content
        found_per_slot = False
        found_specific = False # Inicializar found_specific aquí
        for match in per_slot_matches:
            found_per_slot = True
            # full_sentence = match.group(0) # La oración completa que coincide
            # effect_description_part = match.group(1) # La parte que describe el aumento
            base_level_part = match.group(match.lastindex) # El último grupo es el nivel base

            # Heurística para capturar la descripción del efecto
            # Puede ser complejo si hay múltiples "for each"
            # Tomamos el texto desde el inicio del match hasta "for each"
            # El grupo 1 de la regex `per_slot_matches` ya captura la parte descriptiva del aumento.
            # La regex es compleja, así que nos basaremos en los grupos que define.
            # El último grupo es el nivel base. El penúltimo no vacío antes de eso es la descripción del incremento.

            base_level_part = match.group(match.lastindex)
            effect_description_part = ""
            # Iterar hacia atrás desde el penúltimo grupo para encontrar el texto del efecto.
            # Los grupos intermedios pueden ser None si esas partes opcionales de la regex no coincidieron.
            for i in range(match.lastindex -1, 0, -1):
                if match.group(i):
                    effect_description_part = match.group(i)
                    break

            # El texto completo de la oración que coincidió con "for each"
            full_sentence_of_per_slot_match = match.group(0)


            per_slot_el = ET.SubElement(ahl_el, "per_slot_above", base_level=base_level_part)
            # Usar la frase completa del match como descripción para ser más inclusivo,
            # y luego intentar extraer detalles específicos.
            effect_el = ET.SubElement(per_slot_el, "effect", description=full_sentence_of_per_slot_match.split("for each spell slot level above")[0].strip())

            # Intentar extraer aumento de dado de la parte del efecto
            roll_increase_match = re.search(r"(\d+d\d+)", effect_description_part)
            if roll_increase_match:
                 ET.SubElement(effect_el, "roll_increase", increase_dice=roll_increase_match.group(1))

            additional_target_match = re.search(r"(one|two) additional (creature|target|Beast|Undead creatures|Ghouls|Ghasts or Wights|Mummies)", effect_description_part, re.IGNORECASE)
            if additional_target_match:
                 count_str = additional_target_match.group(1).lower()
                 num_additional = "1"
                 if count_str == "two": num_additional = "2"
                 ET.SubElement(effect_el, "additional_targets", count=num_additional)

            # Remover la parte procesada para el siguiente ciclo o para el text_block final
            processed_text = processed_text.replace(full_sentence_of_per_slot_match, "").strip()

        # Lo que queda en processed_text puede ser una descripción general o mejoras específicas de nivel
        if processed_text:
            # Regex para mejoras de nivel específico (ej. "If you use a level X spell slot, Y happens.")
            # Esta regex intenta capturar múltiples cláusulas "If you use a level X... Y happens. If you use level Z... W happens."
            # Es compleja y puede necesitar ajustes.
            specific_pattern = r"If you use a (?:level|spell slot of level)\s*(\d+(?:-\d+)?(?:(?:,|\s*or)\s*\d+)?\+?)\s*(?:spell slot|slot),\s*(.*?)\.(?:\s*If you use a (?:level|spell slot of level)\s*(\d+(?:-\d+)?(?:(?:,|\s*or)\s*\d+)?\+?)\s*(?:spell slot|slot),\s*(.*?)\.)?(?:\s*If you use a (?:level|spell slot of level)\s*(\d+(?:-\d+)?(?:(?:,|\s*or)\s*\d+)?\+?)\s*(?:spell slot|slot),\s*(.*?)\.)?"

            remaining_for_general_block = processed_text
            # Usamos finditer para encontrar todos los matches no solapados.
            for s_match in re.finditer(specific_pattern, processed_text, re.IGNORECASE):
                found_specific = True

                # Extraer todos los pares de nivel/efecto del match actual
                # Un solo match puede contener hasta 3 niveles/efectos debido a los grupos opcionales
                # groups() devuelve: (level1, effect1, level2, effect2, level3, effect3)
                # donde level2/effect2 y level3/effect3 pueden ser None.
                groups = s_match.groups()

                current_match_text = s_match.group(0) # El texto completo de este match específico

                if groups[0] and groups[1]:
                    specific_el = ET.SubElement(ahl_el, "specific_slot", level=groups[0].replace("+","").strip())
                    ET.SubElement(specific_el, "effect", description=groups[1].strip())
                if groups[2] and groups[3]:
                    specific_el = ET.SubElement(ahl_el, "specific_slot", level=groups[2].replace("+","").strip())
                    ET.SubElement(specific_el, "effect", description=groups[3].strip())
                if groups[4] and groups[5]:
                    specific_el = ET.SubElement(ahl_el, "specific_slot", level=groups[4].replace("+","").strip())
                    ET.SubElement(specific_el, "effect", description=groups[5].strip())

                remaining_for_general_block = remaining_for_general_block.replace(current_match_text, "").strip()

            # Si queda texto después de extraer los patrones de "per_slot_above" y "specific_slot",
            # se añade como un bloque de texto general.
            if remaining_for_general_block.strip('.'): # Evitar añadir solo un punto.
                ET.SubElement(ahl_el, "text_block", title="General Higher Level Effects").text = remaining_for_general_block.strip()

        # Si no se parseó nada específico (ni per_slot ni specific_slot) pero había texto de AHL,
        # poner todo el texto original de AHL en un bloque genérico.
        if not found_per_slot and not found_specific and text_content and not ahl_el.findall("*"):
            ET.SubElement(ahl_el, "text_block", title="Using a Higher-Level Spell Slot").text = text_content


    # Si ahl_el no tiene hijos, removerlo
    if not list(ahl_el):
        spell_el.remove(ahl_el)

    return spell_el

def main():
    input_file = "01_Core/01_Players_Handbook_2024/spells-phb24.xml"
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
    input_file = "01_Core/01_Players_Handbook_2024/spells-phb24.xml"
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

        full_text = spell_node.find("text").text if spell_node.find("text") is not None else ""

        # Separar la información de la fuente del texto principal
        source_info_match = re.search(r"Source:\s*(.*?)(?:\n|$)", full_text, re.DOTALL) # Modificado para capturar hasta fin de línea o fin de texto
        if source_info_match:
            data["source_info"] = source_info_match.group(0).strip()
            # Remover la información de la fuente del texto principal para evitar duplicados en la descripción
            full_text = full_text.replace(data["source_info"], "").strip()
        else:
            data["source_info"] = ""
        data["text"] = full_text

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

            if "heal" in desc_lower: roll_data["type"] = "healing"

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
