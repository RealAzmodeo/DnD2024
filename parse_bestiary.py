import xml.etree.ElementTree as ET
import json
import re

# Glossary-aligned monster template
monster_glossary_template = {
    "name": "",
    "sort_name": "",
    "ancestry": "",
    "source": {
        "book": "",
        "page": "",
        "other_sources": ""
    },
    "description_text": "",
    "flavor_text": [], # This will be a list of {"title": "...", "text_block": ["paragraph1", "table_string_or_paragraph2"]}
    "size": {
        "code": "",
        "full_name": ""
    },
    "creature_type": {
        "type": "",
        "tags": []
    },
    "alignment": {
        "abbreviation": "",
        "text_override": ""
    },
    "statistics": {
        "strength": {"score": 0},
        "dexterity": {"score": 0},
        "constitution": {"score": 0},
        "intelligence": {"score": 0},
        "wisdom": {"score": 0},
        "charisma": {"score": 0}
    },
    "defenses": {
        "armor_class": {
            "value": 0,
            "description": ""
        },
        "hit_points": {
            "average": 0,
            "formula": "",
            "notes": ""
        },
        "saving_throw_proficiencies": [],
        "damage_resistances": {
            "list": [], "notes": ""
        },
        "damage_immunities": {
            "list": [], "notes": ""
        },
        "damage_vulnerabilities": {
            "list": [], "notes": ""
        },
        "condition_immunities": {
            "list": [], "notes": ""
        }
    },
    "speed": {
        "walk": {"value": "", "notes": ""},
        "fly": {"value": "", "hover": False, "notes": ""},
        "swim": {"value": "", "notes": ""},
        "burrow": {"value": "", "notes": ""},
        "climb": {"value": "", "notes": ""},
        "notes": ""
    },
    "senses": {
        "sense_list": [],
        "passive_perception": {"value": 0},
        "notes": ""
    },
    "languages": {
        "language_list": [],
        "telepathy": {"range": ""},
        "understands_but_cant_speak": {"list": []},
        "notes": ""
    },
    "challenge_rating": {
        "value": "",
        "xp_value": 0
    },
    "proficiency_bonus": {"value": ""},
    "skill_proficiencies": [],
    "traits": [],
    "actions": [],
    "bonus_actions": [],
    "reactions": [],
    "legendary_actions": {
        "per_turn": 0,
        "actions_list": []
    },
    "mythic_actions": {
        "actions_list": []
    },
    "lair_actions": {
        "actions_list": []
    },
    "regional_effects": {
        "effects_list": []
    },
    "spellcasting": {
        "type": "",
        "ability": "",
        "spell_save_dc": "",
        "attack_bonus": "",
        "at_will": [],
        "per_day": [],
        "spell_slots": [],
        "known_spells": [],
        "prepared_spells": []
    },
    "equipment": [],
    "environment_tags": {"tags": []},
    "source_file": ""
}

def get_monster_name(monster_element):
    name_tag = monster_element.find('name')
    return name_tag.text.strip() if name_tag is not None and name_tag.text else "Unnamed Monster"

def initialize_monster_data(monster_element, filename):
    new_monster_data = json.loads(json.dumps(monster_glossary_template))
    new_monster_data["name"] = get_monster_name(monster_element)
    new_monster_data["source_file"] = filename
    return new_monster_data

def get_text(element, path=None, default=""): # Modified to allow direct text from element if path is None
    if path:
        found = element.find(path)
    else: # If no path, assume we want text from the element itself
        found = element

    if found is not None and found.text:
        return found.text.strip()
    return default

def parse_core_details(monster_element, monster_data):
    monster_data['sort_name'] = get_text(monster_element, 'sortname')
    monster_data['ancestry'] = get_text(monster_element, 'ancestry')

    size_code = get_text(monster_element, 'size')
    monster_data['size']['code'] = size_code
    size_map = {
        "T": "Tiny", "S": "Small", "M": "Medium",
        "L": "Large", "H": "Huge", "G": "Gargantuan"
    }
    monster_data['size']['full_name'] = size_map.get(size_code, size_code)

    type_text = get_text(monster_element, 'type')
    type_match = re.match(r"([\w\s]+)(?:\s*\((.*?)\))?", type_text)
    if type_match:
        monster_data['creature_type']['type'] = type_match.group(1).strip().lower() # Standardize to lowercase
        if type_match.group(2):
            monster_data['creature_type']['tags'] = [tag.strip().lower() for tag in type_match.group(2).split(',')]
    else:
        monster_data['creature_type']['type'] = type_text.lower()

    alignment_text = get_text(monster_element, 'alignment')
    alignment_map_full_to_abbr = {
        "lawful good": "LG", "neutral good": "NG", "chaotic good": "CG",
        "lawful neutral": "LN", "neutral": "N", "chaotic neutral": "CN",
        "lawful evil": "LE", "neutral evil": "NE", "chaotic evil": "CE",
        "unaligned": "Unaligned", "any alignment": "AnyAlignment"
    }
    alignment_map_abbr_to_full = {v: k for k, v in alignment_map_full_to_abbr.items()}

    # Check if it's an abbreviation
    if alignment_text in alignment_map_abbr_to_full:
        monster_data['alignment']['abbreviation'] = alignment_text
        monster_data['alignment']['text_override'] = alignment_map_abbr_to_full[alignment_text]
    # Check if it's a full text version
    elif alignment_text.lower() in alignment_map_full_to_abbr:
        monster_data['alignment']['abbreviation'] = alignment_map_full_to_abbr[alignment_text.lower()]
        monster_data['alignment']['text_override'] = alignment_text.lower()
    else: # Complex or unmappable alignment
        monster_data['alignment']['text_override'] = alignment_text
        monster_data['alignment']['abbreviation'] = "" # Or some indicator like "Custom"


def parse_statistics(monster_element, monster_data):
    stats = monster_data['statistics']
    stats['strength']['score'] = int(get_text(monster_element, 'str', '0'))
    stats['dexterity']['score'] = int(get_text(monster_element, 'dex', '0'))
    stats['constitution']['score'] = int(get_text(monster_element, 'con', '0'))
    stats['intelligence']['score'] = int(get_text(monster_element, 'int', '0'))
    stats['wisdom']['score'] = int(get_text(monster_element, 'wis', '0'))
    stats['charisma']['score'] = int(get_text(monster_element, 'cha', '0'))

def parse_defenses(monster_element, monster_data):
    defenses = monster_data['defenses']

    ac_text = get_text(monster_element, 'ac')
    ac_match = re.match(r"(\d+)(?:\s*\((.*?)\))?", ac_text)
    if ac_match:
        defenses['armor_class']['value'] = int(ac_match.group(1))
        if ac_match.group(2):
            defenses['armor_class']['description'] = ac_match.group(2).strip()
    elif ac_text.isdigit():
         defenses['armor_class']['value'] = int(ac_text)
    else:
        defenses['armor_class']['description'] = ac_text

    hp_text = get_text(monster_element, 'hp')
    hp_match = re.match(r"(\d+)\s*\((.*?)\)", hp_text)
    if hp_match:
        defenses['hit_points']['average'] = int(hp_match.group(1))
        defenses['hit_points']['formula'] = hp_match.group(2)
    elif hp_text.isdigit():
        defenses['hit_points']['average'] = int(hp_text)
        defenses['hit_points']['formula'] = hp_text
    else:
        defenses['hit_points']['formula'] = hp_text

    save_text = get_text(monster_element, 'save')
    if save_text:
        saves = save_text.split(',')
        for s in saves:
            s_match = re.match(r"\s*(\w+)\s*([+-]\d+)\s*", s.strip())
            if s_match:
                defenses['saving_throw_proficiencies'].append({
                    "name": s_match.group(1).strip(), # Keep original case for now
                    "bonus": s_match.group(2).strip()
                })

    def parse_defense_types(xml_text, category_key):
        structured_list = []
        general_notes_parts = []
        if not xml_text: return structured_list, ""
        groups = xml_text.split(';')
        for group_text in groups:
            group_text = group_text.strip()
            if not group_text: continue
            common_note_match = re.search(r"(\bfrom\b .*|\bexcept\b .*|\bwhile\b .*|\bbut not from\b .*|\bonly\b)$", group_text, re.IGNORECASE)
            common_note = common_note_match.group(1).strip() if common_note_match else ""
            current_types_text = group_text[:common_note_match.start()].strip() if common_note_match else group_text

            types_in_group = current_types_text.split(',')
            parsed_types_in_this_group = False
            for type_candidate_text in types_in_group:
                type_candidate_text = type_candidate_text.replace("and ", "").strip()
                if not type_candidate_text: continue
                parsed_types_in_this_group = True
                specific_note_match = re.match(r"([\w\s\-\/]+)\s+\((.*?)\)$", type_candidate_text)
                final_type_name = type_candidate_text
                final_note = common_note
                if specific_note_match:
                    final_type_name = specific_note_match.group(1).strip()
                    specific_note_text = specific_note_match.group(2).strip()
                    final_note = f"{specific_note_text}; {common_note}" if common_note else specific_note_text
                if final_type_name:
                    structured_list.append({"type": final_type_name.lower(), "note": final_note}) # Standardize type to lowercase
            if not parsed_types_in_this_group and not common_note: # If the group was just a note itself
                general_notes_parts.append(group_text)
        final_general_notes = "; ".join(general_notes_parts).strip()
        return structured_list, final_general_notes

    defenses['damage_resistances']['list'], defenses['damage_resistances']['notes'] = parse_defense_types(get_text(monster_element, 'resist'), 'damage_resistances')
    defenses['damage_immunities']['list'], defenses['damage_immunities']['notes'] = parse_defense_types(get_text(monster_element, 'immune'), 'damage_immunities')
    defenses['damage_vulnerabilities']['list'], defenses['damage_vulnerabilities']['notes'] = parse_defense_types(get_text(monster_element, 'vulnerable'), 'damage_vulnerabilities')
    defenses['condition_immunities']['list'], defenses['condition_immunities']['notes'] = parse_defense_types(get_text(monster_element, 'conditionImmune'), 'condition_immunities')

    skill_tags = monster_element.findall('.//skill')
    if skill_tags:
        raw_skills_text = get_text(monster_element, 'skill')
        if raw_skills_text:
            for skill_entry in raw_skills_text.split(','):
                skill_entry = skill_entry.strip()
                match = re.match(r"(.+?)\s*([+-]\d+)", skill_entry)
                if match:
                    skill_name = match.group(1).strip()
                    bonus = match.group(2).strip()
                    monster_data["skill_proficiencies"].append({"name": skill_name, "bonus": bonus})

