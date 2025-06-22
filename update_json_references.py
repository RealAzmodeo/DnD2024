import json
import os

def get_first_letter_of_name(monster_name):
    """Get the first letter of the monster name, or '#' if not a letter."""
    if monster_name and isinstance(monster_name, str):
        first_char = monster_name.strip()[0].lower()
        if 'a' <= first_char <= 'z':
            return first_char
    return '#'

def update_json_source_files(json_file_path, original_source_name, new_source_prefix, output_dir_for_new_files):
    """
    Updates the 'source_file' field in a JSON file for monster entries.

    Args:
        json_file_path (str): Path to the JSON file to update.
        original_source_name (str): The original 'source_file' value to replace
                                   (e.g., "01_Core/03_Monster_Manual_2024/bestiary_mm24.xml").
        new_source_prefix (str): The prefix for the new source files
                                (e.g., "bestiary_mm24_").
        output_dir_for_new_files (str): The directory where the new XML files are located
                                     (e.g., "01_Core/03_Monster_Manual_2024/").
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_file_path}")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {json_file_path}: {e}")
        return

    if not isinstance(data, list):
        print("Error: JSON data is not a list of monsters.")
        return

    updated_count = 0
    for monster in data:
        if isinstance(monster, dict) and monster.get('source_file') == original_source_name:
            name = monster.get('name')
            if name:
                first_letter = get_first_letter_of_name(name)
                new_filename = f"{new_source_prefix}{first_letter}.xml"
                monster['source_file'] = os.path.join(output_dir_for_new_files, new_filename)
                updated_count += 1
            else:
                print(f"Warning: Monster entry without a name found, original source: {monster.get('source_file')}")


    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Updated {updated_count} entries in {json_file_path}.")

if __name__ == '__main__':
    json_file = 'bestiario_estructurado.json'
    original_source = '01_Core/03_Monster_Manual_2024/bestiary_mm24.xml'
    new_prefix = 'bestiary_mm24_'
    output_dir = '01_Core/03_Monster_Manual_2024/' # Ensure this ends with a slash if os.path.join is used this way

    update_json_source_files(json_file, original_source, new_prefix, output_dir)
