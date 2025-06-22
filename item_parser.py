import xml.etree.ElementTree as ET
import re

# Helper to create a sub_element if text is not None and not empty
def sub_element_if_text(parent, tag, text=None, attributes=None):
    if text is not None and text.strip():
        if tag == "item_ref" and attributes is None:
            attributes = {"name": text.strip()}
            element = ET.SubElement(parent, tag, attributes)
            return element

        element = ET.SubElement(parent, tag, attributes if attributes else {})
        element.text = text.strip()
        return element
    elif attributes:
        return ET.SubElement(parent, tag, attributes)
    return None

# Mappings
DAMAGE_TYPE_MAP = {"A": "Acid", "B": "Bludgeoning", "C": "Cold", "F": "Fire", "FO": "Force", "L": "Lightning", "N": "Necrotic", "P": "Piercing", "PO": "Poison", "PY": "Psychic", "R": "Radiant", "S": "Slashing", "T": "Thunder"}
WEAPON_PROPERTY_MAP = {"A": "Ammunition", "F": "Finesse", "H": "Heavy", "L": "Light", "LD": "Loading", "R": "Reach", "T": "Thrown", "2H": "TwoHanded", "V": "Versatile", "S": "Special"}
ITEM_TYPE_MAP = {"LA": {"main": "Armor", "sub": "Light"}, "MA": {"main": "Armor", "sub": "Medium"}, "HA": {"main": "Armor", "sub": "Heavy"}, "S": {"main": "Shield", "sub": "Shield"}, "M": {"main": "Weapon", "sub": "Melee"}, "R": {"main": "Weapon", "sub": "Ranged"}, "A": {"main": "Gear", "sub": "Ammunition"}, "G": {"main": "Gear", "sub": None}, "P": {"main": "Potion", "sub": None}, "SC": {"main": "Scroll", "sub": None}, "$": {"main": "Currency", "sub": None}, "RD": {"main": "Rod"}, "ST": {"main": "Staff"}, "WD": {"main": "Wand"}, "RG": {"main": "Ring"}, "W": {"main": "WondrousItem"}}
TOOL_CATEGORY_MAP = {"artisan tools": "ArtisansTools", "tools": "Other", "gaming set": "GamingSet", "musical instrument": "MusicalInstrument"}
ARMOR_AC_RULES = {"Light": {"add_dex": True, "max_dex_bonus": "none"}, "Medium": {"add_dex": True, "max_dex_bonus": "2"}, "Heavy": {"add_dex": False, "max_dex_bonus": "0"}, "Shield": {"add_dex": False}}

SOURCE_PATTERN = re.compile(r"Source:\s*(.*?)\s*p\.\s*(\d+)", re.IGNORECASE)
PROFICIENCY_PATTERN = re.compile(r"Proficiency:\s*([\w\s,-]+)", re.IGNORECASE)
MASTERY_PATTERN = re.compile(r"([\w\s-]+?)\s*\(Mastery\):\s*(.*?)(?=\n\n|\nSource:|\nProficiency:|Ammo:|$)", re.DOTALL | re.IGNORECASE)
AMMO_TEXT_PATTERN = re.compile(r"Ammo:\s*([\w\s\[\]\d-]+)\s*(\n|$)", re.IGNORECASE)