def parse_speed(monster_element, monster_data):
    speed_text = get_text(monster_element, 'speed')
    speeds = monster_data['speed']
    parts = speed_text.split(',')
    general_speed_notes = []
    for part in parts:
        part = part.strip()
        fly_match = re.match(r"fly\s*(\d+\s*ft\.?)(?:\s*\(hover\))?(?:\s*\((.*?)\))?", part, re.IGNORECASE)
        swim_match = re.match(r"swim\s*(\d+\s*ft\.?)(?:\s*\((.*?)\))?", part, re.IGNORECASE)
        burrow_match = re.match(r"burrow\s*(\d+\s*ft\.?)(?:\s*\((.*?)\))?", part, re.IGNORECASE)
        climb_match = re.match(r"climb\s*(\d+\s*ft\.?)(?:\s*\((.*?)\))?", part, re.IGNORECASE)
        # General walk, potentially with a note. Example "30 ft. (40 ft. in tiger form)"
        walk_match = re.match(r"(\d+\s*ft\.?)(?:\s*\((.*?)\))?", part)

        if fly_match:
            speeds['fly']['value'] = fly_match.group(1).strip()
            if "(hover)" in part.lower(): speeds['fly']['hover'] = True
            if fly_match.group(2): speeds['fly']['notes'] = fly_match.group(2).strip()
        elif swim_match:
            speeds['swim']['value'] = swim_match.group(1).strip()
            if swim_match.group(2): speeds['swim']['notes'] = swim_match.group(2).strip()
        elif burrow_match:
            speeds['burrow']['value'] = burrow_match.group(1).strip()
            if burrow_match.group(2): speeds['burrow']['notes'] = burrow_match.group(2).strip()
        elif climb_match:
            speeds['climb']['value'] = climb_match.group(1).strip()
            if climb_match.group(2): speeds['climb']['notes'] = climb_match.group(2).strip()
        elif walk_match and not any(st in part.lower() for st in ["fly", "swim", "burrow", "climb"]):
            speeds['walk']['value'] = walk_match.group(1).strip()
            if walk_match.group(2): speeds['walk']['notes'] = walk_match.group(2).strip()
        elif part: # Unparsed part, add to general notes
            general_speed_notes.append(part)
    if general_speed_notes:
        speeds['notes'] = "; ".join(general_speed_notes)


def parse_senses_languages_cr(monster_element, monster_data):
    senses_text = get_text(monster_element, 'senses')
    if senses_text:
        parts = senses_text.split(',')
        for part in parts:
            part = part.strip()
            sense_match = re.match(r"(darkvision|blindsight|tremorsense|truesight)\s*(\d+\s*ft\.?)", part, re.IGNORECASE)
            if sense_match:
                monster_data['senses']['sense_list'].append({
                    "name": sense_match.group(1).capitalize(),
                    "range": sense_match.group(2)
                })
            else:
                if monster_data['senses']['notes']: monster_data['senses']['notes'] += "; " + part
                else: monster_data['senses']['notes'] = part

    monster_data['senses']['passive_perception']['value'] = int(get_text(monster_element, 'passive', '0'))

    languages_text = get_text(monster_element, 'languages')
    if languages_text:
        lang_parts = languages_text.split(';')
        processed_languages = []
        additional_notes = []
        for part_content in lang_parts:
            part_content = part_content.strip()
            if not part_content: continue
            telepathy_full_match = re.search(r"telepathy\s+(\d+\s*(?:ft\.?|feet|mile|miles))(?:\s*\((.*?)\))?", part_content, re.IGNORECASE)
            if telepathy_full_match:
                monster_data['languages']['telepathy']['range'] = telepathy_full_match.group(1).strip()
                if telepathy_full_match.group(2): additional_notes.append(telepathy_full_match.group(2).strip())
                remaining_text_after_telepathy = part_content.replace(telepathy_full_match.group(0), "").strip(" ,")
                if not remaining_text_after_telepathy: continue
                else: part_content = remaining_text_after_telepathy
            current_segment_languages = []
            current_segment_notes = []
            sub_parts = part_content.split(',')
            for sub_part_raw in sub_parts:
                sub_part = sub_part_raw.strip()
                if not sub_part: continue
                understands_match = re.search(r"understands\s+(.+?)(?:\s+but\s+(?:can't|cannot)\s+speak(?:\s+(?:it|them))?)?(\s*\(.*\))?$", sub_part, re.IGNORECASE)
                if understands_match:
                    understood_langs_text = understands_match.group(1).strip()
                    understood_list = [l.strip() for l in re.split(r'\s+and\s+|\s*,\s*', understood_langs_text) if l.strip()]
                    monster_data['languages']['understands_but_cant_speak']['list'].extend(understood_list)
                    if understands_match.group(2): current_segment_notes.append(understands_match.group(2)[1:-1].strip())
                else:
                    embedded_telepathy_match = re.search(r"telepathy\s+(\d+\s*(?:ft\.?|feet|mile|miles))(?:\s*\((.*?)\))?", sub_part, re.IGNORECASE)
                    if embedded_telepathy_match:
                        if not monster_data['languages']['telepathy']['range']:
                            monster_data['languages']['telepathy']['range'] = embedded_telepathy_match.group(1).strip()
                        if embedded_telepathy_match.group(2): current_segment_notes.append(embedded_telepathy_match.group(2).strip())
                        lang_name_part = sub_part.replace(embedded_telepathy_match.group(0), "").strip(" ,")
                        if lang_name_part: current_segment_languages.append(lang_name_part)
                    elif sub_part.lower() != "telepathy": current_segment_languages.append(sub_part)
            processed_languages.extend(current_segment_languages)
            additional_notes.extend(current_segment_notes)
        monster_data['languages']['language_list'] = sorted(list(set(lang for lang in processed_languages if lang)))
        monster_data['languages']['understands_but_cant_speak']['list'] = sorted(list(set(lang for lang in monster_data['languages']['understands_but_cant_speak']['list'] if lang)))
        if additional_notes:
            notes_str = "; ".join(note for note in additional_notes if note)
            monster_data['languages']['notes'] = f"{monster_data['languages']['notes']}; {notes_str}".strip("; ") if monster_data['languages']['notes'] else notes_str
        if monster_data['languages']['telepathy']['range'] and monster_data['languages']['notes']:
            telepathy_range_cleaned = re.escape(monster_data['languages']['telepathy']['range'])
            note_telepathy_pattern = rf"\btelepathy\s+{telepathy_range_cleaned}(?:\s*\([^)]*\))?\b"
            temp_notes = monster_data['languages']['notes']
            temp_notes = re.sub(note_telepathy_pattern, "", temp_notes, flags=re.IGNORECASE).strip(" ;,()")
            monster_data['languages']['notes'] = temp_notes if re.search(r"[a-zA-Z0-9]", temp_notes) else ""

    cr_text = get_text(monster_element, 'cr')
    monster_data['challenge_rating']['value'] = cr_text

