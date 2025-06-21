import xml.etree.ElementTree as ET
import json
import re

# Structure defined in Step 1 (for reference within the script)
monster_template_for_reference = {
    "name": "",
    "source_file": "",
    "stats_formulas": {
        "armor_class": "",
        "hit_points": "",
    },
    "attacks": {
        "attack_bonus_formula": "",
        "base_damage_formula": "",
    },
    "actions": [],
    "special_abilities": [],
    "raw_xml_traits": []
}

def get_monster_name(monster_element):
    name_tag = monster_element.find('name')
    return name_tag.text if name_tag is not None and name_tag.text else "Unnamed Monster"

def initialize_monster_data(monster_element, filename):
    """Initializes a new monster data dictionary from the template."""
    return {
        "name": get_monster_name(monster_element),
        "source_file": filename,
        "stats_formulas": {
            "armor_class": monster_element.find('ac').text if monster_element.find('ac') is not None else "",
            "hit_points": monster_element.find('hp').text if monster_element.find('hp') is not None else "",
        },
        "attacks": { # General attack/damage formulas, to be filled if applicable
            "attack_bonus_formula": "",
            "base_damage_formula": "",
        },
        "actions": [],
        "special_abilities": [],
        "raw_xml_traits": [] # For traits that aren't easily parsed into specific categories
    }

def parse_xml_file(filepath):
    """Parses a single XML bestiary file and returns a list of monster data."""
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
        # Further parsing for actions, traits, etc. will be added in subsequent steps.
        # For now, this function just initializes the basic structure.
        # Populate actions, special_abilities etc. in the next step
        monster_data["actions"] = parse_actions(monster_element, monster_data)
        monster_data["special_abilities"] = parse_special_abilities(monster_element, monster_data)

        # Extract raw traits that might contain formulas or specific abilities not yet parsed
        for trait_element in monster_element.findall('trait'):
            name_tag = trait_element.find('name')
            text_tag = trait_element.find('text')
            if name_tag is not None and name_tag.text and text_tag is not None and text_tag.text:
                monster_data["raw_xml_traits"].append({
                    "name": name_tag.text.strip(),
                    "text": text_tag.text.strip()
                })

        # Specific parsing for summon stats based on formulas in traits
        parse_summon_stat_formulas(monster_element, monster_data)

        parsed_monsters.append(monster_data)

    return parsed_monsters

# --- Formula and Text Parsing Functions ---

def standardize_formula(text):
    """Standardizes common formula terms."""
    if not text:
        return ""
    text = text.lower()
    text = text.replace("spell's level", "spell_level")
    text = text.replace("spell level", "spell_level")
    text = text.replace("your spell attack modifier", "spell_attack_modifier")
    text = text.replace("your spell save dc", "spell_save_dc")
    text = text.replace("half this spell's level (round down)", "floor(spell_level / 2)")
    text = text.replace("half this spell's level", "spell_level / 2") # Assuming rounding handled by consumer
    return text.strip()

def parse_ac_formula(text_content):
    # Example: "11 + the spell's level"
    match = re.search(r"(\d+)\s*\+\s*(?:the\s*)?spell(?:'s)?\s*level", text_content, re.IGNORECASE)
    if match:
        base_ac = match.group(1)
        return f"{base_ac} + spell_level"
    # Example: "11 + your proficiency bonus" (Proficiency bonus might be related to spell level for summons)
    if "your proficiency bonus" in text_content.lower():
         # This is a common pattern for summoned creatures where PB scales with caster level / spell level
        return standardize_formula(text_content)
    return standardize_formula(text_content) # Fallback for other direct formulas or text

def parse_hp_formula(text_content):
    # Example: "40 + 10 for each spell level above 4"
    match = re.search(r"(\d+)\s*\+\s*(\d+)\s*for each spell\s*level above\s*(\d+)", text_content, re.IGNORECASE)
    if match:
        base_hp, per_level_hp, above_level = match.groups()
        return f"{base_hp} + {per_level_hp} * max(0, spell_level - {above_level})"
    # Example: "5 plus five times your Ranger level" -> for Beast Master companion, not directly spell_level
    # For now, we'll just standardize and pass it through if it's not the primary pattern
    return standardize_formula(text_content)


def parse_attack_bonus_formula_from_text(text_content):
    if "your spell attack modifier" in text_content.lower():
        return "spell_attack_modifier"
    # Try to extract a simple bonus like "+X"
    match = re.search(r"([+-]\d+)", text_content)
    if match:
        return match.group(1)
    return standardize_formula(text_content)