# Regex for cleaning property descriptions
PROPERTY_TEXT_PATTERNS = {
    "Finesse": re.compile(r"Finesse:\s*When making an attack.*?modifier for both rolls\.\s*\n?", re.IGNORECASE | re.DOTALL),
    "Light": re.compile(r"Light:\s*When you take the Attack action.*?unless that modifier is negative\.\s*\n?", re.IGNORECASE | re.DOTALL),
    "Thrown": re.compile(r"Thrown:\s*If a weapon has the Thrown property.*?with that weapon\.\s*\n?", re.IGNORECASE | re.DOTALL),
    "Versatile": re.compile(r"Versatile:\s*A Versatile weapon can be used.*?make a melee attack\.\s*\n?", re.IGNORECASE | re.DOTALL),
    "TwoHanded": re.compile(r"Two-Handed:\s*A Two-Handed weapon requires two hands when you attack with it\.\s*\n?", re.IGNORECASE | re.DOTALL),
    "Ammunition": re.compile(r"Ammunition:\s*You can use a weapon that has the Ammunition property.*?the rest is lost\.\s*\n?", re.IGNORECASE | re.DOTALL),
    "Loading": re.compile(r"Loading:\s*You can fire only one piece of ammunition.*?can normally make\.\s*\n?", re.IGNORECASE | re.DOTALL),
    "Heavy": re.compile(r"Heavy:\s*You have Disadvantage on attack rolls.*?isn't at least \d+\.\s*\n?", re.IGNORECASE | re.DOTALL),
    "Reach": re.compile(r"Reach:\s*A Reach weapon adds 5 feet.*?with it\.\s*\n?", re.IGNORECASE | re.DOTALL)
}

def parse_source(text_content, new_item_element): # Unchanged
    if not text_content: return ""
    match = SOURCE_PATTERN.search(text_content)
    if match:
        book, page = match.group(1).strip(), match.group(2).strip()
        ET.SubElement(new_item_element, "source", attrib={"book": book, "page": page})
        return text_content.replace(match.group(0), "").strip()
    return text_content

def parse_item_name(source_item, new_item_element): # Unchanged
    name_tag = source_item.find("name")
    if name_tag is not None and name_tag.text:
        sub_element_if_text(new_item_element, "name", text=name_tag.text)
        return name_tag.text
    return ""

def parse_item_type_and_rarity(source_item, new_item_element, item_name_text): # Unchanged
    item_type_main_val = "Gear"
    item_type_sub_val = None
    type_tag = source_item.find("type")
    original_type_abbr_val = type_tag.text.strip() if type_tag is not None and type_tag.text else "G"

    if original_type_abbr_val in ITEM_TYPE_MAP:
        item_type_main_val = ITEM_TYPE_MAP[original_type_abbr_val]["main"]
        item_type_sub_val = ITEM_TYPE_MAP[original_type_abbr_val].get("sub")

    detail_text = source_item.findtext("detail","").strip().lower()
    if detail_text:
        focus_map = {"arcane focus": "ArcaneFocus", "druidic focus": "DruidicFocus", "holy symbol": "HolySymbol"}
        specific_focus_map = {
            ("crystal", "arcane focus"): "Crystal", ("orb", "arcane focus"): "Orb", ("rod", "arcane focus"): "Rod",
            ("staff", "arcane focus"): "Staff", ("wand", "arcane focus"): "Wand",
            ("amulet", "holy symbol"): "Amulet", ("emblem", "holy symbol"): "Emblem", ("reliquary", "holy symbol"): "Reliquary",
            ("sprig of mistletoe", "druidic focus"): "SprigOfMistletoe", ("yew wand", "druidic focus"): "YewWand", ("wooden staff", "druidic focus"): "WoodenStaff"
        }
        name_lower = item_name_text.lower()
        is_focus_detail = False
        for k_detail, v_focus_general in focus_map.items():
            if k_detail in detail_text:
                current_sub = v_focus_general; is_focus_detail = True
                for (name_part, focus_detail_key), specific_sub in specific_focus_map.items():
                    if name_part in name_lower and focus_detail_key == k_detail:
                        if specific_sub in ["Staff", "Wand"] and item_type_main_val != "Weapon":
                            item_type_main_val = specific_sub
                            current_sub = None if specific_sub != "WoodenStaff" else "Wooden"
                        else: current_sub = specific_sub
                        break
                item_type_sub_val = current_sub; break

        if not is_focus_detail:
            if detail_text in TOOL_CATEGORY_MAP: item_type_main_val, item_type_sub_val = "Tool", TOOL_CATEGORY_MAP[detail_text]
            elif detail_text in ["common", "uncommon", "rare", "very rare", "legendary", "artifact", "varies"]:
                ET.SubElement(new_item_element, "rarity", type=detail_text.replace(" ", "").capitalize())
                if item_type_main_val in ["Potion", "Scroll", "Gear"] and new_item_element.find("attunement") is None:
                    ET.SubElement(new_item_element, "attunement", required="false")

    if item_type_main_val == "Currency":
        name_l = item_name_text.lower()
        for code in ["CP", "SP", "EP", "GP", "PP"]:
            if f"({code.lower()})" in name_l or code.lower() in name_l.split(" ")[0].replace(",",""): item_type_sub_val = code; break

    item_type_attrs = {"main": item_type_main_val}
    if item_type_sub_val: item_type_attrs["sub"] = item_type_sub_val
    ET.SubElement(new_item_element, "item_type", attrib=item_type_attrs)
    return item_type_main_val, item_type_sub_val, original_type_abbr_val