def parse_description_and_source(monster_element, monster_data):
    description_content = ""
    source_info = {"book": "", "page": "", "other_sources": ""}

    # Attempt 1: Try dedicated <description_text> and <source> tags first
    desc_text_elements = monster_element.findall('description_text')
    if desc_text_elements:
        current_desc_parts = []
        for desc_elem in desc_text_elements:
            part_content = "".join(desc_elem.itertext()).strip()
            if part_content:
                current_desc_parts.append(part_content)
        description_content = "\n\n".join(current_desc_parts)

    source_tag_element = monster_element.find('source')
    if source_tag_element is not None and source_tag_element.text:
        raw_source_text = source_tag_element.text.strip()
        source_info['other_sources'] = raw_source_text # Default assignment
        source_match = re.match(r"(.*?)(?:,?\s*p(?:g|age)?\.?\s*(\d+))?$", raw_source_text, re.IGNORECASE)
        if source_match:
            book_candidate = source_match.group(1).strip()
            page_candidate = source_match.group(2)
            # Simplified book mapping for brevity
            if "Monster Manual 2024" in book_candidate or book_candidate == "MM24": source_info['book'] = "Monster Manual 2024"
            elif "Player's Handbook 2024" in book_candidate or book_candidate == "PHB24": source_info['book'] = "Player's Handbook 2024"
            else: source_info['book'] = book_candidate
            if page_candidate: source_info['page'] = page_candidate

            if source_info['book'] and source_info['book'] == book_candidate and not page_candidate:
                 source_info['other_sources'] = ""
            elif source_info['book'] and source_info['book'] != book_candidate:
                 source_info['other_sources'] = book_candidate
            elif not source_info['book']:
                source_info['other_sources'] = raw_source_text


    # Attempt 2: If no <description_text> or if it was empty, or if source wasn't found in a dedicated tag,
    # try the general <description> tag.
    if not description_content.strip() or (not source_info['book'] and not source_info['page'] and not source_info['other_sources']):
        description_element = monster_element.find('description')
        if description_element is not None:
            # Extract all text content from <description>, including <p> and direct text.
            # Exclude text from known sub-elements that are NOT part of the main description
            # (e.g. if flavor_text_block was nested here, or if other parsers handle parts of it)
            # For now, we assume <description> is mostly text or <p> tags for the main description.

            # Iteratively build description, stopping if a "Source:" line is encountered.
            raw_desc_parts = []
            potential_source_line = ""

            # Get all text nodes and text from <p> children directly under <description>
            # This avoids grabbing text from deeper, unrelated structures if any were present.
            if description_element.text and description_element.text.strip():
                raw_desc_parts.append(description_element.text.strip())

            for child in description_element:
                if child.tag == 'p':
                    p_text = "".join(child.itertext()).strip()
                    if p_text:
                        raw_desc_parts.append(p_text)
                elif child.text and child.text.strip(): # Catch text in other direct children if any
                    raw_desc_parts.append(child.text.strip())
                if child.tail and child.tail.strip(): # And their tail text
                    raw_desc_parts.append(child.tail.strip())

            full_desc_from_general_tag = "\n\n".join(filter(None, raw_desc_parts)).strip()

            # Check for source line within this general <description> content
            # Only do this if a dedicated <source> tag wasn't already successfully parsed
            if not source_info['book'] and not source_info['page'] and not source_info['other_sources']:
                source_pattern = r"Source:\s*(.*?)(?:p\.\s*(\d+))?(?:,\s*(.*))?$"
                # Try to find source at the very end of the combined text
                match_source_in_desc = re.search(source_pattern, full_desc_from_general_tag, re.IGNORECASE | re.MULTILINE)

                if match_source_in_desc and full_desc_from_general_tag.strip().endswith(match_source_in_desc.group(0).strip()):
                    potential_source_line = match_source_in_desc.group(0).strip()
                    # If description_content was empty, this becomes the main description (minus source)
                    if not description_content.strip():
                        description_content = full_desc_from_general_tag[:match_source_in_desc.start()].strip()

                    # Parse the found source line
                    book_name_raw = match_source_in_desc.group(1).strip() if match_source_in_desc.group(1) else ""
                    page_number_raw = match_source_in_desc.group(2).strip() if match_source_in_desc.group(2) else ""
                    other_sources_raw = match_source_in_desc.group(3).strip() if match_source_in_desc.group(3) else ""

                    if "Monster Manual 2024" in book_name_raw or book_name_raw == "MM24": source_info['book'] = "Monster Manual 2024"
                    elif "Player's Handbook 2024" in book_name_raw or book_name_raw == "PHB24": source_info['book'] = "Player's Handbook 2024"
                    else: source_info['book'] = book_name_raw.split(',')[0].strip()
                    if page_number_raw: source_info['page'] = page_number_raw

                    if other_sources_raw: source_info['other_sources'] = other_sources_raw
                    elif ',' in book_name_raw and source_info['book'] != book_name_raw :
                        other_sources_candidate = book_name_raw[len(source_info['book']):].strip(", ")
                        if other_sources_candidate: source_info['other_sources'] = other_sources_candidate
                    elif not source_info['book'] and not page_number_raw and book_name_raw:
                         source_info['other_sources'] = book_name_raw
                elif not description_content.strip(): # No source line found at the end, use the whole text
                    description_content = full_desc_from_general_tag
            elif not description_content.strip(): # Source was already found in <source>, just take the description
                 description_content = full_desc_from_general_tag


    monster_data['description_text'] = description_content.strip()
    monster_data['source'] = source_info

    environment_tags = []
    environment_element = monster_element.find('environment')
    if environment_element is not None and environment_element.text:
        tags = [tag.strip() for tag in environment_element.text.split(',') if tag.strip()]
        environment_tags.extend(tags)
    monster_data['environment_tags']['tags'] = environment_tags

def parse_flavor_text(monster_element, monster_data):
    flavor_text_elements = monster_element.findall('flavor_text_block')
    parsed_flavor_texts = []
    for ft_elem in flavor_text_elements:
        title = ft_elem.get('title', "").strip()
        current_text_blocks = []

        # Capture direct text before any child elements if it exists
        if ft_elem.text and ft_elem.text.strip():
            current_text_blocks.append(ft_elem.text.strip())

        for child_elem in ft_elem:
            if child_elem.tag == 'p':
                p_text = "".join(child_elem.itertext()).strip()
                if p_text:
                    current_text_blocks.append(p_text)
            elif child_elem.tag == 'table':
                table_representation = []
                header_row_elem = child_elem.find('.//header')
                if header_row_elem is not None:
                    header_texts = ["".join(entry.itertext()).strip() for entry in header_row_elem.findall('.//entry')]
                    if any(h.strip() for h in header_texts): # Only add header if it has content
                        table_representation.append(" | ".join(header_texts))
                        table_representation.append("--- | " * (len(header_texts) -1) + "---" if len(header_texts)>0 else "")

                for row_elem in child_elem.findall('.//row'):
                    entry_texts = ["".join(entry.itertext()).strip() for entry in row_elem.findall('.//entry')]
                    if any(e.strip() for e in entry_texts): # Only add row if it has content
                        table_representation.append(" | ".join(entry_texts))

                if table_representation: # Only add table if it has content
                    current_text_blocks.append("\n".join(table_representation))

            # Capture tail text of the child element
            if child_elem.tail and child_elem.tail.strip():
                current_text_blocks.append(child_elem.tail.strip())

        if current_text_blocks:
            parsed_flavor_texts.append({
                "title": title,
                "text_block": current_text_blocks
            })
    if parsed_flavor_texts:
         monster_data['flavor_text'] = parsed_flavor_texts

# --- Detailed Parsing Functions for Complex Structures ---

def extract_text_with_tags_for_action_description(element):
    """
    Extracts text from an element, preserving basic formatting (like <p>, <i>, <b>)
    as simple newlines or markdown-like tags if necessary, but primarily for text content.
    This version is simplified to mostly join paragraphs.
    """
    if element is None:
        return ""

    parts = []
    if element.text:
        parts.append(element.text.strip())

    for child in element:
        if child.tag == 'p':
            p_text = "".join(t for t in child.itertext()).strip()
            if p_text:
                parts.append(p_text)
        elif child.tag == 'i' or child.tag == 'b' or child.tag == 'strong' or child.tag == 'em':
            # For simplicity, just get the text, could add markdown later
            tag_text = "".join(t for t in child.itertext()).strip()
            if child.tag == 'i' or child.tag == 'em':
                parts.append(f"*{tag_text}*")
            elif child.tag == 'b' or child.tag == 'strong':
                parts.append(f"**{tag_text}**")
            else:
                 parts.append(tag_text)

        else: # For other tags, just grab their full text content
            inner_text = "".join(t for t in child.itertext()).strip()
            if inner_text:
                parts.append(inner_text)

        if child.tail: # Text immediately after the child tag
            parts.append(child.tail.strip())

    return "\n".join(filter(None, parts)).strip()


def parse_traits(monster_element, monster_data):
    traits_list = monster_data['traits']
    for trait_elem in monster_element.findall('trait'):
        name_elem = trait_elem.find('name')
        name = name_elem.text.strip() if name_elem is not None and name_elem.text else "Unnamed Trait"

        # Skip "Proficiency Bonus" and "Treasure" traits as they are handled elsewhere or not part of this structure
        if name.lower() == "proficiency bonus" or name.lower() == "treasure":
            continue

        texts = []
        # The primary text content is expected in <text> tags directly under <trait>
        # Or sometimes as a list of <p> tags under a general <text> tag.
        text_elements = trait_elem.findall('text')
        specific_text_content = ""

        for text_elem in text_elements:
            if text_elem.text and text_elem.text.strip(): # Direct text in <text>
                texts.append(text_elem.text.strip())
            for p_elem in text_elem.findall('p'): # Paragraphs within <text>
                if p_elem.text and p_elem.text.strip():
                    texts.append(p_elem.text.strip())

        # If no <text> tags, check for direct <p> tags under <trait> or direct text in <trait> (less common)
        if not texts:
            if trait_elem.text and trait_elem.text.strip(): # direct text in trait
                 texts.append(trait_elem.text.strip())
            for p_elem in trait_elem.findall('p'): # direct paragraphs in trait
                p_text = "".join(t.strip() for t in p_elem.itertext() if t.strip())
                if p_text:
                    texts.append(p_text)

        specific_text_content = "\n".join(texts).strip()

        recharge_text = "" # Placeholder for recharge if it's ever directly in a simple trait
        recharge_match = re.search(r"\((Recharge\s*([\d\-\–]+(?:–[\d]+)?(?:-[\d]+)?|[\d\–]+))\)", name, re.IGNORECASE)
        if not recharge_match: # Check text if not in name
            recharge_match = re.search(r"\((Recharge\s*([\d\-\–]+(?:–[\d]+)?(?:-[\d]+)?|[\d\–]+))\)", specific_text_content, re.IGNORECASE)

        if recharge_match:
            recharge_value = recharge_match.group(2).strip()
            # Clean up name and text from recharge string
            name = name.replace(recharge_match.group(1), "").strip()
            specific_text_content = specific_text_content.replace(recharge_match.group(1), "").strip()
            recharge_text = recharge_value


        trait_obj = {
            "name": name,
            "text_description": specific_text_content,
            "recharge": {"value": recharge_text, "type": ""}, # Basic recharge parsing
            "limited_uses": {"count": 0, "per": ""}
        }
        # Basic limited use parsing (e.g. "3/Day")
        limited_use_match = re.search(r"\((\d+)/([a-zA-Z]+)\)", name, re.IGNORECASE)
        if not limited_use_match:
             limited_use_match = re.search(r"\((\d+)/([a-zA-Z]+)\)", specific_text_content, re.IGNORECASE)

        if limited_use_match:
            trait_obj["limited_uses"]["count"] = int(limited_use_match.group(1))
            trait_obj["limited_uses"]["per"] = limited_use_match.group(2).lower()
            name = name.replace(limited_use_match.group(0), "").strip() # Clean from name
            trait_obj["name"] = name # Update name in object
            # specific_text_content = specific_text_content.replace(limited_use_match.group(0), "").strip() # Optionally clean from text

        traits_list.append(trait_obj)

