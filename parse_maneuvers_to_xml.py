import json
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def create_xml_element(parent, tag, text=None, attributes=None):
    """Helper to create and append an XML element."""
    element = ET.SubElement(parent, tag)
    if text:
        element.text = str(text).strip()
    if attributes:
        for key, value in attributes.items():
            element.set(key, str(value))
    return element

def parse_maneuver_description(maneuver_name, description):
    """
    Attempts to parse the maneuver description to extract structured information.
    Returns a dictionary with parsed fields. This will be a complex part
    and will likely need iterative refinement.
    """
    parsed_data = {
        "activation_type": None,
        "activation_trigger": None,
        "effects": [],
        "saving_throw": None,
        "notes": []
    }

    # Common phrases
    description_lower = description.lower()

    # Activation Type
    # Order matters: more specific should come first.
    if "when you hit a creature with a weapon attack" in description_lower:
        # This is a common prefix, needs to be distinguished if it's the primary activation or part of an effect
        if any(kw.lower() in maneuver_name.lower() for kw in ["Disarming", "Distracting", "Goading", "Maneuvering", "Menacing", "Pushing", "Sweeping", "Trip"]):
             parsed_data["activation_type"] = "WhenHittingWithWeaponAttack"
    elif "when you make a dexterity (stealth) check or an initiative roll" in description_lower: # Ambush
        parsed_data["activation_type"] = "WhenMakingCheckOrInitiative"
        match = re.search(r"When you make a Dexterity \(Stealth\) check or an initiative roll", description, re.IGNORECASE)
        if match:
            parsed_data["activation_trigger"] = match.group(0).strip(" .,")
    elif "when you make a charisma (intimidation), a charisma (performance), or a charisma (persuasion) check" in description_lower: # Commanding Presence
        parsed_data["activation_type"] = "WhenMakingAbilityCheck"
        match = re.search(r"When you make a Charisma \(Intimidation\), a Charisma \(Performance\), or a Charisma \(Persuasion\) check", description, re.IGNORECASE)
        if match:
            parsed_data["activation_trigger"] = match.group(0).strip(" .,")
    elif "when you make an intelligence (investigation), an intelligence (history), or a wisdom (insight) check" in description_lower: # Tactical Assessment
        parsed_data["activation_type"] = "WhenMakingAbilityCheck"
        match = re.search(r"When you make an Intelligence \(Investigation\), an Intelligence \(History\), or a Wisdom \(Insight\) check", description, re.IGNORECASE)
        if match:
            parsed_data["activation_trigger"] = match.group(0).strip(" .,")
    elif "when you make a weapon attack roll against a creature" in description_lower and "precision attack" in maneuver_name.lower(): # Precision Attack
        parsed_data["activation_type"] = "WhenMakingWeaponAttackRoll"
        match = re.search(r"When you make a weapon attack roll against a creature", description, re.IGNORECASE)
        if match:
            parsed_data["activation_trigger"] = match.group(0).strip(" .,")
    elif "when you're within 5 feet of a creature on your turn" in description_lower and "switch places" in description_lower: # Bait and Switch
        parsed_data["activation_type"] = "Action" # Implied by "on your turn" and spending movement
        parsed_data["activation_trigger"] = "When you're within 5 feet of a creature on your turn"
    elif "when a creature you can see moves into the reach" in description_lower: # Brace
        parsed_data["activation_type"] = "Reaction"
        parsed_data["activation_trigger"] = "When a creature you can see moves into the reach you have with the melee weapon you're wielding"
    elif "when you take the attack action on your turn, you can forgo one of your attacks and use a bonus action" in description_lower: # Commander's Strike
        parsed_data["activation_type"] = "BonusAction"
        parsed_data["activation_trigger"] = "When you take the Attack action on your turn and forgo one of your attacks"
    elif "when you move, you can expend one superiority die" in description_lower: # Evasive Footwork
        parsed_data["activation_type"] = "WhenMoving"
    elif "you can expend one superiority die and use a bonus action on your turn to feint" in description_lower: # Feinting Attack
        parsed_data["activation_type"] = "BonusAction"
        parsed_data["activation_trigger"] = "On your turn to feint"
    elif "immediately after you hit a creature with a melee attack on your turn" in description_lower and "as a bonus action" in description_lower:
        parsed_data["activation_type"] = "BonusAction"
        parsed_data["activation_trigger"] = "Immediately after you hit a creature with a melee attack on your turn"
    elif "when you make a melee weapon attack on your turn" in description_lower and "increase your reach" in description_lower:
        parsed_data["activation_type"] = "WhenMakingMeleeWeaponAttack" # Or PartOfAttackAction
    elif "when another creature damages you with a melee attack" in description_lower:
        parsed_data["activation_type"] = "Reaction"
        parsed_data["activation_trigger"] = "When another creature damages you with a melee attack"
    elif "when you make a weapon attack roll against a creature" in description_lower and "precision attack" in maneuver_name.lower():
        parsed_data["activation_type"] = "WhenMakingWeaponAttackRoll" # Special for Precision Attack
        parsed_data["activation_trigger"] = "When you make a weapon attack roll against a creature"
    elif "as a bonus action, you can expend one superiority die and make a ranged attack" in description_lower:
        parsed_data["activation_type"] = "BonusAction"
        parsed_data["activation_trigger"] = "As a bonus action to make a ranged attack with a thrown weapon"
    elif "on your turn, you can use a bonus action and expend one superiority die to bolster" in description_lower:
        parsed_data["activation_type"] = "BonusAction"
        parsed_data["activation_trigger"] = "On your turn to bolster the resolve of one of your companions"
    elif "when a creature misses you with a melee attack" in description_lower:
        parsed_data["activation_type"] = "Reaction"
        parsed_data["activation_trigger"] = "When a creature misses you with a melee attack"

    # Default if nothing specific found yet for activation
    if parsed_data["activation_type"] is None:
        if "as a bonus action" in description_lower:
            parsed_data["activation_type"] = "BonusAction"
        elif "as a reaction" in description_lower: # generic reaction
            parsed_data["activation_type"] = "Reaction"
            match = re.search(r"as your reaction (to .*?[\.,])", description, re.IGNORECASE)
            if not match:
                match = re.search(r"reaction (when .*?[\.,])", description, re.IGNORECASE)
            if match:
                 parsed_data["activation_trigger"] = match.group(1).strip(" .,")


    # Effects - this is highly pattern-based and simplified
    effect_details = {} # Used for currently parsed effect before adding to list

    # --- PARSE ACTIVATION SPECIFIC EFFECTS FIRST ---
    # These often define the primary outcome of the maneuver.
    if maneuver_name == "Ambush":
        parsed_data["effects"].append({
            "type": "RollBonus", "roll_bonus_dice_type": "SuperiorityDie",
            "roll_bonus_applies_to_roll": "StealthCheckOrInitiativeRoll"
        })
    elif maneuver_name == "Commanding Presence":
        effect = {"type": "RollBonus", "roll_bonus_dice_type": "SuperiorityDie", "roll_bonus_applies_to_roll": "AbilityCheck"}
        m_skill = re.search(r"charisma \((intimidation|performance|persuasion)\)", description_lower)
        if m_skill:
            effect["roll_bonus_ability_for_check"] = "Charisma"
            effect["roll_bonus_skill_for_check"] = m_skill.group(1) # intimidation, performance, or persuasion
        parsed_data["effects"].append(effect)
    elif maneuver_name == "Tactical Assessment":
        effect = {"type": "RollBonus", "roll_bonus_dice_type": "SuperiorityDie", "roll_bonus_applies_to_roll": "AbilityCheck"}
        m_skill = re.search(r"intelligence \((investigation|history)\)|wisdom \((insight)\)", description_lower)
        if m_skill:
            if "intelligence" in m_skill.group(0): effect["roll_bonus_ability_for_check"] = "Intelligence"
            if "wisdom" in m_skill.group(0): effect["roll_bonus_ability_for_check"] = "Wisdom"
            if m_skill.group(1): effect["roll_bonus_skill_for_check"] = m_skill.group(1) # investigation or history
            else: effect["roll_bonus_skill_for_check"] = m_skill.group(2) # insight
        parsed_data["effects"].append(effect)
    elif maneuver_name == "Precision Attack":
        parsed_data["effects"].append({
            "type": "RollBonus", "roll_bonus_dice_type": "SuperiorityDie",
            "roll_bonus_applies_to_roll": "AttackRoll"
        })

    # --- GENERIC EFFECT PARSING ---

    # AC Bonus
    if "gains a bonus to ac equal to the number rolled" in description_lower: # Bait and Switch
        parsed_data["effects"].append({
            "type": "ACBonus", "ac_bonus_value_from_roll": "SuperiorityDie",
            "target": "self_or_other_creature_your_choice", "duration": "until_the_start_of_your_next_turn"
        })
    elif "adding the number rolled to your ac until you stop moving" in description_lower: # Evasive Footwork
        parsed_data["effects"].append({
            "type": "ACBonus", "ac_bonus_value_from_roll": "SuperiorityDie",
            "target": "self", "duration": "until_you_stop_moving"
        })

    # Saving Throws & Associated Conditions/Effects
    save_match = re.search(r"target must make a (Strength|Wisdom) saving throw\. On a failed save, (it drops the object you choose|the target has disadvantage on all attack rolls against targets other than you until the end of your next turn|it is frightened of you until the end of your next turn|you push the target up to 15 feet away from you|you knock the target prone)", description, re.IGNORECASE)
    if save_match:
        parsed_data["saving_throw"] = {
            "ability": save_match.group(1),
            "dc_formula_ref": "ManeuverSaveDC"
        }
        failed_effect_text = save_match.group(2).lower()
        associated_effect = {}
        if "drops the object" in failed_effect_text: # Disarming Attack
            parsed_data["saving_throw"]["required_for_effect"] = "Disarm"
            associated_effect = {"type": "Condition", "condition_inflicted_name": "Disarmed", "condition_duration": "object_lands_at_feet"}
            parsed_data["notes"].append("The object lands at its feet.")
        elif "disadvantage on all attack rolls against targets other than you" in failed_effect_text: # Goading Attack
            parsed_data["saving_throw"]["required_for_effect"] = "AvoidGoad"
            associated_effect = {"type": "Condition", "condition_inflicted_name": "Goaded", "condition_duration": "until_end_of_your_next_turn",
                                 "disadvantage_on_attack_rolls": {"against_targets_other_than_self": "true", "duration": "until_end_of_your_next_turn"}}
        elif "frightened of you" in failed_effect_text: # Menacing Attack
            parsed_data["saving_throw"]["required_for_effect"] = "AvoidFrighten"
            associated_effect = {"type": "Condition", "condition_inflicted_name": "Frightened", "condition_duration": "until_end_of_your_next_turn"}
        elif "push the target up to 15 feet away" in failed_effect_text: # Pushing Attack
            parsed_data["saving_throw"]["required_for_effect"] = "AvoidPush"
            associated_effect = {"type": "Movement", "movement_effect_type": "ForcedPush", "movement_distance_feet": "15"}
        elif "knock the target prone" in failed_effect_text: # Trip Attack
            parsed_data["saving_throw"]["required_for_effect"] = "AvoidTrip"
            associated_effect = {"type": "Condition", "condition_inflicted_name": "Prone"}

        if associated_effect:
            parsed_data["effects"].append(associated_effect)


    # --- OTHER SPECIFIC EFFECTS BY NAME (if not covered by above or need additions) ---
    if maneuver_name == "Bait and Switch":
        # The AC bonus is already handled. Add movement effect.
        parsed_data["effects"].append({
            "type": "Movement", "movement_effect_type": "SwitchPlaces",
            "movement_does_not_provoke_opportunity_attack": "true",
            "notes": "Provided you spend at least 5 feet of movement and the creature is willing and isn't incapacitated."
        })

    if maneuver_name == "Commander's Strike":
        parsed_data["effects"].append({
            "type": "AdditionalAttack", "additional_attack_trigger": "ReactionFromAlly",
            "damage_bonus_dice": "SuperiorityDie" # The ally adds the die
        })
    if maneuver_name == "Distracting Strike":
         parsed_data["effects"].append({ # This is the "distraction" effect itself
            "type": "Condition", "condition_inflicted_name": "Distracted",
            "advantage_on_next_attack_roll": {"by_attacker_other_than_self": "true", "duration": "until_start_of_your_next_turn"}
        })
    if maneuver_name == "Feinting Attack":
        parsed_data["effects"].append({
            "type": "Advantage", "advantage_on_attack_roll": "self_next_attack_this_turn",
            "target_description": "one_creature_within_5_feet"
        })
    if maneuver_name == "Grappling Strike":
         parsed_data["effects"].append({
            "type": "RollBonus", "roll_bonus_dice_type": "SuperiorityDie",
            "roll_bonus_applies_to_roll": "AbilityCheck",
            "roll_bonus_ability_for_check": "Strength", "roll_bonus_skill_for_check": "Athletics",
            "effect_notes": "When attempting to grapple as a bonus action after hitting with a melee attack." # Changed from "notes" to avoid clash
        })
    if maneuver_name == "Lunging Attack":
        parsed_data["effects"].append({"type": "ReachIncrease", "value": "5_feet", "duration": "for_that_attack"})
    if maneuver_name == "Maneuvering Attack":
        parsed_data["effects"].append({
            "type": "Movement", "movement_effect_type": "AllyMove",
            "movement_distance_feet": "HalfSpeed", "movement_does_not_provoke_opportunity_attack": "true_from_your_target"
        })
    if maneuver_name == "Parry":
        parsed_data["effects"].append({
            "type": "DamageReduction", "damage_reduction_roll": "SuperiorityDie",
            "damage_reduction_add_modifier": "Dexterity"
        })
    if maneuver_name == "Quick Toss":
        parsed_data["notes"].append("You can draw the weapon as part of making this attack.")
    if maneuver_name == "Rally":
        parsed_data["effects"].append({
            "type": "GainTemporaryHitPoints", "temporary_hit_points_roll": "SuperiorityDie",
            "temporary_hit_points_add_modifier": "Charisma"
        })
    # Riposte: main effect is attack via reaction (activation), damage bonus below.
    if maneuver_name == "Sweeping Attack":
        parsed_data["effects"].append({
            "type": "Damage", "target_description": "another_creature_within_5_feet_of_original_target_and_within_your_reach",
            "damage_roll_dice_type": "SuperiorityDie", # Damage is the roll of the die
            "damage_type_matches_original_attack": "true",
            "condition_text": "If the original attack roll would hit the second creature"
        })

    # --- GENERIC "ADD SUPERIORITY DIE TO DAMAGE ROLL" ---
    # This is a very common effect, add it if not already part_of another more specific damage effect.
    if "add the superiority die to the attack's damage roll" in description_lower or \
       "add the superiority die to the weapon's damage roll" in description_lower or \
       "add the superiority die to this damage" in description_lower:

        # Check if a damage-related effect that *includes* the superiority die is already present
        damage_already_accounted_for = False
        for eff in parsed_data["effects"]:
            if eff.get("type") == "AdditionalAttack" and eff.get("damage_bonus_dice") == "SuperiorityDie": # Commander's Strike
                damage_already_accounted_for = True
                break
            if eff.get("type") == "Damage" and eff.get("damage_roll_dice_type") == "SuperiorityDie": # Sweeping Attack
                damage_already_accounted_for = True
                break
            # Brace, Riposte will just have this generic damage bonus.
            # Disarming, Goading, Menacing, Pushing, Trip, Lunging, Feinting, Distracting, Maneuvering, Quick Toss also add to damage.

        if not damage_already_accounted_for:
            # Avoid adding if the *only* effect is already a RollBonus to damage (should be DamageBonus type)
            is_only_roll_bonus_damage = len(parsed_data["effects"]) == 1 and \
                                      parsed_data["effects"][0].get("type") == "RollBonus" and \
                                      parsed_data["effects"][0].get("roll_bonus_applies_to_roll") == "DamageRoll"
            if not is_only_roll_bonus_damage:
                 parsed_data["effects"].append({"type": "DamageBonus", "damage_bonus_dice_type": "SuperiorityDie"})


    # --- NOTES ---
    if "provided you aren't incapacitated" in description_lower:
        parsed_data["notes"].append("Provided you aren't incapacitated.")
    # Bait and Switch note is handled with its specific effect.
    # if "provided you spend at least 5 feet of movement and the creature is willing and isn't incapacitated" in description_lower:
    #     parsed_data["notes"].append("Provided you spend at least 5 feet of movement and the creature is willing and isn't incapacitated.")
    if "if the target is large or smaller" in description_lower:
        # This note is often tied to save effects (Pushing, Trip)
        # Check if a save is present, if so, maybe add to save notes or effect notes.
        # For now, keep as general note.
        parsed_data["notes"].append("If the target is Large or smaller.")


    # Remove duplicate notes
    if parsed_data["notes"]:
        parsed_data["notes"] = sorted(list(set(parsed_data["notes"])))

    # Filter out empty effects if any were added as {}
    parsed_data["effects"] = [eff for eff in parsed_data["effects"] if eff]


    return parsed_data


