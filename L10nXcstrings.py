#!/usr/bin/env python3

import json
import os
import re
import argparse

def get_keys_from_xcstrings(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return set(data.get("strings", {}).keys())

def find_used_keys_in_code(source_dir, keys, enum_name):
    used_keys = set()
    pattern = re.compile(rf'\b{re.escape(enum_name)}\.([a-zA-Z0-9_]+)\b')

    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".swift"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    used_keys.update(matches)

    return used_keys

def find_unused_keys(args):
    defined_keys = get_keys_from_xcstrings(args.input)
    used_keys = find_used_keys_in_code(args.source_dir, defined_keys, args.enum_name)

    unused_keys = defined_keys - used_keys
    if os.path.exists(args.output_unused):
        os.remove(args.output_unused)

    if unused_keys:
        print("Unused Keys:")
        with open(args.output_unused, "w", encoding="utf-8") as f:
            for key in sorted(unused_keys):
                print(f" - {key}")
                f.write(f"{key}\n")

        print(f"\nTotal: {len(unused_keys)} unused of {len(defined_keys)} keys.")

    return unused_keys

def swiftify_key(key: str) -> str:
    return re.sub(r'[._-](\w)', lambda match: match.group(1).upper(), key)

def generate_strings(args):
    strings_dict = get_keys_from_xcstrings(args.input)
    keys = sorted(strings_dict)
    unused_keys = find_unused_keys(args)

    with open(args.output_swift, "w", encoding="utf-8") as f:
        f.write(f"//swiftlint:disable all\n\n")
        f.write(f"// Generated from {os.path.basename(args.input)}\n")
        f.write(f"// Do not edit manually\n\n")
        f.write(f"// Run in terminal for regenerating \"python3 strings.py\"\n\n")
        f.write(f"import Foundation\n\n")
        f.write(f"enum {args.enum_name}: String {{\n")
        for key in keys:
            swift_key = swiftify_key(key)
            if swift_key in unused_keys:
                f.write(f'    case {swift_key} = "{key}" //TODO: Unused\n')
            else:
                f.write(f'    case {swift_key} = "{key}"\n')
        f.write("}\n\n")

        f.write(f"extension {args.enum_name} {{\n")
        f.write(f"    func localize(_ args: CVarArg...) -> String {{\n")
        f.write(f"        let localizedString = NSLocalizedString(self.rawValue, comment: self.rawValue)\n")
        f.write(f"        return String(format: localizedString, arguments: args)\n")
        f.write(f"    }}\n")
        f.write(f"}}\n")

    print(f"Generated {args.output_swift} with {len(keys)} keys.")

def parse_args():
    parser = argparse.ArgumentParser(description="Generate Swift localization enum and check unused keys.")
    parser.add_argument("--input", default="Localizable.xcstrings", help="Path to .xcstrings file")
    parser.add_argument("--output-swift", default="Generated/Strings+Generated.swift", help="Path to output .swift file")
    parser.add_argument("--output-unused", default="Unused.txt", help="File to write unused keys to")
    parser.add_argument("--source-dir", default=".", help="Directory to scan Swift source code")
    parser.add_argument("--enum-name", default="L10n", help="Name of the generated enum")
    return parser.parse_args()

def main():
    args = parse_args()
    generate_strings(args)

if __name__ == "__main__":
    main()