def parse_melee_ranged_attacks(action_elem, action_obj):
    """Parses <attack> sub-elements for melee/ranged/special attacks."""
    attack_details_list = []

    # The primary text for the action is usually in <text> tags directly under <action>
    # This text often contains the "Hit:" or effect description.
    action_text_parts = []
    for text_node in action_elem.findall('text'):
        if text_node.text and text_node.text.strip():
            action_text_parts.append(text_node.text.strip())
    full_action_text = "\n".join(action_text_parts)

    # Look for <attack> tags which often encode the mechanical bits
    # Format: <attack>Name|ToHitBonus|DamageDice</attack>
    # Example: <attack>Rend|+11|2d6+6</attack>
    # Example: <attack>Acid Damage||1d8</attack>  (secondary damage)

    # First, try to get the main attack details from the action's name and the first <attack> tag
    # The action_obj['name'] should already be set by parse_actions_section

    # Melee Attack Roll: +11, reach 10 ft. Hit: 13 (2d6 + 6) Slashing damage plus 4 (1d8) Acid damage.
    # Ranged Attack Roll: +7, range 80/320 ft. Hit: 8 (1d8 + 4) Piercing damage plus 21 (6d6) Poison damage.
    # Special "attacks" like breaths: Dexterity Saving Throw: DC 18... Failure: 54 (12d8) Acid damage.

    # Regex to find attack roll details
    attack_roll_pattern = r"(Melee|Ranged)\s*(?:Weapon|Spell)?\s*Attack Roll:\s*([+-]?\d+)\s*(?:to hit)?(?:,\s*reach\s*([\d\s]+ft\.?))?(?:,\s*range\s*([\d\s\/]+ft\.?))?"
    # Regex to find "Hit:" details
    hit_pattern = r"Hit:\s*([\d\s\(\)\w\+\-\–\.]+(?:damage)?(?:[\s\w\(\)]*?))(?:plus\s*([\d\s\(\)\w\+\-\–\.]+(?:damage)?(?:[\s\w\(\)]*?)))?(?:,\s*and\s*(.*?))?\."
    # Regex for save-based attacks/actions
    save_pattern = r"(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s*Saving Throw:\s*DC\s*(\d+)"
    failure_pattern = r"Failure:\s*([\d\s\(\)\w\+\-\–\.]+(?:damage)?(?:[\s\w\(\)]*?))(?:plus\s*([\d\s\(\)\w\+\-\–\.]+(?:damage)?(?:[\s\w\(\)]*?)))?(?:,\s*and\s*(.*?))?\."
    success_pattern = r"Success:\s*(Half damage only|Half damage|No damage|.*?)\."


    main_attack_parsed = False
    attack_detail = {
        "name": action_obj.get("name", "Attack"), # Use action name as default
        "type": "", # melee, ranged, special
        "to_hit": "",
        "reach": "",
        "range": "",
        "target": "", # e.g., "one target", "each creature in a 60-foot cone"
        "damage_list": [], # [{"dice_formula": "...", "damage_type": "...", "notes": "..."}]
        "on_hit_effects": [], # list of strings for other effects
        "save_details": {"ability": "", "dc": "", "success_effect": "", "failure_effect": ""}
    }

    # Check for attack roll style
    attack_roll_match = re.search(attack_roll_pattern, full_action_text, re.IGNORECASE)
    if attack_roll_match:
        main_attack_parsed = True
        attack_detail["type"] = attack_roll_match.group(1).lower()
        attack_detail["to_hit"] = attack_roll_match.group(2)
        if attack_roll_match.group(3): # reach
            attack_detail["reach"] = attack_roll_match.group(3).strip()
        if attack_roll_match.group(4): # range
            attack_detail["range"] = attack_roll_match.group(4).strip()

        hit_match = re.search(hit_pattern, full_action_text, re.IGNORECASE)
        if hit_match:
            primary_damage_text = hit_match.group(1).strip()
            secondary_damage_text = hit_match.group(2).strip() if hit_match.group(2) else ""
            other_effects_text = hit_match.group(3).strip() if hit_match.group(3) else ""

            # Parse primary damage
            # e.g., "13 (2d6 + 6) Slashing damage" or "7 (1d8 + 3) Bludgeoning damage"
            damage_match = re.match(r"(?:.*?\(?([ \d\w\+\-\–d]+)\)?\s*)?([\w\s]+(?:damage)?)", primary_damage_text)
            if damage_match:
                dmg_dice = damage_match.group(1).strip() if damage_match.group(1) else ""
                dmg_type = damage_match.group(2).replace("damage","").strip()
                attack_detail["damage_list"].append({"dice_formula": dmg_dice, "damage_type": dmg_type.lower(), "notes": ""})

            # Parse secondary damage if present
            if secondary_damage_text:
                damage_match_sec = re.match(r"(?:.*?\(?([ \d\w\+\-\–d]+)\)?\s*)?([\w\s]+(?:damage)?)", secondary_damage_text)
                if damage_match_sec:
                    dmg_dice_sec = damage_match_sec.group(1).strip() if damage_match_sec.group(1) else ""
                    dmg_type_sec = damage_match_sec.group(2).replace("damage","").strip()
                    attack_detail["damage_list"].append({"dice_formula": dmg_dice_sec, "damage_type": dmg_type_sec.lower(), "notes": "plus"})

            if other_effects_text:
                attack_detail["on_hit_effects"].append(other_effects_text)

        # Extract target from text before "Hit:"
        target_text_match = re.search(r"(?:reach|range)\s*[\d\s\w\/\.]+\.?\s*(.*?)(?:Hit:|$)", full_action_text, re.IGNORECASE | re.DOTALL)
        if target_text_match and target_text_match.group(1).strip():
             attack_detail["target"] = target_text_match.group(1).strip().rstrip(',')
        elif not attack_detail["target"]:
             attack_detail["target"] = "one target" # Default if not specified

    # Check for save-based style (often for breaths or special abilities)
    save_match = re.search(save_pattern, full_action_text, re.IGNORECASE)
    if save_match:
        main_attack_parsed = True
        attack_detail["type"] = "special" # Or determine more specifically if possible
        attack_detail["save_details"]["ability"] = save_match.group(1).lower()
        attack_detail["save_details"]["dc"] = save_match.group(2)

        failure_match = re.search(failure_pattern, full_action_text, re.IGNORECASE)
        if failure_match:
            primary_damage_text_fail = failure_match.group(1).strip()
            # secondary_damage_text_fail = failure_match.group(2).strip() if failure_match.group(2) else "" # Not common for saves
            other_effects_text_fail = failure_match.group(3).strip() if failure_match.group(3) else ""

            damage_match_fail = re.match(r"(?:.*?\(?([ \d\w\+\-\–d]+)\)?\s*)?([\w\s]+(?:damage)?)", primary_damage_text_fail)
            if damage_match_fail:
                dmg_dice_fail = damage_match_fail.group(1).strip() if damage_match_fail.group(1) else ""
                dmg_type_fail = damage_match_fail.group(2).replace("damage","").strip()
                attack_detail["damage_list"].append({"dice_formula": dmg_dice_fail, "damage_type": dmg_type_fail.lower(), "notes": "on failed save"})

            attack_detail["save_details"]["failure_effect"] = primary_damage_text_fail
            if other_effects_text_fail:
                 attack_detail["save_details"]["failure_effect"] += f", and {other_effects_text_fail}"


        success_match = re.search(success_pattern, full_action_text, re.IGNORECASE)
        if success_match:
            attack_detail["save_details"]["success_effect"] = success_match.group(1).strip()

        # Extract target/area for save-based effects
        # e.g., "each creature in a 60-foot-long, 5-foot-wide Line"
        target_save_match = re.search(r"DC\s*\d+,\s*(.*?)(?:\.\s*Failure:|$)", full_action_text, re.IGNORECASE | re.DOTALL)
        if target_save_match and target_save_match.group(1).strip():
            attack_detail["target"] = target_save_match.group(1).strip().rstrip('.')
        elif not attack_detail["target"]:
             attack_detail["target"] = "one or more targets"


    # If main attack details were parsed, add to list
    if main_attack_parsed and (attack_detail["damage_list"] or attack_detail["save_details"]["dc"]):
        attack_details_list.append(attack_detail)

    # Then, process explicit <attack> tags for additional damage components or alternative attacks
    # These are often secondary damage types or sometimes alternative ways to represent the main attack
    xml_attack_tags = action_elem.findall('attack')
    for attack_tag in xml_attack_tags:
        if attack_tag.text:
            parts = attack_tag.text.strip().split('|')
            tag_name = parts[0].strip()
            tag_to_hit = parts[1].strip() if len(parts) > 1 else ""
            tag_damage_dice = parts[2].strip() if len(parts) > 2 else ""

            # Avoid duplicating the main attack if already parsed from text and names match
            # And if the <attack> tag seems to represent the primary damage already captured
            is_primary_damage_source = any(d["dice_formula"] == tag_damage_dice for d in attack_detail["damage_list"]) if attack_detail["damage_list"] else False
            if tag_name.lower() == attack_detail["name"].lower() and tag_to_hit == attack_detail["to_hit"] and is_primary_damage_source:
                continue # Already parsed this as part of the main attack from text

            # If it's a secondary damage type (e.g., "Acid Damage||1d8")
            if not tag_to_hit and tag_damage_dice:
                # Check if this damage is already in the list from text parsing
                already_parsed = False
                for existing_damage in attack_detail.get("damage_list", []):
                    if existing_damage["dice_formula"] == tag_damage_dice and \
                       tag_name.lower().replace(" damage", "") in existing_damage["damage_type"].lower():
                        already_parsed = True
                        break
                if not already_parsed:
                    damage_type_from_name = tag_name.lower().replace(" damage", "").strip()
                    # Ensure the primary attack_detail object exists if we are adding secondary damage to it
                    if not attack_details_list and main_attack_parsed: # Add to the current main attack_detail
                         attack_detail["damage_list"].append({
                            "dice_formula": tag_damage_dice,
                            "damage_type": damage_type_from_name,
                            "notes": "plus" # Assume it's additional
                        })
                    elif attack_details_list: # Add to the last parsed attack in the list
                        attack_details_list[-1]["damage_list"].append({
                            "dice_formula": tag_damage_dice,
                            "damage_type": damage_type_from_name,
                            "notes": "plus"
                        })
                    # else: this secondary damage has no primary attack to attach to via this logic
            elif tag_to_hit and tag_damage_dice: # A distinct attack not captured by main text parsing
                new_sub_attack = {
                    "name": tag_name, "type": "", "to_hit": tag_to_hit, "reach": "", "range": "", "target": "one target",
                    "damage_list": [{"dice_formula": tag_damage_dice, "damage_type": "unknown", "notes": ""}], # Need to infer damage type
                    "on_hit_effects": [], "save_details": {"ability": "", "dc": "", "success_effect": "", "failure_effect": ""}
                }
                # Try to infer damage type from name or previous context
                if "slashing" in tag_name.lower(): new_sub_attack["damage_list"][0]["damage_type"] = "slashing"
                elif "piercing" in tag_name.lower(): new_sub_attack["damage_list"][0]["damage_type"] = "piercing"
                elif "bludgeoning" in tag_name.lower(): new_sub_attack["damage_list"][0]["damage_type"] = "bludgeoning"
                # ... more types
                attack_details_list.append(new_sub_attack)


    if attack_details_list:
        action_obj['attack_details'] = attack_details_list

    # Ensure description is populated even if no structured attack found
    if not action_obj.get('text_description'):
        action_obj['text_description'] = extract_text_with_tags_for_action_description(action_elem.find('text')) \
                                         or full_action_text \
                                         or " ".join(t.strip() for t in action_elem.itertext() if t.strip())