def parse_weight_value(source_item, new_item_element): # Unchanged
    if source_item.findtext("weight"): sub_element_if_text(new_item_element, "weight", text=source_item.findtext("weight"), attributes={"unit": "lb"})
    if source_item.findtext("value"): sub_element_if_text(new_item_element, "value", text=source_item.findtext("value"), attributes={"currency": "GP"})

def parse_weapon_details(source_item, text_content, new_item_element, weapon_sub_type, item_name_text): # Modified
    weapon_cat = "Simple"
    prof_match = PROFICIENCY_PATTERN.search(text_content)
    if prof_match:
        prof_text_for_tag = prof_match.group(1).strip()
        parts = [p.strip() for p in prof_text_for_tag.split(',') if p.strip()]
        cat_text = parts[0].lower()
        specific_weapon_name_in_prof = parts[1].lower() if len(parts) > 1 else cat_text

        known_martial = ["battleaxe", "flail", "glaive", "greataxe", "greatsword", "halberd", "lance", "longsword", "maul", "pike", "rapier", "scimitar", "shortsword", "trident", "warhammer", "war pick", "whip", "blowgun", "hand crossbow", "heavy crossbow", "longbow", "musket", "pistol"]
        known_simple = ["club", "dagger", "greatclub", "handaxe", "javelin", "light hammer", "mace", "quarterstaff", "sickle", "spear", "dart", "light crossbow", "shortbow", "sling", "morningstar"]

        if cat_text == "martial" or specific_weapon_name_in_prof in known_martial or cat_text in known_martial : weapon_cat = "Martial"
        elif cat_text == "simple" or specific_weapon_name_in_prof in known_simple or cat_text in known_simple: weapon_cat = "Simple"
        elif cat_text == "firearms": weapon_cat = "Martial"
        if "psychic blade" in item_name_text.lower() and ("simple" in cat_text or "psychic blade" in cat_text): weapon_cat = "Simple"

        sub_element_if_text(new_item_element, "proficiency_requirement", text=prof_text_for_tag)
        text_content = text_content.replace(prof_match.group(0), "").strip()

    wd_attrs = {"category": weapon_cat, "type": weapon_sub_type if weapon_sub_type else "Melee"}
    weapon_details_el = ET.SubElement(new_item_element, "weapon_details", attrib=wd_attrs)
    dmg_attrs = {"dice": source_item.findtext("dmg1","").strip()}
    dmg_type_abbr = source_item.findtext("dmgType","").strip().upper()
    dmg_attrs["type"] = DAMAGE_TYPE_MAP.get(dmg_type_abbr, dmg_type_abbr if dmg_type_abbr else "Unknown")
    if source_item.findtext("dmg2"): dmg_attrs["versatile_dice"] = source_item.findtext("dmg2").strip()
    if dmg_attrs["dice"]: ET.SubElement(weapon_details_el, "damage", attrib=dmg_attrs)

    properties_el = ET.SubElement(weapon_details_el, "properties")
    prop_tag_text = source_item.findtext("property", "")
    if prop_tag_text:
        for prop_abbr in prop_tag_text.split(','):
            prop_abbr = prop_abbr.strip().upper()
            prop_name = WEAPON_PROPERTY_MAP.get(prop_abbr)
            if not prop_name and prop_abbr == 'M': continue
            if prop_name:
                prop_attrs = {"name": prop_name}
                if prop_name == "Thrown":
                    range_text = source_item.findtext("range","")
                    if "/" in range_text: parts = range_text.split('/'); prop_attrs.update({"range_short":parts[0].strip(), "range_long":parts[1].strip()})
                elif prop_name == "Ammunition":
                    range_text = source_item.findtext("range","")
                    if "/" in range_text: parts = range_text.split('/'); prop_attrs.update({"range_short":parts[0].strip(), "range_long":parts[1].strip()})
                    ammo_match = AMMO_TEXT_PATTERN.search(text_content)
                    if ammo_match: prop_attrs["ammo_type"] = ammo_match.group(1).strip().replace("\n",""); text_content = text_content.replace(ammo_match.group(0), "").strip()
                if prop_name == "Heavy":
                    heavy_req_match = re.search(r"(?:Strength|Dexterity) score isn't at least (\d+)", text_content, re.IGNORECASE) # Check for Str or Dex for Heavy, though glossary implies Str for melee
                    if heavy_req_match: prop_attrs["strength_requirement"] = heavy_req_match.group(1) # Storing as strength_requirement as per glossary for weapon property

                ET.SubElement(properties_el, "property", attrib=prop_attrs)
                # Remove property description text after processing the property
                if prop_name in PROPERTY_TEXT_PATTERNS:
                    text_content = PROPERTY_TEXT_PATTERNS[prop_name].sub("", text_content).strip()

    mastery_matches = MASTERY_PATTERN.findall(text_content)
    if mastery_matches:
        masteries_el = ET.SubElement(weapon_details_el, "mastery_options")
        original_mastery_text_block = ""
        # Find the whole block of mastery text to remove it once
        mastery_search = MASTERY_PATTERN.search(text_content)
        if mastery_search: original_mastery_text_block = mastery_search.group(0)

        for name, desc in mastery_matches: ET.SubElement(masteries_el, "mastery", name=name.strip(), default="true")

        if original_mastery_text_block: text_content = text_content.replace(original_mastery_text_block, "").strip()
    return text_content