def parse_damage_formula_from_text(text_content, base_attack_xml_dmg=""):
    # Example: "1d8 + 3 + the spell's level Psychic damage"
    # Regex to find dice roll, a static bonus, and spell level scaling
    # Basic dice pattern: (\d+d\d+(\s*[+-]\s*\d+)?)
    # Spell level pattern: (\s*[+-]\s*the spell's level)

    formula_parts = []

    # Check for base damage from XML <attack> tag if provided
    if base_attack_xml_dmg and base_attack_xml_dmg != "0": # "0" can be placeholder
        formula_parts.append(base_attack_xml_dmg)

    # Check for spell level scaling
    if "the spell's level" in text_content.lower() or "spell level" in text_content.lower():
        # If base_attack_xml_dmg already contains a static mod, we just append spell_level
        # Otherwise, we might need to find a static mod in the text if not in base_attack_xml_dmg

        # Look for explicit static number if not in base_attack_xml_dmg or if base_attack_xml_dmg is simple dice
        # e.g. "1d8 + 3 + the spell's level" vs "1d8 + the spell's level"
        # This is tricky because the <attack> tag often has the static mod like "1d8+3"
        # Let's assume for now that if "spell's level" is present, the XML part is sufficient for dice and static mod
        # and we just add "+ spell_level"

        # A simple approach: if "spell_level" is in the text, add it to the formula.
        # This might result in "1d8+3 + spell_level" if base_attack_xml_dmg was "1d8+3"
        # Or "1d8 + spell_level" if base_attack_xml_dmg was "1d8"
        # This needs refinement based on how consistently "+ X" is present before "+ spell_level"

        # More robust: Extract the static number if it's directly before "+ the spell's level"
        # and not already captured by base_attack_xml_dmg
        static_mod_match = re.search(r"([+-]\s*\d+)\s*\+\s*(?:the\s*)?spell(?:'s)?\s*level", text_content, re.IGNORECASE)
        if static_mod_match:
            # Check if this static mod is different from what base_attack_xml_dmg implies
            if not base_attack_xml_dmg or not static_mod_match.group(1).replace(" ","") in base_attack_xml_dmg.replace(" ",""):
                 # Add this specific static mod only if it's not already part of base_attack_xml_dmg
                 # This is still complex. For now, let's assume the text gives the full formula structure.
                 pass # Simplified below

        # Simplified: if "spell_level" is in text, assume it adds to whatever base is there.
        # The main structure of dice and static mods should come from the <attack> tag.
        # The text primarily tells *that* spell_level is added.
        if not any("spell_level" in part for part in formula_parts): # Avoid duplicating if already inferred
            # Attempt to extract the core dice + static mod from text if not from XML
            core_damage_match = re.search(r"(\d+d\d+(\s*[+-]\s*\d+)?)", text_content)
            if core_damage_match and not base_attack_xml_dmg:
                formula_parts.append(core_damage_match.group(1).replace(" ", ""))

            if formula_parts and formula_parts[-1] not in ["+", "-"]:
                 formula_parts.append("+")
            formula_parts.append("spell_level")

    # If no spell_level scaling, and no base_attack_xml_dmg, try to get from text
    if not formula_parts:
        damage_match = re.search(r"(\d+d\d+(\s*[+-]\s*\d+)?)", text_content)
        if damage_match:
            formula_parts.append(damage_match.group(1).replace(" ", ""))

    final_formula = " ".join(formula_parts)

    # Attempt to capture any remaining static numbers if the formula is still simple (like just "spell_level")
    if final_formula == "spell_level" or not re.search(r"\d", final_formula):
        numeric_mod_match = re.search(r"([+-]\s*\d+)", text_content)
        if numeric_mod_match and numeric_mod_match.group(1).replace(" ","") not in final_formula:
            if final_formula and final_formula[-1] not in ["+", "-"]:
                final_formula += " +"
            final_formula += f" {numeric_mod_match.group(1).replace(' ','')}"


    # Fallback if no formula parts were derived but text exists
    if not final_formula and text_content:
        return standardize_formula(text_content) # As a last resort, return standardized text

    return standardize_formula(final_formula)


def parse_multiattack_formula(text_content):
    # Example: "The spirit makes a number of attacks equal to half this spell's level (round down)."
    match = re.search(r"equal to half this spell's level(?: \(round down\))?", text_content, re.IGNORECASE)
    if match:
        return "floor(spell_level / 2)"
    match = re.search(r"equal to half this spell's level", text_content, re.IGNORECASE)
    if match:
        return "spell_level / 2" # Consumer should handle rounding if necessary or specified elsewhere

    # Example "two attacks" or "three attacks"
    num_match = re.search(r"(one|two|three|four|five|six)\s+attacks", text_content, re.IGNORECASE)
    if num_match:
        num_str = num_match.group(1).lower()
        num_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6"}
        return num_map.get(num_str, standardize_formula(text_content))

    return standardize_formula(text_content) # Fallback