def parse_special_actions(action_elem, action_obj):
    """Parses actions that are not typical attacks (e.g., Multiattack, Spellcasting descriptions)."""
    # Name is already parsed by parse_actions_section
    # Text description is the main content here.
    # Try to get a more structured text if possible (e.g. from multiple <text> or <p> tags)

    text_content_parts = []
    for text_node in action_elem.findall('text'):
        if text_node.text and text_node.text.strip():
            text_content_parts.append(text_node.text.strip())
        for p_node in text_node.findall('p'):
            p_text = "".join(t.strip() for t in p_node.itertext() if t.strip())
            if p_text:
                text_content_parts.append(p_text)

    if not text_content_parts and action_elem.text and action_elem.text.strip(): # Fallback to direct text in action
        text_content_parts.append(action_elem.text.strip())

    action_obj['text_description'] = "\n".join(text_content_parts).strip()
    if not action_obj['text_description']: # Ultimate fallback
         action_obj['text_description'] = " ".join(t.strip() for t in action_elem.itertext() if t.strip()).replace(action_obj.get("name",""),"").strip()


def parse_actions_section(monster_element, monster_data, action_type_tag, target_list_key):
    """Generic parser for <action>, <bonus_action>, <reaction> sections."""
    action_list = monster_data[target_list_key]
    for action_elem in monster_element.findall(action_type_tag):
        name_elem = action_elem.find('name')
        name = name_elem.text.strip() if name_elem is not None and name_elem.text else f"Unnamed {action_type_tag.capitalize()}"

        action_obj = {
            "name": name,
            "text_description": "", # Will be filled by specific parsers
            "recharge": {"value": "", "type": ""},
            "limited_uses": {"count": 0, "per": ""}
            # attack_details will be added by parse_melee_ranged_attacks if applicable
        }

        # Parse recharge from name or text
        recharge_text_content = "".join(t.strip() for t in action_elem.find('text').itertext()) if action_elem.find('text') else ""

        recharge_val_from_tag = get_text(action_elem, 'recharge') # e.g. D5, 1/DAY

        recharge_match_name = re.search(r"\((Recharge\s*([\d\-\–]+(?:–[\d]+)?(?:-[\d]+)?|[\d\–]+))\)", name, re.IGNORECASE)
        recharge_match_text = re.search(r"\((Recharge\s*([\d\-\–]+(?:–[\d]+)?(?:-[\d]+)?|[\d\–]+))\)", recharge_text_content, re.IGNORECASE)

        final_recharge_value = ""
        if recharge_val_from_tag:
            final_recharge_value = recharge_val_from_tag
        elif recharge_match_name:
            final_recharge_value = recharge_match_name.group(2).strip()
            name = name.replace(recharge_match_name.group(1), "").strip() # Clean name
            action_obj["name"] = name
        elif recharge_match_text:
            final_recharge_value = recharge_match_text.group(2).strip()
            # Cleaning from text_description will be handled by specific parsers if they re-extract text

        if final_recharge_value:
            action_obj["recharge"]["value"] = final_recharge_value
            if "d" in final_recharge_value.lower(): # e.g. D6, D4-6
                 action_obj["recharge"]["type"] = "dice"
            elif "/" in final_recharge_value.lower(): # e.g. 1/Day
                 action_obj["recharge"]["type"] = "per_interval"
            else: # e.g. 6 (for recharge 6)
                 action_obj["recharge"]["type"] = "numerical"


        # Parse limited uses (e.g., " (2/Day)")
        limited_use_match_name = re.search(r"\((\d+)/([a-zA-Z]+)\)", name, re.IGNORECASE)
        limited_use_match_text = re.search(r"\((\d+)/([a-zA-Z]+)\)", recharge_text_content, re.IGNORECASE) # Check text too

        if recharge_val_from_tag and "/" in recharge_val_from_tag: # Treat "2/DAY" from <recharge> as limited use
            parts = recharge_val_from_tag.split('/')
            if len(parts) == 2 and parts[0].isdigit():
                action_obj["limited_uses"]["count"] = int(parts[0])
                action_obj["limited_uses"]["per"] = parts[1].lower()
                action_obj["recharge"]["value"] = "" # Clear recharge if it was actually a limited use
                action_obj["recharge"]["type"] = ""


        elif limited_use_match_name:
            action_obj["limited_uses"]["count"] = int(limited_use_match_name.group(1))
            action_obj["limited_uses"]["per"] = limited_use_match_name.group(2).lower()
            name = name.replace(limited_use_match_name.group(0), "").strip()
            action_obj["name"] = name
        elif limited_use_match_text:
            action_obj["limited_uses"]["count"] = int(limited_use_match_text.group(1))
            action_obj["limited_uses"]["per"] = limited_use_match_text.group(2).lower()
            # Cleaning from text_description will be handled by specific parsers

        # Determine if it's an attack action or a special action based on presence of <attack> tags or keywords
        if action_elem.find('attack') is not None or \
           any(kw in name.lower() for kw in ["attack", "rend", "slam", "bite", "claw", "breath", "gaze", "tentacle", "lash", "ray"]) or \
           any(kw in recharge_text_content.lower() for kw in ["attack roll:", "saving throw:", "hit:"]):
            parse_melee_ranged_attacks(action_elem, action_obj)
        # elif name.lower() == "spellcasting": # Spellcasting has its own parser
            # pass # Will be handled by parse_spellcasting if it's a spellcasting action block
        else:
            parse_special_actions(action_elem, action_obj)

        # Special handling for Multiattack to try and list what it entails
        if name.lower() == "multiattack" and 'text_description' in action_obj:
            multi_desc = action_obj['text_description']
            # "The dragon makes three Rend attacks. It can replace one attack with a use of Spellcasting to cast Melf's Acid Arrow (level 3 version)."
            # Attempt to extract the components of the multiattack
            components = []
            # Simple regex, might need refinement
            # "makes X Y attacks" or "uses X and Y"
            # This is very basic, real multiattack descriptions can be complex
            attack_mentions = re.findall(r"makes (?:one|two|three|four|five|six|\d+)\s+([\w\s]+?)\s+attacks", multi_desc, re.IGNORECASE)
            components.extend(attack_mentions)
            use_mentions = re.findall(r"uses\s+([\w\s]+?)(?:\s+and\s+([\w\s]+?))?(?:\s+if available|\.)", multi_desc, re.IGNORECASE)
            for um in use_mentions:
                components.extend(u.strip() for u in um if u.strip())

            replace_mentions = re.findall(r"replace (?:any|one|two)\s+attack(?:s)?\s+with\s+(?:a use of )?([\w\s\(\)]+?)(?:\.|$|,)", multi_desc, re.IGNORECASE)
            if replace_mentions:
                components.extend([f"(can replace with) {r.strip()}" for r in replace_mentions])

            if components:
                action_obj["multiattack_options"] = sorted(list(set(c.strip() for c in components if c.strip())))


        # Don't add "Spellcasting" action here if it's meant for the dedicated spellcasting section
        # However, some monsters might have a generic "Spellcasting" action that just describes it,
        # distinct from a full <spellcasting> block. The glossary wants spellcasting in its own section.
        # So, if this IS the spellcasting info, it will be processed by parse_spellcasting later.
        # For now, we add all found actions. Duplicates or misplacements can be refined.
        # Let's skip adding if name is "Spellcasting" and a dedicated spellcasting parser will handle it.
        is_main_spellcasting_action = (name.lower() == "spellcasting" and monster_element.find('spellcasting') is not None)

        if not is_main_spellcasting_action:
             action_list.append(action_obj)