def main():
    try:
        with open("maneuvers.json", 'r') as f:
            maneuvers_data = json.load(f)
    except FileNotFoundError:
        print("Error: maneuvers.json not found.")
        return
    except json.JSONDecodeError:
        print("Error: maneuvers.json is not valid JSON.")
        return

    root = ET.Element("maneuvers_list")
    # Potentially add a comment about the source/schema or Battle Master context
    # root.append(ET.Comment("Maneuvers for the Battle Master Fighter, conforming to glossary_xml_tags_v1.txt structure where applicable"))


    for name, description in maneuvers_data.items():
        maneuver_el = create_xml_element(root, "maneuver", attributes={"name": name})

        # Source - Placeholder, actual page number needed
        create_xml_element(maneuver_el, "source", attributes={"book": "Player's Handbook 2024", "page": "TODO"})

        create_xml_element(maneuver_el, "description_text", text=description)

        # Parse description for structured data
        parsed_info = parse_maneuver_description(name, description)

        if parsed_info["activation_type"] or parsed_info["activation_trigger"]:
            activation_el = create_xml_element(maneuver_el, "activation")
            action_attrs = {}
            if parsed_info["activation_type"]:
                action_attrs["type"] = parsed_info["activation_type"]
            if parsed_info["activation_trigger"]:
                action_attrs["trigger"] = parsed_info["activation_trigger"]
            if action_attrs: #Only create if there's something to put in it
                create_xml_element(activation_el, "action", attributes=action_attrs)

        # Cost is always 1 superiority die
        create_xml_element(maneuver_el, "cost", attributes={"resource": "SuperiorityDie", "value": "1"})

        if parsed_info["effects"]: #Only create <effects> if there are any
            effects_el = create_xml_element(maneuver_el, "effects")
            for effect_data_original in parsed_info["effects"]:
                effect_data = effect_data_original.copy() # Work with a copy
                effect_attrs = {"type": effect_data.pop("type")} # Base type

                # Specific attributes for different effect types
                if effect_attrs["type"] == "RollBonus":
                    if "roll_bonus_dice_type" in effect_data: effect_attrs["dice_type"] = effect_data.pop("roll_bonus_dice_type")
                    if "roll_bonus_applies_to_roll" in effect_data: effect_attrs["applies_to_roll"] = effect_data.pop("roll_bonus_applies_to_roll")
                    if "roll_bonus_ability_for_check" in effect_data: effect_attrs["ability_for_check"] = effect_data.pop("roll_bonus_ability_for_check")
                    if "roll_bonus_skill_for_check" in effect_data: effect_attrs["skill_for_check"] = effect_data.pop("roll_bonus_skill_for_check")
                elif effect_attrs["type"] == "ACBonus":
                    if "ac_bonus_value_from_roll" in effect_data: effect_attrs["value_from_roll"] = effect_data.pop("ac_bonus_value_from_roll")
                    if "target" in effect_data: effect_attrs["target"] = effect_data.pop("target")
                    if "duration" in effect_data: effect_attrs["duration"] = effect_data.pop("duration")
                elif effect_attrs["type"] == "DamageBonus":
                     if "damage_bonus_dice_type" in effect_data: effect_attrs["dice_type"] = effect_data.pop("damage_bonus_dice_type")
                elif effect_attrs["type"] == "AdditionalAttack":
                    if "additional_attack_trigger" in effect_data: effect_attrs["trigger"] = effect_data.pop("additional_attack_trigger")
                    if "damage_bonus_dice" in effect_data: effect_attrs["damage_bonus_dice"] = effect_data.pop("damage_bonus_dice")
                elif effect_attrs["type"] == "Movement":
                    if "movement_effect_type" in effect_data: effect_attrs["movement_type"] = effect_data.pop("movement_effect_type")
                    if "movement_distance_feet" in effect_data: effect_attrs["distance_feet"] = effect_data.pop("movement_distance_feet")
                    if "movement_does_not_provoke_opportunity_attack" in effect_data: effect_attrs["does_not_provoke_opportunity_attack"] = effect_data.pop("movement_does_not_provoke_opportunity_attack")
                elif effect_attrs["type"] == "Condition":
                    if "condition_inflicted_name" in effect_data: effect_attrs["name"] = effect_data.pop("condition_inflicted_name")
                    if "condition_duration" in effect_data: effect_attrs["duration"] = effect_data.pop("condition_duration")
                elif effect_attrs["type"] == "DamageReduction":
                    if "damage_reduction_roll" in effect_data: effect_attrs["roll"] = effect_data.pop("damage_reduction_roll")
                    if "damage_reduction_add_modifier" in effect_data: effect_attrs["add_modifier"] = effect_data.pop("damage_reduction_add_modifier")
                elif effect_attrs["type"] == "GainTemporaryHitPoints":
                    if "temporary_hit_points_roll" in effect_data: effect_attrs["roll"] = effect_data.pop("temporary_hit_points_roll")
                    if "temporary_hit_points_add_modifier" in effect_data: effect_attrs["add_modifier"] = effect_data.pop("temporary_hit_points_add_modifier")
                elif effect_attrs["type"] == "Advantage":
                    if "advantage_on_attack_roll" in effect_data: effect_attrs["on_attack_roll"] = effect_data.pop("advantage_on_attack_roll")
                    if "target_description" in effect_data: effect_attrs["target"] = effect_data.pop("target_description")
                elif effect_attrs["type"] == "ReachIncrease":
                    if "value" in effect_data: effect_attrs["value"] = effect_data.pop("value")
                    if "duration" in effect_data: effect_attrs["duration"] = effect_data.pop("duration")
                elif effect_attrs["type"] == "Damage":
                    if "target_description" in effect_data: effect_attrs["target"] = effect_data.pop("target_description")
                    if "damage_roll_dice_type" in effect_data: effect_attrs["dice_type"] = effect_data.pop("damage_roll_dice_type")
                    if "damage_type_matches_original_attack" in effect_data: effect_attrs["type_matches_original_attack"] = effect_data.pop("damage_type_matches_original_attack")
                    if "condition_text" in effect_data: effect_attrs["condition"] = effect_data.pop("condition_text")

                sub_elements_data = {}
                if "advantage_on_next_attack_roll" in effect_data and isinstance(effect_data["advantage_on_next_attack_roll"], dict):
                    sub_elements_data["advantage_on_next_attack_roll"] = effect_data.pop("advantage_on_next_attack_roll")
                if "disadvantage_on_attack_rolls" in effect_data and isinstance(effect_data["disadvantage_on_attack_rolls"], dict):
                    sub_elements_data["disadvantage_on_attack_rolls"] = effect_data.pop("disadvantage_on_attack_rolls")

                current_effect_el = create_xml_element(effects_el, "effect", attributes=effect_attrs)

                for sub_tag, sub_attrs in sub_elements_data.items():
                    create_xml_element(current_effect_el, sub_tag, attributes=sub_attrs)

                # Add any remaining data in effect_data as simple text sub-elements or attributes
                # For "effect_notes" from Grappling Strike
                if "effect_notes" in effect_data:
                    create_xml_element(current_effect_el, "notes", text=effect_data.pop("effect_notes"))

                for key, val in effect_data.items(): # any other remaining items
                     create_xml_element(current_effect_el, key.replace(" ", "_"), text=str(val))


        if parsed_info["saving_throw"]:
            save_attrs = parsed_info["saving_throw"].copy()
            create_xml_element(maneuver_el, "saving_throw", attributes=save_attrs)

        if parsed_info["notes"]:
            notes_el = create_xml_element(maneuver_el, "notes")
            for note_text in parsed_info["notes"]:
                create_xml_element(notes_el, "note", text=note_text)

    xml_string = prettify_xml(root)

    try:
        with open("maneuvers.xml", 'w') as f:
            f.write(xml_string)
        print("Successfully generated maneuvers.xml (v2)")
    except IOError:
        print("Error: Could not write to maneuvers.xml")

if __name__ == "__main__":
    main()