def get_attack_type_from_text(text_content):
    text_lower = text_content.lower()
    if "melee weapon attack" in text_lower: return "Melee Weapon Attack"
    if "ranged weapon attack" in text_lower: return "Ranged Weapon Attack"
    if "melee spell attack" in text_lower: return "Melee Spell Attack"
    if "ranged spell attack" in text_lower: return "Ranged Spell Attack"
    if "melee attack" in text_lower: return "Melee Attack" # Generic melee
    if "ranged attack" in text_lower: return "Ranged Attack" # Generic ranged
    return "Special"


def parse_aura_details(text_content):
    radius_formula = ""
    aura_effect = standardize_formula(text_content) # Default to full text

    # Radius: "X-foot Emanation/Radius"
    radius_match = re.search(r"(\d+)-foot\s+(?:Emanation|Radius)", text_content, re.IGNORECASE)
    if radius_match:
        radius_formula = f"{radius_match.group(1)} feet"

    # Attempt to get a simple effect description (this is very basic)
    # Example: "takes 2d6 Psychic damage"
    damage_match = re.search(r"takes\s+(.*?)\sdamage", text_content, re.IGNORECASE)
    if damage_match:
        aura_effect = f"takes {damage_match.group(1)} damage"
    else:
        # Example: "DC X TYPE save or CONDITION"
        save_match = re.search(r"(DC\s*\d+\s*\w+\s*saving throw).*?(Failure|Success):\s*(.*?)(?=(?:Failure|Success|\.|$))", text_content, re.IGNORECASE | re.DOTALL)
        if save_match:
            aura_effect = standardize_formula(save_match.group(0).strip())


    return radius_formula, aura_effect


def parse_regeneration_details(text_content):
    amount_formula = ""
    condition = ""

    # Amount: "regains X Hit Points"
    amount_match = re.search(r"regains\s+(\d+)\s+Hit Points", text_content, re.IGNORECASE)
    if amount_match:
        amount_formula = amount_match.group(1)

    # Condition: "if it has at least X HP" or similar
    condition_match = re.search(r"if\s+(.*)", text_content, re.IGNORECASE)
    if condition_match:
        condition = standardize_formula(condition_match.group(1).strip().rstrip('.'))

    if not amount_formula and not condition: # Fallback if specific parsing fails
        return standardize_formula(text_content), ""

    return amount_formula, condition

# --- End Formula and Text Parsing Functions ---

def parse_actions(monster_element, monster_data):
    actions = []
    for action_element in monster_element.findall('action'):
        action_name_tag = action_element.find('name')
        action_text_tag = action_element.find('text')
        if not action_name_tag or action_name_tag.text is None or not action_text_tag or action_text_tag.text is None:
            continue

        action_name = action_name_tag.text.strip()
        action_text = action_text_tag.text.strip()

        action_entry = {
            "name": action_name,
            "text_description": action_text,
            "type": get_attack_type_from_text(action_text),
            "multiattack_formula": "",
            "attack_bonus": "",
            "reach": "",
            "range": "",
            "hit_damage": "",
            "additional_effects_on_hit": ""
        }

        if "Multiattack" in action_name:
            action_entry["multiattack_formula"] = parse_multiattack_formula(action_text)

        # Attack details from <attack> sub-tag
        attack_sub_element = action_element.find('attack')
        base_xml_bonus = ""
        base_xml_damage = ""
        if attack_sub_element is not None and attack_sub_element.text:
            parts = attack_sub_element.text.split('|')
            if len(parts) > 1 and parts[1]: base_xml_bonus = parts[1]
            if len(parts) > 2 and parts[2]: base_xml_damage = parts[2]

        # Attack Bonus
        bonus_text_extract = re.search(r"([Pp]lus|-)\s*(\d+)\s*(?:to hit|Attack Roll)", action_text) # for "+X to hit"
        if "your spell attack modifier" in action_text.lower():
            action_entry["attack_bonus"] = "spell_attack_modifier"
        elif base_xml_bonus and base_xml_bonus != "0": # "0" can be a placeholder in some XMLs
             action_entry["attack_bonus"] = base_xml_bonus
        elif bonus_text_extract:
            action_entry["attack_bonus"] = f"+{bonus_text_extract.group(2)}" # Standardize to always have sign

        # Reach/Range
        reach_match = re.search(r"reach\s+(\d+\s*ft\.?)", action_text, re.IGNORECASE)
        if reach_match: action_entry["reach"] = reach_match.group(1)

        range_match = re.search(r"range\s+(\d+/\d+\s*ft\.?|\d+\s*ft\.?)", action_text, re.IGNORECASE)
        if range_match: action_entry["range"] = range_match.group(1)

        # Damage
        action_entry["hit_damage"] = parse_damage_formula_from_text(action_text, base_xml_damage)

        # Attempt to capture additional effects on hit more broadly
        hit_effect_match = re.search(r"[Hh]it:\s*.*?damage(?:\s*plus\s*(.*?))?(?:\.\s*If|\.\s*and|\.$|$)", action_text, re.DOTALL)
        if hit_effect_match and hit_effect_match.group(1):
            action_entry["additional_effects_on_hit"] = standardize_formula(hit_effect_match.group(1).strip().rstrip('.').strip())
        elif "Hit:" in action_text and "damage." in action_text: # Basic case if no "plus"
             pass # Already handled by hit_damage

        actions.append(action_entry)
    return actions