def parse_legendary_actions(monster_element, monster_data):
    legendary_section = monster_data['legendary_actions']

    # Find the introductory legendary action block first (if any)
    # e.g. <legendary><name>Legendary Actions (3/Turn)</name><recharge>3/TURN</recharge><text>...</text></legendary>
    intro_legendary_elem = monster_element.find("legendary[name[contains(translate(text(), 'L', 'l'), 'legendary actions')]]")

    if intro_legendary_elem is not None:
        name_text = get_text(intro_legendary_elem, 'name', "")
        recharge_text = get_text(intro_legendary_elem, 'recharge', "") # e.g., "3/TURN"

        per_turn_match = re.search(r"\((\d+)/Turn\)", name_text, re.IGNORECASE)
        if not per_turn_match and recharge_text:
            per_turn_match_recharge = re.match(r"(\d+)/TURN", recharge_text, re.IGNORECASE)
            if per_turn_match_recharge:
                legendary_section['per_turn'] = int(per_turn_match_recharge.group(1))

        if per_turn_match:
            legendary_section['per_turn'] = int(per_turn_match.group(1))

        # The general description text for legendary actions can be stored if needed, but glossary doesn't specify where.
        # For now, we focus on the actions themselves.

    # Then parse individual legendary actions
    for legendary_elem in monster_element.findall('legendary'):
        name_elem = legendary_elem.find('name')
        name = name_elem.text.strip() if name_elem is not None and name_elem.text else "Unnamed Legendary Action"

        # Skip the introductory block if encountered again
        if "legendary actions" in name.lower() and legendary_elem.find('recharge') is not None : # Heuristic
            if legendary_section['per_turn'] == 0 and legendary_elem.find('recharge') is not None: # Try to get per_turn if not already set
                recharge_text_val = get_text(legendary_elem, 'recharge', "")
                per_turn_match_recharge = re.match(r"(\d+)/TURN", recharge_text_val, re.IGNORECASE)
                if per_turn_match_recharge:
                    legendary_section['per_turn'] = int(per_turn_match_recharge.group(1))
            continue

        # Skip lair action blocks here, they are handled separately
        if legendary_elem.get('category') == 'lair':
            continue

        action_obj = {
            "name": name,
            "text_description": "",
            "cost": 1, # Default cost
            # attack_details will be added by parse_melee_ranged_attacks if applicable
        }

        # Try to parse cost from name, e.g. "Wing Attack (Costs 2 Actions)"
        cost_match = re.search(r"\(Costs\s*(\d+)\s*Actions?\)", name, re.IGNORECASE)
        if cost_match:
            action_obj['cost'] = int(cost_match.group(1))
            name = name.replace(cost_match.group(0), "").strip() # Clean name
            action_obj['name'] = name

        full_text_content = "".join(t.strip() for t in legendary_elem.find('text').itertext()) if legendary_elem.find('text') else ""

        # Determine if it's an attack or special, then parse
        if legendary_elem.find('attack') is not None or \
           any(kw in name.lower() for kw in ["attack", "rend", "slam", "bite", "claw", "breath", "gaze", "tentacle", "lash", "ray", "swipe"]) or \
           any(kw in full_text_content.lower() for kw in ["attack roll:", "saving throw:", "hit:"]):
            parse_melee_ranged_attacks(legendary_elem, action_obj) # Pass the legendary_elem as if it's an action_elem
        else:
            parse_special_actions(legendary_elem, action_obj) # Pass legendary_elem

        # Ensure description is populated even if no structured attack found
        if not action_obj.get('text_description') and full_text_content:
             action_obj['text_description'] = full_text_content.replace(action_obj.get("name",""),"").strip()


        legendary_section['actions_list'].append(action_obj)


def parse_mythic_actions(monster_element, monster_data):
    mythic_section = monster_data['mythic_actions']
    # Mythic actions might be under a general <mythic> tag or individual ones.
    # Structure: <mythic name="Mythic Trait Name (Recharges after a Short or Long Rest)."> <text>If the monster...</text> </mythic>
    # Or <action category="mythic"> <name>...</name> <text>...</text> </action>
    # The glossary implies a list of actions.

    # Look for <action category="mythic">
    for mythic_action_elem in monster_element.findall("action[@category='mythic']"):
        name_elem = mythic_action_elem.find('name')
        name = name_elem.text.strip() if name_elem is not None and name_elem.text else "Unnamed Mythic Action"

        action_obj = {"name": name, "text_description": ""}
        parse_special_actions(mythic_action_elem, action_obj) # Generic parsing for text
        # Potentially parse for attacks if structure allows:
        # parse_melee_ranged_attacks(mythic_action_elem, action_obj)
        mythic_section['actions_list'].append(action_obj)

    # Also look for <mythic> tags that aren't just introductory fluff
    for mythic_elem in monster_element.findall('mythic'):
        name_attr = mythic_elem.get('name', "")
        name_tag = mythic_elem.find('name')

        name = name_tag.text.strip() if name_tag is not None and name_tag.text else name_attr
        if not name: name = "Unnamed Mythic Feature"

        # Avoid generic headers like "Mythic Actions" if they are just containers
        if "mythic actions" in name.lower() and not mythic_elem.find('text'): # Simple heuristic
            continue

        action_obj = {"name": name, "text_description": ""}
        parse_special_actions(mythic_elem, action_obj) # Generic parsing for text
        mythic_section['actions_list'].append(action_obj)