def parse_armor_details(source_item, text_content, new_item_element, armor_sub_type): # Modified for Chain Shirt
    ad_attrs = {"category": armor_sub_type if armor_sub_type else "Unknown"}
    armor_details_el = ET.SubElement(new_item_element, "armor_details", attrib=ad_attrs)
    ac_val_str = source_item.findtext("ac","").strip()
    ac_rules = ARMOR_AC_RULES.get(armor_sub_type, {"add_dex": False})
    ac_attrs = {}

    if armor_sub_type == "Shield":
        shield_effect_el = source_item.find("effect[@type='ACBonus']")
        bonus_val = shield_effect_el.get("value") if shield_effect_el is not None and shield_effect_el.get("value") else "2"
        ac_attrs["bonus"] = bonus_val
        if shield_effect_el is not None and shield_effect_el.get("description"): text_content = text_content.replace(shield_effect_el.get("description"),"").strip()
        ET.SubElement(armor_details_el, "armor_class", attrib=ac_attrs)
    elif ac_val_str:
        ac_attrs["base"] = ac_val_str
        if ac_rules.get("add_dex"): ac_attrs["add_dex_modifier"] = "true"
        if ac_rules.get("add_dex") and ac_rules.get("max_dex_bonus") != "none": ac_attrs["max_dex_bonus"] = ac_rules["max_dex_bonus"]
        ET.SubElement(armor_details_el, "armor_class", attrib=ac_attrs)

    str_req = source_item.findtext("strength","").strip()
    if str_req:
        ET.SubElement(armor_details_el, "strength_requirement", value=str_req)
        text_content = re.sub(r"If the wearer has a Strength score lower than \d+, their speed is reduced by 10 feet\.\s*\n?", "", text_content, flags=re.IGNORECASE)

    stealth_dis_tag_present = source_item.findtext("stealth","").strip().upper() == "YES"
    stealth_text_pattern = r"The wearer has disadvantage on (?:Dexterity \(Stealth\)|Stealth \(Dexterity\)) checks\."
    stealth_text_match = re.search(stealth_text_pattern, text_content, re.IGNORECASE)

    if stealth_dis_tag_present or stealth_text_match:
        if new_item_element.find("armor_details/stealth_disadvantage") is None: # Avoid duplicates
            ET.SubElement(armor_details_el, "stealth_disadvantage", value="true")
        if stealth_text_match:
            text_content = text_content.replace(stealth_text_match.group(0), "").strip()

    if "Utilize Action to Don or Doff" in text_content and armor_sub_type == "Shield":
        sub_element_if_text(armor_details_el, "don_time", attributes={"description":"1 Action (Utilize)"})
        sub_element_if_text(armor_details_el, "doff_time", attributes={"description":"1 Action (Utilize)"})
        text_content = text_content.replace("Utilize Action to Don or Doff.", "").strip()
    return text_content

