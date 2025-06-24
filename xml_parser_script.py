import xml.etree.ElementTree as ET
import json
import os
import xmltodict
from collections import OrderedDict

def parse_xml_to_ordered_dict(xml_string):
    """Parses an XML string to an OrderedDict to preserve element order."""
    try:
        # Replace problematic XML entities manually if necessary, though xmltodict should handle most
        # xml_string = xml_string.replace('&', '&amp;') # Example, be careful with this

        # Parse with xmltodict, which generally handles entities well
        # and preserves order by default (though dicts in Python 3.7+ are ordered)
        # Ns_separator was removed as it caused errors with the current version.
        # The XMLs don't appear to use namespaces in a way that requires this.
        parsed_dict = xmltodict.parse(xml_string)
        return parsed_dict
    except Exception as e:
        print(f"Error parsing XML string with xmltodict: {e}")
        # Fallback or more robust error handling can be added here
        # For instance, try lxml if available, or a simpler regex-based cleanup
        # For now, we'll re-raise to see the error clearly during development
        raise

def convert_xml_to_json(xml_filepath, json_filepath):
    """Converts an XML file to a JSON file, ensuring UTF-8 and handling entities."""
    try:
        with open(xml_filepath, 'r', encoding='utf-8') as xml_file:
            xml_content = xml_file.read()

        # Basic corrections / normalizations
        # Ensure XML declaration is UTF-8
        if xml_content.startswith("<?xml version='1.0' encoding='UTF-8'?>"):
            pass # Already correct
        elif xml_content.startswith("<?xml version='1.0' encoding='utf-8'?>"):
            xml_content = xml_content.replace("encoding='utf-8'", "encoding='UTF-8'", 1)
        else:
            # Add or correct XML declaration if missing or different
            import re
            if xml_content.startswith("<?xml"):
                xml_content = re.sub(r"<\?xml.*?\?>", "<?xml version='1.0' encoding='UTF-8'?>", xml_content, count=1)
            else:
                xml_content = "<?xml version='1.0' encoding='UTF-8'?>\n" + xml_content

        # Direct parse attempt. Manual fixes will be applied to files that fail.
        ordered_data = parse_xml_to_ordered_dict(xml_content)

        # Create directory for JSON file if it doesn't exist
        os.makedirs(os.path.dirname(json_filepath), exist_ok=True)

        with open(json_filepath, 'w', encoding='UTF-8') as json_file:
            json.dump(ordered_data, json_file, indent=2, ensure_ascii=False)

        return True, None

    except FileNotFoundError:
        return False, f"File not found: {xml_filepath}"
    except xmltodict.expat.ExpatError as e: # Catching ExpatError specifically
        return False, f"XML Parse Error (xmltodict/expat): {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

def process_files(xml_files_list):
    base_dir = "01_Core"
    output_base_dir = "01_Core_JSON"

    # Create the root JSON output directory if it doesn't exist
    os.makedirs(output_base_dir, exist_ok=True)

    error_files = []

    for xml_relative_path in xml_files_list:
        xml_full_path = xml_relative_path
        # Construct the output path, maintaining subdirectory structure
        # Remove "01_Core/" prefix for constructing json_relative_path
        path_inside_core = xml_relative_path[len("01_Core/"):] if xml_relative_path.startswith("01_Core/") else xml_relative_path

        json_relative_path = os.path.join(output_base_dir, path_inside_core)
        json_full_path = os.path.splitext(json_relative_path)[0] + ".json"

        # Ensure the subdirectories for JSON files exist
        json_dir = os.path.dirname(json_full_path)
        if not os.path.exists(json_dir):
            os.makedirs(json_dir, exist_ok=True)

        # print(f"Processing {xml_full_path} -> {json_full_path}")
        success, error_message = convert_xml_to_json(xml_full_path, json_full_path)
        if not success:
            error_files.append({'file': xml_full_path, 'error': error_message})
            print(f"Failed to convert {xml_full_path}: {error_message}")
        else:
            print(f"Successfully converted {xml_full_path} to {json_full_path}")

    if error_files:
        print("\n--- Files with errors ---")
        for entry in error_files:
            print(f"File: {entry['file']}, Error: {entry['error']}")
    else:
        print("\nAll files processed successfully.")

