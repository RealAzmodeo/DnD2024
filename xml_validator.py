import xml.etree.ElementTree as ET
import sys

def validate_xml_files(filepaths):
    results = {}
    for filepath in filepaths:
        try:
            ET.parse(filepath)
            results[filepath] = "Valid XML"
        except ET.ParseError as e:
            results[filepath] = f"Invalid XML: {e}"
        except FileNotFoundError:
            results[filepath] = "File not found"
        except Exception as e:
            results[filepath] = f"An unexpected error occurred: {e}"
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python xml_validator.py <file1.xml> <file2.xml> ...")
        sys.exit(1)

    files_to_validate = sys.argv[1:]
    validation_results = validate_xml_files(files_to_validate)

    for file, result in validation_results.items():
        print(f"{file}: {result}")

    all_valid = all(res == "Valid XML" for res in validation_results.values())
    sys.exit(0 if all_valid else 1)