def parse_lair_actions_and_regional_effects(monster_element, monster_data):
    lair_actions_list = monster_data['lair_actions']['actions_list']
    regional_effects_list = monster_data['regional_effects']['effects_list']

    # Lair actions and regional effects are often described together in XML,
    # typically under a <legendary category="lair"> tag or similar.
    # Example: <legendary category="lair"><name>Black Dragon Lairs...</name><text>Lair actions text... Regional effects text...</text></legendary>
    # Or sometimes dedicated <lairaction> and <regionaleffect> tags.

    # First, check for dedicated tags
    for la_elem in monster_element.findall('lairaction'):
        name = get_text(la_elem, 'name', "Lair Action")
        text_parts = [t.strip() for t in la_elem.findall('text') if t.text and t.text.strip()]
        desc = "\n".join(text_parts) if text_parts else get_text(la_elem, 'text', "Lair action description.")
        lair_actions_list.append({"name": name, "text_description": desc})

    for re_elem in monster_element.findall('regionaleffect'):
        name = get_text(re_elem, 'name', "Regional Effect")
        text_parts = [t.strip() for t in re_elem.findall('text') if t.text and t.text.strip()]
        desc = "\n".join(text_parts) if text_parts else get_text(re_elem, 'text', "Regional effect description.")
        regional_effects_list.append({"name": name, "text_description": desc})

    # If not found in dedicated tags, look for combined sections like <legendary category="lair">
    if not lair_actions_list and not regional_effects_list:
        lair_section_elems = monster_element.findall("legendary[@category='lair']")
        if not lair_section_elems: # Fallback to general <lair> or <regional> tags
            lair_section_elems.extend(monster_element.findall("lair"))
            # regional_section_elems = monster_element.findall("regional") # Not standard

        for section_elem in lair_section_elems:
            full_text_content = ""
            text_elem = section_elem.find('text')
            if text_elem is not None:
                # Get all text, including from <p> tags inside <text>
                if text_elem.text and text_elem.text.strip():
                    full_text_content += text_elem.text.strip() + "\n\n"
                for p_child in text_elem.findall('p'):
                    p_text_content = "".join(t for t in p_child.itertext()).strip()
                    if p_text_content:
                        full_text_content += p_text_content + "\n\n"
            full_text_content = full_text_content.strip()

            if not full_text_content: continue # Skip if no text

            # Heuristics to split lair actions from regional effects if combined
            # This is tricky and highly dependent on common phrasing.
            # "The region containing an X's lair is warped by it, creating the following effects:"
            # "On initiative count 20 (losing initiative ties), the X takes a lair action to cause one of the following effects:"

            lair_action_intro_keyword = "takes a lair action to cause one of the following"
            regional_effect_intro_keyword = "region containing .*? lair is warped .*? creating the following effects:"

            lair_actions_text_block = ""
            regional_effects_text_block = ""

            # Try to find a split point
            lair_match = re.search(lair_action_intro_keyword, full_text_content, re.IGNORECASE)
            regional_match = re.search(regional_effect_intro_keyword, full_text_content, re.IGNORECASE)

            if lair_match and regional_match:
                if lair_match.start() < regional_match.start():
                    lair_actions_text_block = full_text_content[lair_match.end():regional_match.start()].strip()
                    regional_effects_text_block = full_text_content[regional_match.end():].strip()
                else:
                    regional_effects_text_block = full_text_content[regional_match.end():lair_match.start()].strip()
                    lair_actions_text_block = full_text_content[lair_match.end():].strip()
            elif lair_match:
                lair_actions_text_block = full_text_content[lair_match.end():].strip()
                 # Assume anything before it might be general lair description, not regional effects unless explicitly stated
            elif regional_match:
                regional_effects_text_block = full_text_content[regional_match.end():].strip()
                # Assume anything before it might be general lair description
            else:
                # No clear keywords, assume it's all one or the other, or needs manual split.
                # Default to lair actions if "lair" is in the section name, or regional if "regional"
                section_name_text = get_text(section_elem, 'name', "").lower()
                if "lair" in section_name_text and "regional" not in section_name_text:
                    lair_actions_text_block = full_text_content
                elif "regional" in section_name_text and "lair" not in section_name_text:
                    regional_effects_text_block = full_text_content
                else: # Could be both, or just general description. For now, put into lair actions as a fallback.
                    # This is a common case: "Black Dragon Lairs Black dragons lurk... Acrid Haze... Foul Water..."
                    # Here, "Acrid Haze" and "Foul Water" are regional effects.
                    # The part before is description.
                    # A simple split by "If the dragon dies" might work for some regional effects blocks.

                    # More refined split for common dragon lair text:
                    # 1. General Lair Description (Name of section)
                    # 2. Regional Effects Introduction (e.g., "The region containing an adult or ancient black dragon's lair is warped by its presence, creating the following effects:")
                    # 3. List of Regional Effects (often bulleted or distinct paragraphs)
                    # 4. Concluding statement (e.g., "If the dragon dies or moves its lair elsewhere, these effects end immediately.")
                    # Lair actions are often separate or introduced with "On initiative count 20..."

                    # Let's try to parse regional effects based on common structure for dragons:
                    # "Effect Name: Effect description."
                    # Split by lines that look like "Effect Name:"

                    potential_regional_effects = []
                    lines = full_text_content.split('\n')
                    current_effect_name = ""
                    current_effect_desc_parts = []

                    # Find the "creating the following effects:" part
                    intro_re_match = re.search(r"(creating the following effects:)", full_text_content, re.IGNORECASE)
                    if intro_re_match:
                        text_after_intro = full_text_content[intro_re_match.end():].strip()

                        # Attempt to remove the "If the dragon dies..." tail part
                        tail_re_match = re.search(r"(If the (?:dragon|hag|creature) (?:dies|is destroyed|moves its lair elsewhere), these effects end .*?\.)$", text_after_intro, re.IGNORECASE | re.DOTALL)
                        if tail_re_match:
                            text_after_intro = text_after_intro[:tail_re_match.start()].strip()

                        # Split into paragraphs, assume each is an effect or part of one
                        paragraphs = [p.strip() for p in text_after_intro.split('\n') if p.strip()]
                        for para_idx, para in enumerate(paragraphs):
                            # Check if para starts with something like "Effect Name:"
                            name_match = re.match(r"([\w\s\-\'\u2019]+?):\s*(.*)", para) # Name: Description
                            if name_match:
                                if current_effect_name and current_effect_desc_parts: # Save previous
                                    regional_effects_list.append({
                                        "name": current_effect_name,
                                        "text_description": "\n".join(current_effect_desc_parts).strip()
                                    })
                                current_effect_name = name_match.group(1).strip()
                                current_effect_desc_parts = [name_match.group(2).strip()]
                            elif current_effect_name: # Belongs to current effect
                                current_effect_desc_parts.append(para)
                            # else: # It's before the first named effect, possibly still part of intro or general desc

                        if current_effect_name and current_effect_desc_parts: # Save the last one
                            regional_effects_list.append({
                                "name": current_effect_name,
                                "text_description": "\n".join(current_effect_desc_parts).strip()
                            })

                        # If after all this, regional_effects_list is still empty, but we had text_after_intro
                        # it means the effects weren't in "Name: Desc" format.
                        # So, we might just put the whole block as one regional effect.
                        if not regional_effects_list and text_after_intro:
                             regional_effects_list.append({
                                "name": "General Regional Effects", # Or try to get from section_elem's name
                                "text_description": text_after_intro
                            })

                    # If still no regional effects, and the section_elem name suggests lair actions, put it there.
                    elif "lair action" in get_text(section_elem, 'name', "").lower():
                         lair_actions_text_block = full_text_content


            if lair_actions_text_block:
                # Lair actions are often listed with bullet points or distinct paragraphs.
                # "• Effect 1.\n• Effect 2."
                action_descs = re.split(r'\n\s*•\s*|\n\n', lair_actions_text_block) # Split by bullets or double newlines
                for i, desc_part in enumerate(action_descs):
                    desc_part = desc_part.strip("• ")
                    if desc_part:
                        # Try to find a name within the desc part, e.g. if it's "Grasping Roots. The ..."
                        name_match = re.match(r"([\w\s\-\'\u2019]+)\.\s*(.*)", desc_part)
                        action_name = f"Lair Action Option {i+1}"
                        action_text = desc_part
                        if name_match:
                            action_name = name_match.group(1).strip()
                            action_text = name_match.group(2).strip() if name_match.group(2) else action_name # if no further text

                        lair_actions_list.append({"name": action_name, "text_description": action_text})

            # This part is largely superseded by the more specific regional effect parsing above
            # if regional_effects_text_block and not regional_effects_list: # Only if list is still empty
            #     effect_descs = re.split(r'\n\s*•\s*|\n\n', regional_effects_text_block)
            #     for i, desc_part in enumerate(effect_descs):
            #         desc_part = desc_part.strip("• ")
            #         if desc_part:
            #             name_match = re.match(r"([\w\s\-\'\u2019]+)\.\s*(.*)", desc_part)
            #             effect_name = f"Regional Effect Option {i+1}"
            #             effect_text = desc_part
            #             if name_match:
            #                 effect_name = name_match.group(1).strip()
            #                 effect_text = name_match.group(2).strip() if name_match.group(2) else effect_name
            #             regional_effects_list.append({"name": effect_name, "text_description": effect_text})


def parse_spellcasting(monster_element, monster_data):
    spell_section = monster_data['spellcasting']

    # Option 1: Dedicated <spellcasting> block (more structured)
    spellcasting_elem = monster_element.find('spellcasting')
    if spellcasting_elem is not None:
        spell_section['type'] = get_text(spellcasting_elem, 'type', "innate").lower() # e.g. innate, prepared, known
        spell_section['ability'] = get_text(spellcasting_elem, 'ability', "").capitalize()
        spell_section['spell_save_dc'] = get_text(spellcasting_elem, 'dc')
        spell_section['attack_bonus'] = get_text(spellcasting_elem, 'attack')

        for at_will_elem in spellcasting_elem.findall('atwill/spell'):
            spell_section['at_will'].append({"name": get_text(at_will_elem)})

        for per_day_elem in spellcasting_elem.findall('perday'):
            count = per_day_elem.get('count', '1')
            spells_in_group = [{"name": get_text(s_elem)} for s_elem in per_day_elem.findall('spell')]
            spell_section['per_day'].append({"count": count, "spells": spells_in_group})

        for slot_elem in spellcasting_elem.findall('slot'):
            level = slot_elem.get('level', '0')
            num_slots = get_text(slot_elem)
            spell_section['spell_slots'].append({"level": level, "count": num_slots})

        for known_elem in spellcasting_elem.findall('known/spell'):
             spell_section['known_spells'].append({"name": get_text(known_elem)})
        for prepared_elem in spellcasting_elem.findall('prepared/spell'):
             spell_section['prepared_spells'].append({"name": get_text(prepared_elem)})
        return # Prioritize structured data

    # Option 2: Spellcasting described within an <action> block
    # <action><name>Spellcasting</name><text>The dragon casts... (spell save DC 17, +9 to hit...): At will: ... 1/Day each: ...</text></action>
    spellcasting_action_elem = monster_element.find("action[name='Spellcasting']")
    if spellcasting_action_elem is None: # Try case-insensitive just in case
        spellcasting_action_elem = monster_element.find("action[name[translate(text(), 'SPELLCASTING', 'spellcasting')='spellcasting']]")

    if spellcasting_action_elem is not None:
        text_elem = spellcasting_action_elem.find('text')
        if text_elem is None or not text_elem.text: return # No text to parse

        full_text = "".join(t for t in text_elem.itertext()).strip()

        # Infer type (usually innate if described this way)
        if "casts one of the following spells" in full_text:
            spell_section['type'] = "innate"
        elif "spellbook contains the following spells" in full_text or "prepares the following wizard spells" in full_text:
            spell_section['type'] = "prepared" # Or known if it's like "knows the following sorcerer spells"
        else:
            spell_section['type'] = "innate" # Default

        # Spellcasting ability
        ability_match = re.search(r"using\s+(Wisdom|Intelligence|Charisma|Con|Str|Dex)\s+as\s+the\s+spellcasting\s+ability", full_text, re.IGNORECASE)
        if ability_match:
            spell_section['ability'] = ability_match.group(1).capitalize()

        # Save DC and Attack Bonus
        dc_match = re.search(r"spell\s+save\s+DC\s*(\d+)", full_text, re.IGNORECASE)
        if dc_match:
            spell_section['spell_save_dc'] = dc_match.group(1)

        attack_bonus_match = re.search(r"([+-]\d+)\s+to\s+hit\s+with\s+spell\s+attacks", full_text, re.IGNORECASE)
        if attack_bonus_match:
            spell_section['attack_bonus'] = attack_bonus_match.group(1)

        # At will spells
        at_will_match = re.search(r"At\s+will:\s*(.*?)(?:\n|\d+/Day|•|$)", full_text, re.IGNORECASE | re.DOTALL)
        if at_will_match:
            spells_str = at_will_match.group(1).strip("• ")
            spell_names = [s.strip(" .,;") for s in spells_str.split(',') if s.strip()]
            for sn in spell_names:
                spell_detail = {"name": sn.replace(" (level 3 version)", "").strip(), "level": "", "school": "", "notes": ""} # Basic extraction
                if "(level" in sn:
                    lvl_match = re.search(r"\(level\s*(\d+)\s*version\)", sn, re.IGNORECASE)
                    if lvl_match: spell_detail["notes"] = f"cast at level {lvl_match.group(1)}"
                spell_section['at_will'].append(spell_detail)

        # Per day spells (e.g., "1/Day each: ...", "2/Day: ...")
        per_day_matches = re.findall(r"(\d+)/Day\s*(?:each)?:\s*(.*?)(?:\n|\d+/Day|•|$)", full_text, re.IGNORECASE | re.DOTALL)
        for match in per_day_matches:
            count = match[0]
            spells_str = match[1].strip("• ")
            spell_names = [s.strip(" .,;") for s in spells_str.split(',') if s.strip()]
            current_per_day_spells = []
            for sn in spell_names:
                spell_detail = {"name": sn.replace(" (level 5 version)", "").strip(), "level": "", "school": "", "notes": ""}
                if "(level" in sn:
                    lvl_match = re.search(r"\(level\s*(\d+)\s*version\)", sn, re.IGNORECASE)
                    if lvl_match: spell_detail["notes"] = f"cast at level {lvl_match.group(1)}"
                current_per_day_spells.append(spell_detail)
            if current_per_day_spells:
                 spell_section['per_day'].append({"count": count, "spells": current_per_day_spells})

        # Spell Slots (e.g. "1st level (4 slots): shield, magic missile") - This is more complex
        # This regex is a basic attempt and might need significant refinement for complex slot descriptions
        slot_matches = re.findall(r"(\d+)(?:st|nd|rd|th)\s+level\s*\((\d+)\s+slots?\):\s*(.*?)(?:\n|Cantrips|\d+(?:st|nd|rd|th)\s+level|$)", full_text, re.IGNORECASE | re.DOTALL)
        for match in slot_matches:
            level = match[0]
            num_slots = match[1]
            spells_str = match[2].strip("• ")
            spell_names = [s.strip(" .,;") for s in spells_str.split(',') if s.strip()] # These are usually known/prepared for that level

            spell_section['spell_slots'].append({"level": level, "count": num_slots})
            for sn in spell_names:
                spell_detail = {"name": sn, "level": level, "school": "", "notes": ""}
                # Decide if these go into known_spells or prepared_spells based on type or keywords
                if spell_section['type'] == "prepared" or "wizard" in full_text.lower() or "cleric" in full_text.lower() or "druid" in full_text.lower():
                    if not any(s['name'] == sn for s in spell_section['prepared_spells']):
                         spell_section['prepared_spells'].append(spell_detail)
                elif spell_section['type'] == "known" or "sorcerer" in full_text.lower() or "bard" in full_text.lower() or "warlock" in full_text.lower():
                    if not any(s['name'] == sn for s in spell_section['known_spells']):
                         spell_section['known_spells'].append(spell_detail)
                # else, if just "innate" but with slots, it's a bit ambiguous by D&D rules, but we can list them as known.
                elif spell_section['type'] == "innate":
                     if not any(s['name'] == sn for s in spell_section['known_spells']):
                         spell_section['known_spells'].append(spell_detail)


        # Fallback for general spell list if other parsing fails but <spells> tag exists
        if not spell_section['at_will'] and not spell_section['per_day'] and not spell_section['spell_slots']:
            spells_tag_text = get_text(monster_element, 'spells')
            if spells_tag_text:
                # This is usually a flat list, hard to categorize without more context
                # For now, put them all in 'known_spells' as a default if type is ambiguous
                spell_names_flat = [s.strip() for s in spells_tag_text.split(',') if s.strip()]
                for sn in spell_names_flat:
                    if not any(s['name'] == sn for s in spell_section['known_spells']): # Avoid duplicates if some were parsed
                        spell_section['known_spells'].append({"name": sn, "level": "", "school": "", "notes": ""})