def parse_special_abilities(monster_element, monster_data):
    special_abilities = []
    for trait_element in monster_element.findall('trait'):
        name_tag = trait_element.find('name')
        text_tag = trait_element.find('text')
        if not name_tag or name_tag.text is None or not text_tag or text_tag.text is None:
            continue

        name = name_tag.text.strip()
        text = text_tag.text.strip()
        ability_entry = {"name": name, "text_description": text, "type": "Other"}

        if "aura" in name.lower():
            ability_entry["type"] = "Aura"
            ability_entry["aura_radius"], ability_entry["aura_effect"] = parse_aura_details(text)
        elif "regeneration" in name.lower():
            ability_entry["type"] = "Regeneration"
            ability_entry["regeneration_amount"], ability_entry["regeneration_condition"] = parse_regeneration_details(text)

        special_abilities.append(ability_entry)
    return special_abilities

def parse_summon_stat_formulas(monster_element, monster_data):
    """Parses AC, HP, and summon-specific attack/damage formulas from traits and actions."""
    for trait_element in monster_element.findall('trait'):
        name_tag = trait_element.find('name')
        text_tag = trait_element.find('text')
        if name_tag is not None and name_tag.text and text_tag is not None and text_tag.text:
            trait_name = name_tag.text.strip().lower()
            trait_text = text_tag.text.strip()
            if trait_name == 'armor class':
                monster_data["stats_formulas"]["armor_class"] = parse_ac_formula(trait_text)
            elif trait_name == 'hit points':
                monster_data["stats_formulas"]["hit_points"] = parse_hp_formula(trait_text)
            elif trait_name == 'proficiency bonus' and "equals your proficiency bonus" in trait_text.lower():
                 # This implies PB scales with caster, often tied to spell_level for summons
                 # We can note this, or assume consumer of JSON knows this context for summons
                 pass


    # For summon-specific general attack/damage scaling (often described in action text)
    # This is heuristic; some summons have varied attacks
    for action_element in monster_element.findall('action'):
        action_text_tag = action_element.find('text')
        if action_text_tag is not None and action_text_tag.text:
            action_text = action_text_tag.text.strip().lower()
            if "bonus equals your spell attack modifier" in action_text:
                 monster_data["attacks"]["attack_bonus_formula"] = "spell_attack_modifier"

            # This is a bit broad; specific damage formulas are better handled per-action
            # if "spell's level" in action_text and "damage" in action_text:
            #     if not monster_data["attacks"]["base_damage_formula"]: # Don't overwrite if already found a more specific one
            #         # This is a placeholder, specific damage parsing per action is more reliable
            #         monster_data["attacks"]["base_damage_formula"] = "see_action_text"
            pass # Per-action damage parsing is more reliable

def main():
    xml_files = [
        "01_Core/01_Players_Handbook_2024/bestiary-phb24.xml",
        "01_Core/03_Monster_Manual_2024/bestiary_mm24.xml",
        # "01_Core/02_Dungeon_Masters_Guide_2024/bestiary-dmg24.xml" # Optional
    ]

    all_monsters_data = []
    for xml_file in xml_files:
        print(f"Parsing {xml_file}...")
        monsters_in_file = parse_xml_file(xml_file)
        if monsters_in_file:
            all_monsters_data.extend(monsters_in_file)
            print(f"Successfully parsed {len(monsters_in_file)} monsters from {xml_file}.")
        else:
            print(f"No monsters found or error in parsing {xml_file}.")

    # Output to JSON
    output_filename = "bestiario_estructurado.json" # Final output filename
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_monsters_data, f, indent=4, ensure_ascii=False)

    print(f"Processing complete. Parsed {len(all_monsters_data)} monsters into {output_filename}.")

if __name__ == "__main__":
    main()
# End of parse_bestiary.py
