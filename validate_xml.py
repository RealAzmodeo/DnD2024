from lxml import etree
import sys

def validate_xml_file(filepath):
    try:
        parser = etree.XMLParser(dtd_validation=False, no_network=True) # Turning off DTD validation for now
        etree.parse(filepath, parser)
        print(f"Validation successful for {filepath}")
        return True
    except etree.XMLSyntaxError as e:
        print(f"Validation failed for {filepath}:")
        print(e)
        return False
    except Exception as e:
        print(f"An unexpected error occurred while validating {filepath}:")
        print(e)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_xml.py <file1.xml> [file2.xml ...]")
        sys.exit(1)

    all_valid = True
    for filepath in sys.argv[1:]:
        if not validate_xml_file(filepath):
            all_valid = False

    if not all_valid:
        sys.exit(1)