def parse_equipment(monster_element, monster_data):
    equipment_list = monster_data['equipment']
    # Equipment might be in <equipment> tags, or mentioned in text (harder to parse reliably)
    # <equipment>Shortsword, Dagger (3), Pouch containing 15 gp</equipment>
    # Or <trait><name>Gear</name><text>Wand</text></trait>

    # Option 1: Direct <equipment> tag
    equipment_elem = monster_element.find('equipment')
    if equipment_elem is not None and equipment_elem.text:
        items = [item.strip() for item in equipment_elem.text.split(',') if item.strip()]
        equipment_list.extend(items)

    # Option 2: "Gear" trait (common in newer MM24 style)
    gear_trait = monster_element.find("trait[name='Gear']")
    if gear_trait is not None:
        gear_text_elem = gear_trait.find('text')
        if gear_text_elem is not None and gear_text_elem.text:
            items = [item.strip() for item in gear_text_elem.text.split(',') if item.strip()]
            for item in items: # Avoid duplicates if both methods used
                if item not in equipment_list:
                    equipment_list.append(item)


def parse_xml_file(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML file {filepath}: {e}")
        return []
    except FileNotFoundError:
        print(f"Error: File not found {filepath}")
        return []

    parsed_monsters = []
    for monster_element in root.findall('monster'):
        monster_data = initialize_monster_data(monster_element, filepath)

        parse_core_details(monster_element, monster_data)
        parse_statistics(monster_element, monster_data)
        parse_defenses(monster_element, monster_data) # Also handles skill proficiencies
        parse_speed(monster_element, monster_data)
        parse_senses_languages_cr(monster_element, monster_data)

        # Description and Source are parsed together
        parse_description_and_source(monster_element, monster_data)
        # Flavor text is parsed separately
        parse_flavor_text(monster_element, monster_data)

        # Proficiency Bonus (example, might need refinement based on actual XML structure for this)
        for trait_element in monster_element.findall('trait'): # Assuming PB might be in a trait
            name_tag = trait_element.find('name')
            text_tag = trait_element.find('text')
            if name_tag is not None and name_tag.text and "Proficiency Bonus" in name_tag.text:
                if text_tag is not None and text_tag.text:
                    # Extract numeric part if "equals your Proficiency Bonus" or similar
                    pb_match = re.search(r"([+-]?\d+)", text_tag.text.strip())
                    if "equals your proficiency bonus" in text_tag.text.strip().lower():
                         monster_data['proficiency_bonus']['value'] = "equals your Proficiency Bonus"
                    elif pb_match:
                         monster_data['proficiency_bonus']['value'] = pb_match.group(1)
                    else:
                         monster_data['proficiency_bonus']['value'] = text_tag.text.strip()
                    break
        if not monster_data['proficiency_bonus']['value'] and monster_data['challenge_rating']['value']:
            # Fallback: Derive PB from CR if not explicitly found
            # This is a simplified mapping. Official tables are more granular.
            try:
                cr_val_str = monster_data['challenge_rating']['value']
                cr_val = 0
                if '/' in cr_val_str: # Fractional CR
                    num, den = map(int, cr_val_str.split('/'))
                    cr_val = num / den
                else:
                    cr_val = int(cr_val_str)

                if cr_val < 1: pb_val = "+2"
                elif cr_val < 5: pb_val = "+2"
                elif cr_val < 9: pb_val = "+3"
                elif cr_val < 13: pb_val = "+4"
                elif cr_val < 17: pb_val = "+5"
                elif cr_val < 21: pb_val = "+6"
                elif cr_val < 25: pb_val = "+7"
                elif cr_val < 29: pb_val = "+8"
                else: pb_val = "+9"
                monster_data['proficiency_bonus']['value'] = pb_val
            except ValueError:
                pass # Could not parse CR to int/float


        # TODO: Implement detailed parsing for:
        # parse_traits(monster_element, monster_data)
        # parse_actions(monster_element, monster_data) # Needs to be updated for new structure
        # Bonus Actions, Reactions, Legendary Actions, Mythic Actions, Lair Actions, Spellcasting, Equipment

        parsed_monsters.append(monster_data)
    return parsed_monsters

# --- Formula and Text Parsing Functions (Keep as is for now, or integrate if necessary) ---
# standardize_formula, parse_ac_formula, parse_hp_formula,
# parse_attack_bonus_formula_from_text, parse_damage_formula_from_text,
# parse_multiattack_formula, get_attack_type_from_text,
# parse_aura_details, parse_regeneration_details
# These might be used by the detailed trait/action parsers later.

# --- Placeholder for more detailed parsing functions (to be implemented in Step 7) ---
def parse_actions(monster_element, monster_data):
    # Basic placeholder, will be expanded significantly
    actions = []
    for action_elem in monster_element.findall('action'):
        name = get_text(action_elem, 'name')
        texts = [get_text(text_elem) for text_elem in action_elem.findall('text')]
        full_text = "\n".join(filter(None, texts))
        if name or full_text:
            actions.append({"name": name, "text_description": full_text.strip()}) # Add more fields later
    return actions

# ... (other placeholder functions for traits, spellcasting etc. can be added here) ...

import glob

def main():
    xml_files = [
        "01_Core/01_Players_Handbook_2024/bestiary-phb24.xml",
    ]
    mm24_path_pattern = "01_Core/03_Monster_Manual_2024/bestiary_mm24_*.xml"
    mm24_files = glob.glob(mm24_path_pattern)
    if mm24_files:
        xml_files.extend(sorted(mm24_files))
        print(f"Found MM24 bestiary files: {mm24_files}")
    else:
        print(f"Warning: No MM24 bestiary files found matching pattern {mm24_path_pattern}.")

    all_monsters_data = []
    for xml_file in xml_files:
        print(f"Parsing {xml_file}...")
        monsters_in_file = parse_xml_file(xml_file)
        if monsters_in_file:
            all_monsters_data.extend(monsters_in_file)
            print(f"Successfully parsed {len(monsters_in_file)} monsters from {xml_file}.")
        else:
            print(f"No monsters found or error in parsing {xml_file}.")

    output_filename = "bestiario_estructurado.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_monsters_data, f, indent=4, ensure_ascii=False)

    print(f"Processing complete. Parsed {len(all_monsters_data)} monsters into {output_filename}.")

if __name__ == "__main__":
    main()
# End of parse_bestiary.py
