import xml.etree.ElementTree as ET
from collections import defaultdict
import os
import json

import re

def parse_glossary_file(glossary_filepath):
    """Parses the glossary file to extract all defined XML tags."""
    tags = set()
    try:
        with open(glossary_filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to find <tag_name ...> or <tag_name> or </tag_name>
        # This will capture root tags and sub-tags mentioned in the glossary
        # It's a simplified approach; a more robust parser might be needed for complex glossary structures
        # but for extracting tag names, this should be a good start.
        # It specifically looks for tags starting with < followed by a letter,
        # and captures the tag name itself.
        found_tags = re.findall(r"<([a-zA-Z][a-zA-Z0-9_:]*)\s*[^>]*?>", content)
        tags.update(found_tags)

        # Also capture closing tags to ensure we get all unique names
        closing_tags = re.findall(r"</([a-zA-Z][a-zA-Z0-9_:]*)>", content)
        tags.update(closing_tags)

    except FileNotFoundError:
        print(f"Glossary file not found: {glossary_filepath}")
    return tags

def main():
    core_data_dir = "01_Core"
    glossary_file = "glossary_xml_tags_v1.txt"

    GLOSSARY_TAGS = parse_glossary_file(glossary_file)
    if not GLOSSARY_TAGS:
        print("Error: Glossary tags could not be loaded. Exiting.")
        return

    all_project_xml_files = get_all_xml_files(core_data_dir)

    discrepancies = defaultdict(list)
    all_found_tags = set()

    print(f"Found {len(all_project_xml_files)} XML files to analyze.")

    all_found_tags, discrepancies = analyze_files_for_tags(all_project_xml_files, GLOSSARY_TAGS)

    output = {
        "glossary_tags_count": len(GLOSSARY_TAGS),
        "all_found_tags_in_project_count": len(all_found_tags),
        "discrepancies_found": bool(discrepancies),
        "discrepant_tags": [],
        "tags_in_glossary_not_found_in_project": sorted(list(GLOSSARY_TAGS - all_found_tags))
    }

    if discrepancies:
        print("\nDiscrepancies found (tags in project files NOT in glossary):")
        for tag, files in sorted(discrepancies.items()):
            output["discrepant_tags"].append({
                "tag": tag,
                "count": len(files),
                "files": files[:20] # Limit to first 20 files for brevity in output
            })
            # print(f"  Tag '{tag}' found in {len(files)} files (examples: {files[:3]})")
    else:
        print("\nNo discrepancies found. All tags in project files are in the glossary.")

    # print("\nTags in glossary but NOT found in any analyzed project files:")
    # for tag in output["tags_in_glossary_not_found_in_project"]:
    #     print(f"  '{tag}'")

    with open("tag_analysis_report.json", "w", encoding='utf-8') as f:
        json.dump(output, f, indent=4)

    print("\nAnalysis complete. Report saved to tag_analysis_report.json")

def analyze_files_for_tags(xml_files, glossary_tags_set):
    """Analyzes XML files to find unique tags and discrepancies against a glossary set."""
    discrepancies = defaultdict(list)
    all_found_tags = set()
    for xml_file in xml_files:
        # print(f"Analyzing: {xml_file}")
        tags_in_file = get_unique_tags_in_file(xml_file)
        all_found_tags.update(tags_in_file)
        for tag in tags_in_file:
            if tag not in glossary_tags_set:
                discrepancies[tag].append(xml_file)
    return all_found_tags, discrepancies

def get_all_xml_files(root_dir):
    """Finds all .xml files in the given directory and its subdirectories."""
    xml_files = []
    for dirpath, _, filenames in os.walk(root_dir): # Corrected variable name here
        for filename in filenames:
            if filename.endswith('.xml'):
                # Exclude source definition files from direct tag analysis for now
                if not filename.startswith('source-') and not filename.startswith('collection-'):
                    xml_files.append(os.path.join(dirpath, filename)) # Corrected variable name here
    return xml_files

def get_unique_tags_in_file(filepath):
    """Extracts all unique tags from a single XML file."""
    tags = set()
    try:
        tree = ET.parse(filepath)
        for element in tree.iter():
            tags.add(element.tag)
    except ET.ParseError as e:
        print(f"Could not parse {filepath}: {e}")
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    return tags

# Removed the duplicated/older main() function that was here.

if __name__ == "__main__":
    main() # This will now call the correct main() defined earlier.