def parse_tool_details(source_item, text_content, new_item_element, tool_sub_type): # Modified text removal
    td_attrs = {"category": tool_sub_type if tool_sub_type else "Other"}
    tool_details_el = ET.SubElement(new_item_element, "tool_details", attrib=td_attrs)
    ability_match = re.search(r"Ability:\s*(\w+)", text_content, re.IGNORECASE)
    if ability_match:
        sub_element_if_text(tool_details_el, "associated_ability", attributes={"name":ability_match.group(1).strip()})
        text_content = text_content.replace(ability_match.group(0), "").strip() # Remove exact match

    # More careful removal of Utilize sections
    utilize_full_text_to_remove = ""
    util_iter = list(re.finditer(r"Utilize:\s*(.*?)(?=\nUtilize:|\nCraft:|\nSource:|$)", text_content, re.IGNORECASE | re.DOTALL))
    if util_iter:
        util_options_el = ET.SubElement(tool_details_el, "utilization_options")
        for util_match_obj in util_iter:
            utilize_full_text_to_remove += util_match_obj.group(0) # Accumulate full matched "Utilize:..." block
            util_full_desc = util_match_obj.group(1).strip()
            for util_opt_text in re.split(r",\s*or\s+(?![^(]*\))", util_full_desc):
                opt_attrs = {"description": util_opt_text.split("(DC")[0].strip()}
                dc_m = re.search(r"\(DC\s*(\d+)\)", util_opt_text)
                if dc_m: opt_attrs["dc"] = dc_m.group(1)
                ET.SubElement(util_options_el, "option", attrib=opt_attrs)
        text_content = text_content.replace(utilize_full_text_to_remove, "").strip() # Remove all utilize blocks at once

    craft_match = re.search(r"Craft:\s*(.*?)(?=\nUtilize:|\nSource:|$)", text_content, re.IGNORECASE | re.DOTALL)
    if craft_match and craft_match.group(1).strip():
        craft_items_el = ET.SubElement(tool_details_el, "craftable_items")
        for name in craft_match.group(1).strip().split(','):
            if name.strip(): sub_element_if_text(craft_items_el, "item_ref", text=name.strip())
        text_content = text_content.replace(craft_match.group(0), "").strip() # Remove exact match
    return text_content.strip()

