import xml.etree.ElementTree as ET
import re

def format_xml(element):
    """Return a pretty-printed XML string for the Element."""
    # This is a simple version. For more complex pretty printing, lxml might be better.
    from xml.dom import minidom
    rough_string = ET.tostring(element, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def parse_races(input_filepath, output_filepath):
    """
    Parses the races XML file according to the glossary and writes a new XML file.
    """
    try:
        input_tree = ET.parse(input_filepath)
        input_root = input_tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML file {input_filepath}: {e}")
        return
    except FileNotFoundError:
        print(f"Error: Input file not found {input_filepath}")
        return

    output_root = ET.Element(input_root.tag)
    if input_root.get('version'):
        output_root.set('version', input_root.get('version'))
    if input_root.get('auto_indent'):
        output_root.set('auto_indent', input_root.get('auto_indent'))

    for input_race_element in input_root.findall('race'):
        output_race_element = ET.SubElement(output_root, 'race')

        # Helper function to directly copy simple elements if they exist
        def copy_simple_element(parent_in, parent_out, tag_name):
            element = parent_in.find(tag_name)
            if element is not None:
                new_element = ET.SubElement(parent_out, tag_name, element.attrib)
                new_element.text = element.text
                # Also copy any children of this simple element (e.g. <source> might have attributes on main tag and text)
                for sub_element in element: # This is not standard for truly 'simple' tags but good for <source>
                    new_sub_element = ET.SubElement(new_element, sub_element.tag, sub_element.attrib)
                    new_sub_element.text = sub_element.text


        # Parse and add top-level elements according to glossary
        # <name>
        copy_simple_element(input_race_element, output_race_element, 'name')

        # <source page="[numero]">[NombreLibroFuente]</source>
        source_element = input_race_element.find('source')
        if source_element is not None:
            # The source tag in races-phb24.xml has page as an attribute and text for the book name.
            # This matches the glossary: <source page="[numero]">[NombreLibroFuente]</source>
            new_source = ET.SubElement(output_race_element, 'source', source_element.attrib)
            new_source.text = source_element.text

        # <size_summary code="[S|M|L|T|G|H]"/>
        size_summary_element = input_race_element.find('size_summary')
        if size_summary_element is not None:
            ET.SubElement(output_race_element, 'size_summary', size_summary_element.attrib)
            # size_summary should be an empty tag with attributes only, text is not expected.

        # <speed base="[numero_pies]"/>
        speed_element = input_race_element.find('speed')
        if speed_element is not None:
            ET.SubElement(output_race_element, 'speed', speed_element.attrib)
            # speed should be an empty tag with attributes only.

        # <spellcasting_ability default="[AbilityName]" allow_choice="[true|false]"/> (Optional)
        spellcasting_ability_element = input_race_element.find('spellcasting_ability')
        if spellcasting_ability_element is not None:
            ET.SubElement(output_race_element, 'spellcasting_ability', spellcasting_ability_element.attrib)
            # This should also be an empty tag with attributes.

        # Placeholder for <description_text> if it were a direct child,
        # but in races-phb24.xml it's usually a <trait category="description">
        # copy_simple_element(input_race_element, output_race_element, 'description_text')


        # Implement parsing for <trait> elements
        for input_trait_element in input_race_element.findall('trait'):
            output_trait_element = ET.SubElement(output_race_element, 'trait', input_trait_element.attrib)

            # Define a recursive function to copy/transform elements based on glossary
            # This function will be expanded as we identify specific transformations needed
            def process_element(input_el, output_el_parent):
                # Create the new element in the output tree
                # Attributes are copied directly. The glossary doesn't ask to change attributes of existing tags,
                # but rather ensure the correct tags and structures are used.
                output_el = ET.SubElement(output_el_parent, input_el.tag, input_el.attrib)
                output_el.text = input_el.text
                output_el.tail = input_el.tail # Preserve tail text for mixed content

                # Recursively process children
                for child_input_el in input_el:
                    process_element(child_input_el, output_el)

            # Process each child of the current input_trait_element
            for child_input_el in input_trait_element:
                # Here, we could add specific logic if child_input_el.tag needs transformation
                # based on the glossary. For example, if an <effect_old_format> needed to become <effect type="...">.
                # For now, we assume `races-phb24.xml` is already *using* the correct tag names like <effect>, <choice>,
                # and the main task is to ensure their structure and attributes are preserved and correctly nested.
                # The glossary is more about *which* tags to use and *how* they should be structured, rather than
                # wholesale renaming of tags that are already close to the target.

                # Example: If glossary required a specific attribute to be present on an <effect> tag,
                # we could check and add it here.
                # if child_input_el.tag == 'effect':
                #     if 'type' not in child_input_el.attrib:
                #         # This would be a case for error or applying a default based on glossary
                #         pass

                process_element(child_input_el, output_trait_element)


    # Write the output XML file
    try:
        # Using ElementTree.write for basic output, then pretty-printing
        # ET.indent(output_root) # Available in Python 3.9+ for pretty printing
        # tree = ET.ElementTree(output_root)
        # tree.write(output_filepath, encoding='utf-8', xml_declaration=True)

        # Using custom formatter for pretty print
        pretty_xml_string = format_xml(output_root)
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(pretty_xml_string)
        print(f"Successfully parsed races to {output_filepath}")
    except IOError as e:
        print(f"Error writing XML file {output_filepath}: {e}")


if __name__ == "__main__":
    # Path to the input races XML file
    input_races_file = "01_Core/01_Players_Handbook_2024/races-phb24.xml"
    # Path for the output (parsed) XML file
    output_races_file = "races-phb24-parsed.xml"

    parse_races(input_races_file, output_races_file)