if __name__ == "__main__":
    # This list will be populated by the calling agent
    files_to_process = [
        "01_Core/backgrounds/backgrounds-dmg24.xml",
        "01_Core/backgrounds/backgrounds-phb24.xml",
        "01_Core/bestiaries/bestiary-dmg24.xml",
        "01_Core/bestiaries/bestiary-phb24.xml",
        "01_Core/bestiaries/bestiary_mm24_a.xml",
        "01_Core/bestiaries/bestiary_mm24_b.xml",
        "01_Core/bestiaries/bestiary_mm24_c.xml",
        "01_Core/bestiaries/bestiary_mm24_d.xml",
        "01_Core/bestiaries/bestiary_mm24_e.xml",
        "01_Core/bestiaries/bestiary_mm24_f.xml",
        "01_Core/bestiaries/bestiary_mm24_g.xml",
        "01_Core/bestiaries/bestiary_mm24_h.xml",
        "01_Core/bestiaries/bestiary_mm24_i.xml",
        "01_Core/bestiaries/bestiary_mm24_j.xml",
        "01_Core/bestiaries/bestiary_mm24_k.xml",
        "01_Core/bestiaries/bestiary_mm24_l.xml",
        "01_Core/bestiaries/bestiary_mm24_m.xml",
        "01_Core/bestiaries/bestiary_mm24_n.xml",
        "01_Core/bestiaries/bestiary_mm24_o.xml",
        "01_Core/bestiaries/bestiary_mm24_p.xml",
        "01_Core/bestiaries/bestiary_mm24_q.xml",
        "01_Core/bestiaries/bestiary_mm24_r.xml",
        "01_Core/bestiaries/bestiary_mm24_s.xml",
        "01_Core/bestiaries/bestiary_mm24_t.xml",
        "01_Core/bestiaries/bestiary_mm24_u.xml",
        "01_Core/bestiaries/bestiary_mm24_v.xml",
        "01_Core/bestiaries/bestiary_mm24_w.xml",
        "01_Core/bestiaries/bestiary_mm24_x.xml",
        "01_Core/bestiaries/bestiary_mm24_y.xml",
        "01_Core/bestiaries/bestiary_mm24_z.xml",
        "01_Core/classes/class-barbarian-phb24.xml",
        "01_Core/classes/class-bard-phb24.xml",
        "01_Core/classes/class-cleric-phb24.xml",
        "01_Core/classes/class-druid-phb24.xml",
        "01_Core/classes/class-fighter-phb24.xml",
        "01_Core/classes/class-monk-phb24.xml",
        "01_Core/classes/class-paladin-phb24.xml",
        "01_Core/classes/class-ranger-phb24.xml",
        "01_Core/classes/class-rogue-phb24.xml",
        "01_Core/classes/class-sorcerer-phb24.xml",
        "01_Core/classes/class-warlock-phb24.xml",
        "01_Core/classes/class-wizard-phb24.xml",
        "01_Core/feats/feats-phb24.xml",
        "01_Core/items/items-dmg24.xml",
        "01_Core/items/items-phb24.xml",
        "01_Core/optionalfeatures/optionalfeatures-phb24.xml",
        "01_Core/races/races-phb24.xml",
        "01_Core/sources/collection-01_core.xml",
        "01_Core/sources/source-dmg24.xml",
        "01_Core/sources/source-mm24.xml",
        "01_Core/sources/source-phb24.xml",
        "01_Core/spells/spells-abjuration-phb24.xml",
        "01_Core/spells/spells-conjuration-phb24.xml",
        "01_Core/spells/spells-divination-phb24.xml",
        "01_Core/spells/spells-enchantment-phb24.xml",
        "01_Core/spells/spells-evocation-phb24.xml",
        "01_Core/spells/spells-illusion-phb24.xml",
        "01_Core/spells/spells-necromancy-phb24.xml",
        "01_Core/spells/spells-transmutation-phb24.xml"
    ]
    process_files(files_to_process)