def parse_consumable_effects(source_item, text_content, new_item_element, item_main_type, item_name_text): # Unchanged
    fully_parsed = False
    if item_main_type == "Potion" and "Potion of Healing" in item_name_text:
        effects_el = ET.SubElement(new_item_element, "effects")
        action_el = ET.SubElement(effects_el, "action", type="BonusAction", description="drink it or administer it to another creature within 5 feet")
        effect_el = ET.SubElement(action_el, "effect", type="Heal")
        ET.SubElement(effect_el, "dice").text = "2d4"; ET.SubElement(effect_el, "bonus").text = "2"
        sub_element_if_text(new_item_element, "consumable", attributes={"charges":"1", "on_last_charge_behavior":"consumed"})
        fully_parsed = True
    elif item_main_type == "Scroll":
        effects_el = ET.SubElement(new_item_element, "effects")
        dc = re.search(r"spell save DC is (\d+)", text_content, re.I); atk = re.search(r"attack bonus is \+(\d+)", text_content, re.I)
        desc = f"Allows casting of the spell on the scroll. Spell Save DC {dc.group(1) if dc else 'N/A'}. Attack Bonus +{atk.group(1) if atk else 'N/A'}. Scroll disintegrates."
        sub_element_if_text(effects_el, "description_text", text=desc)
        sub_element_if_text(new_item_element, "consumable", attributes={"on_last_charge_behavior":"disintegrates"})
        fully_parsed = True
    elif "Basic Poison" in item_name_text:
        effects_el = ET.SubElement(new_item_element, "effects")
        action_el = ET.SubElement(effects_el, "action", type="BonusAction", description="coat one weapon or up to three pieces of Ammunition")
        eff_desc = "A creature that takes Piercing or Slashing damage from the poisoned weapon or ammunition takes an extra 1d4 Poison damage. Once applied, the poison retains potency for 1 minute or until its damage is dealt, whichever comes first."
        effect_el = ET.SubElement(action_el, "effect", type="ExtraDamage", description=eff_desc)
        ET.SubElement(effect_el, "dice").text = "1d4"; ET.SubElement(effect_el, "damage_type").text = "Poison"
        sub_element_if_text(new_item_element, "consumable", attributes={"charges":"1", "on_last_charge_behavior":"consumed"})
        fully_parsed = True
    elif item_name_text == "Acid [2024]" and item_main_type == "Gear":
        effects_el = ET.SubElement(new_item_element, "effects")
        action_el = ET.SubElement(effects_el, "action", type="AttackReplacement", description="throwing a vial of Acid. Target one creature or object you can see within 20 feet")
        effect_el = ET.SubElement(action_el, "effect", type="Damage", save_required="true", save_ability="Dexterity", save_dc_formula="8+DEX+PB")
        ET.SubElement(effect_el, "dice").text = "2d6"; ET.SubElement(effect_el, "damage_type").text = "Acid"
        sub_element_if_text(new_item_element, "consumable", attributes={"charges":"1", "on_last_charge_behavior":"consumed"})
        fully_parsed = True
    elif item_name_text == "Alchemist's Fire [2024]" and item_main_type == "Gear":
        effects_el = ET.SubElement(new_item_element, "effects")
        action_el = ET.SubElement(effects_el, "action", type="AttackReplacement", description="throwing a flask of Alchemist's Fire. Target one creature or object you can see within 20 feet")
        effect_el = ET.SubElement(action_el, "effect", type="Damage", save_required="true", save_ability="Dexterity", save_dc_formula="8+DEX+PB", description="Takes 1d4 Fire damage and start burning.")
        ET.SubElement(effect_el, "dice").text = "1d4"; ET.SubElement(effect_el, "damage_type").text = "Fire"
        sub_element_if_text(new_item_element, "consumable", attributes={"charges":"1", "on_last_charge_behavior":"consumed"})
        fully_parsed = True
    elif item_name_text == "Holy Water [2024]" and item_main_type == "Gear":
        dice = source_item.findtext("roll","2d8").strip()
        effects_el = ET.SubElement(new_item_element, "effects")
        action_el = ET.SubElement(effects_el, "action", type="AttackReplacement", description="throwing a flask of Holy Water. Target one creature you can see within 20 feet")
        effect_el = ET.SubElement(action_el, "effect", type="Damage", save_required="true", save_ability="Dexterity", save_dc_formula="8+DEX+PB", description=f"{dice} Radiant damage if it is a Fiend or an Undead.")
        ET.SubElement(effect_el, "dice").text = dice; ET.SubElement(effect_el, "damage_type").text = "Radiant"
        sub_element_if_text(effect_el, "condition", text="Target is a Fiend or an Undead")
        sub_element_if_text(new_item_element, "consumable", attributes={"charges":"1", "on_last_charge_behavior":"consumed"})
        fully_parsed = True
    return "" if fully_parsed else text_content

