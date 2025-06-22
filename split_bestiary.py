import xml.etree.ElementTree as ET
from collections import defaultdict
import os

def split_xml_by_first_letter(xml_file_path, output_dir):
    """
    Splits an XML file containing monster entries into multiple XML files,
    each corresponding to the first letter of the monster's name.

    Args:
        xml_file_path (str): The path to the input XML file.
        output_dir (str): The directory where the split XML files will be saved.
    """
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML file {xml_file_path}: {e}")
        return
    except FileNotFoundError:
        print(f"Error: File not found at {xml_file_path}")
        return

    monsters_by_letter = defaultdict(list)

    for monster_element in root.findall('monster'):
        name_element = monster_element.find('name')
        if name_element is not None and name_element.text:
            name = name_element.text.strip()
            if name:
                first_letter = name[0].lower()
                if 'a' <= first_letter <= 'z':
                    monsters_by_letter[first_letter].append(monster_element)
                else:
                    # Handle names that don't start with a letter (e.g., numbers or symbols)
                    monsters_by_letter['#'].append(monster_element) # Or some other category
            else:
                print(f"Warning: Found a monster entry with no name text: {ET.tostring(monster_element, encoding='unicode')}")
                monsters_by_letter['#'].append(monster_element) # Or handle as an error
        else:
            print(f"Warning: Found a monster entry with no name element: {ET.tostring(monster_element, encoding='unicode')}")
            monsters_by_letter['#'].append(monster_element) # Or handle as an error


    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    compendium_root_tag_open = '<compendium version="5" auto_indent="NO">\n'
    compendium_root_tag_close = '</compendium>'

    for letter, monsters in monsters_by_letter.items():
        if not monsters:
            continue

        new_xml_file_name = f"bestiary_mm24_{letter}.xml"
        new_xml_file_path = os.path.join(output_dir, new_xml_file_name)

        with open(new_xml_file_path, 'w', encoding='utf-8') as f:
            f.write(xml_declaration)
            f.write(compendium_root_tag_open)
            for monster_element in monsters:
                # ET.tostring returns bytes, so decode to string
                monster_xml_str = ET.tostring(monster_element, encoding='unicode')
                f.write(monster_xml_str + '\n')
            f.write(compendium_root_tag_close)
        print(f"Created {new_xml_file_path} with {len(monsters)} monster(s).")

if __name__ == '__main__':
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the full path to the XML file relative to the script directory
    # This assumes bestiary_mm24.xml is in 01_Core/03_Monster_Manual_2024/ relative to the script's parent directory
    # Adjust the relative path as necessary if the script is located elsewhere
    relative_xml_path = '01_Core/03_Monster_Manual_2024/bestiary_mm24.xml'
    xml_file_to_split = os.path.join(script_dir, relative_xml_path)

    # Define the output directory, also relative to the script's location
    # This will place the new files in 01_Core/03_Monster_Manual_2024/
    output_directory = os.path.join(script_dir, '01_Core/03_Monster_Manual_2024/')

    # Ensure the input XML file exists before proceeding
    if not os.path.exists(xml_file_to_split):
        print(f"Input XML file not found: {xml_file_to_split}")
        print("Please ensure the path is correct and the file exists.")
    else:
        split_xml_by_first_letter(xml_file_to_split, output_directory)
        print(f"Splitting complete. Files are in {output_directory}")
