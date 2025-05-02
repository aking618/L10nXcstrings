import json
import os
import re

XCSTRINGS_PATH = "Localizable.xcstrings"
OUTPUT_SWIFT = "Strings+Generated.swift"
OUTPUT_UNUSED = "Unused.txt"
SOURCE_DIR = "ProjectDir"
ENUM_NAME = "L10n"

def get_keys_from_xcstrings(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return set(data.get("strings", {}).keys())

def find_used_keys_in_code(source_dir, keys):
    used_keys = set()
    pattern = re.compile(rf'\b{re.escape(ENUM_NAME)}\.([a-zA-Z0-9_]+)\b')

    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".swift"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    used_keys.update(matches)

    return used_keys

def find_unused_keys():
    defined_keys = get_keys_from_xcstrings(XCSTRINGS_PATH)
    used_keys = find_used_keys_in_code(SOURCE_DIR, defined_keys)
    unused_keys = defined_keys - used_keys
    if os.path.exists(OUTPUT_UNUSED):
      os.remove(OUTPUT_UNUSED)

    if unused_keys:
        print("Unused Keys:")
        with open(OUTPUT_UNUSED, "w", encoding="utf-8") as f:
            for key in sorted(unused_keys):
                print(f" - {key}")
                f.write(f"{key}\n")

        print(f"\nTotal: {len(unused_keys)} unused of {len(defined_keys)} keys.")

    return unused_keys

def swiftify_key(key: str) -> str:
    return re.sub(r'[._-](\w)', lambda match: match.group(1).upper(), key)

def generate_strings():
    strings_dict = get_keys_from_xcstrings(XCSTRINGS_PATH)

    keys = sorted(strings_dict)
    unused_keys = find_unused_keys()

    with open(OUTPUT_SWIFT, "w", encoding="utf-8") as f:
        f.write(f"//swiftlint:disable all\n\n")
        f.write(f"// Generated from {os.path.basename(XCSTRINGS_PATH)}\n")
        f.write(f"// Do not edit manually\n\n")
        f.write(f"// Run in terminal for regenerating \"python3 strings.py\"\n\n")
        f.write(f"import Foundation\n\n")
        f.write(f"enum {ENUM_NAME}: String {{\n")
        for key in keys:
            swift_key = swiftify_key(key)
            if swift_key in unused_keys:
                f.write(f'    case {swift_key} = "{key}" //TODO: Unused\n')
            else:
                f.write(f'    case {swift_key} = "{key}"\n')
        f.write("}\n\n")

        f.write(f"extension {ENUM_NAME} {{\n")
        f.write(f"    func localize(_ args: CVarArg...) -> String {{\n")
        f.write(f"        let localizedString = NSLocalizedString(self.rawValue, comment: self.rawValue)\n")
        f.write(f"        return String(format: localizedString, arguments: args)\n")
        f.write(f"    }}\n")
        f.write(f"}}\n")

    print(f"Generated {OUTPUT_SWIFT} with {len(keys)} keys.")

if __name__ == "__main__":
    generate_strings()