def parse_xml_items(source_file_path, output_file_path): # Minor changes to main loop text handling
    try: tree = ET.parse(source_file_path)
    except Exception as e: print(f"Error parsing {source_file_path}: {e}"); return
    root = tree.getroot()
    new_root = ET.Element("compendium", version="1.0")

    for source_item in root.findall("item"):
        new_item_el = ET.SubElement(new_root, "item")
        name = parse_item_name(source_item, new_item_el)
        text = source_item.findtext("text","").strip()
        text = parse_source(text, new_item_el)
        main_type, sub_type, orig_abbr = parse_item_type_and_rarity(source_item, new_item_el, name)
        parse_weight_value(source_item, new_item_el)

        if source_item.findtext("magic","").strip().upper() == "YES":
            if new_item_el.find("rarity") is None: ET.SubElement(new_item_el, "rarity", type="Common")
            if new_item_el.find("attunement") is None: ET.SubElement(new_item_el, "attunement", required="false")

        is_weapon = (source_item.find("dmg1") is not None) or (main_type == "Weapon")
        is_armor_shield = (source_item.find("ac") is not None) or (main_type == "Armor") or (main_type == "Shield")

        if is_weapon:
            weapon_sub = "Melee" if orig_abbr == "M" else "Ranged" if orig_abbr == "R" else sub_type
            if name.lower() in ["staff [2024]", "wooden staff [2024]"]: weapon_sub = "Melee"
            text = parse_weapon_details(source_item, text, new_item_el, weapon_sub, name)
        if is_armor_shield: text = parse_armor_details(source_item, text, new_item_el, sub_type)
        if main_type == "Tool": text = parse_tool_details(source_item, text, new_item_el, sub_type)
        text = parse_consumable_effects(source_item, text, new_item_el, main_type, name)

        if "Trinket [2024]" in name:
            desc_el = ET.SubElement(new_item_el, "description_text")
            intro_text, _, table_content_text = text.partition("Trinkets:\n")
            if intro_text.strip(): sub_element_if_text(desc_el, "p", text=intro_text.strip())
            if table_content_text:
                table_el = ET.SubElement(desc_el, "table")
                header_el = ET.SubElement(table_el, "header")
                sub_element_if_text(header_el, "col", attributes={"label":"1d100"})
                sub_element_if_text(header_el, "col", attributes={"label":"Trinket"})
                for line in table_content_text.splitlines():
                    line = line.strip()
                    if "|" in line:
                        roll_parts = line.split("|",1)
                        if len(roll_parts) == 2:
                            roll, desc_cell = roll_parts[0].strip(), roll_parts[1].strip()
                            if roll.replace("0","").isdigit() or roll == "100":
                                row = ET.SubElement(table_el, "row")
                                sub_element_if_text(row, "cell", text=roll); sub_element_if_text(row, "cell", text=desc_cell)
                text = "" # Trinket table text is now fully structured or part of intro.

        # Final cleanup for any remaining general property descriptions not caught earlier
        # This should be less necessary now that parse_weapon_details handles its own property text.
        if text.strip():
            # Check if it's just leftover from a property that wasn't fully cleaned by parse_weapon_details
            # (e.g. if a property name was in text but not in the <property> tag)
            # This is a bit broad; ideally, all structured text is removed by the specific parsers.
            temp_text = text
            for prop_key_abbr, prop_mapped_name in WEAPON_PROPERTY_MAP.items():
                 if prop_mapped_name in PROPERTY_TEXT_PATTERNS:
                     temp_text = PROPERTY_TEXT_PATTERNS[prop_mapped_name].sub("", temp_text).strip()

            if temp_text.strip(): # If text still remains after this additional check
                desc_el = ET.SubElement(new_item_el, "description_text")
                for para in temp_text.split('\n\n'):
                    if para.strip(): sub_element_if_text(desc_el, "p", text=para.strip())
            elif not temp_text.strip() and text.strip(): # If temp_text is empty, it means text was only property descriptions
                pass # Do not add empty description_text

    new_tree = ET.ElementTree(new_root)
    ET.indent(new_tree, space="  ")
    new_tree.write(output_file_path, encoding="UTF-8", xml_declaration=True)
    print(f"Parsing complete. Output at {output_file_path}")

if __name__ == '__main__':
    parse_xml_items("01_Core/01_Players_Handbook_2024/items-phb24.xml", "items-phb24-structured.xml")
