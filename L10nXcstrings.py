#!/usr/bin/env python3

import json
import os
import re
import argparse

def get_keys_and_strings_from_xcstrings(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    result = {}
    strings = data.get("strings", {})
    for key, val in strings.items():
        try:
            string_val = val["localizations"]["en"]["stringUnit"]["value"]
            comment = string_val
            if "comment" in val:
                comment = val["comment"]
            
            result[key] = {
                "value": string_val,
                "comment": comment
            }
            

        except KeyError:
            pass
    return result

def extract_placeholder_types(string_value: str) -> list[str]:
    pattern = r'%(\d+\$)?[+\-#0 ]*(?:\d+)?(?:\.\d+)?[hlL]?([@diufFeEgGxXoscp])'
    matches = list(re.finditer(pattern, string_value))

    positionals = {}
    order = []

    def swift_type(spec):
        if spec in {'d', 'i'}:
            return 'Int'
        elif spec in {'u'}:
            return 'UInt'
        elif spec in {'f', 'F', 'e', 'E', 'g', 'G'}:
            return 'Double'
        elif spec in {'@'}:
            return 'String'
        elif spec in {'c'}:
            return 'Character'
        elif spec in {'li', 'ld'}:
            return 'Int64'
        else:
            return 'CVarArg'

    for idx, match in enumerate(matches):
        pos, spec = match.groups()
        typ = swift_type(spec)

        if pos:
            index = int(pos[:-1]) - 1
            positionals[index] = typ
        else:
            order.append(typ)

    if positionals:
        return [positionals[i] for i in sorted(positionals.keys())]
    else:
        return order

def swiftify_key(key: str) -> str:
    return re.sub(r'[._-](\w)', lambda m: m.group(1).upper(), key)

def find_used_keys_in_code(source_dir, keys, enum_name, ignore_dirs):
    used_keys = set()
    for root, dirs, files in os.walk(source_dir):
        # Ignore specified directories
        dirs[:] = [d for d in dirs if not any(os.path.join(root, d).startswith(os.path.join(source_dir, ignore)) for ignore in ignore_dirs)]
        for file in files:
            if file.endswith(".swift"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()

                    for key in keys:
                        pattern = re.compile(rf"\b{enum_name}\.{key}\b")
                        matches = pattern.findall(content)
                        if matches:
                            used_keys.add(key)

    return used_keys

def find_unused_keys(args, swiftified_keys):
    defined_keys = set(swiftified_keys)
    used_keys = find_used_keys_in_code(args.source_dir, defined_keys, args.enum_name, args.ignore_dirs)
    unused = defined_keys - used_keys

    if os.path.exists(args.output_unused):
        os.remove(args.output_unused)

    if unused:
        print("Unused Keys:")
        with open(args.output_unused, "w", encoding="utf-8") as f:
            for key in sorted(unused):
                print(f" - {key}")
                f.write(f"{key}\n")

        print(f"\nTotal: {len(unused)} unused of {len(defined_keys)} keys.")
    return unused

def sanitize_comment(text):
        return ' '.join(text.strip().splitlines())

def generate_strings(args):
    keys_and_strings = get_keys_and_strings_from_xcstrings(args.input)

    sorted_keys = sorted(keys_and_strings.keys())

    # Split keys into categories based on the first part of the key
    split_strings = {}

    for key in sorted_keys:
        parts = key.split(".")
        if len(parts) > 1:
            first_part = parts[0]
            if first_part not in split_strings:
                split_strings[first_part] = []
            newKey = ".".join(parts[1:])

            keyValues = {
                "key": newKey,
                "value": keys_and_strings[key]["value"],
                "comment": keys_and_strings[key]["comment"],
                "original_key": key
            }

            split_strings[first_part].append(keyValues)

        else:
            if "general" not in split_strings:
                split_strings["general"] = []
        
            keyValues = {
                "key": key,
                "value": keys_and_strings[key]["value"],
                "comment": keys_and_strings[key]["comment"],
                "original_key": key
            }
            split_strings["general"].append(keyValues)

    # Sort categories alphabetically
    split_strings = dict(sorted(split_strings.items(), key=lambda x: x[0]))

    # Sort keys within each category
    for category, keys in split_strings.items():
        split_strings[category] = sorted(keys, key=lambda x: x["key"])

    # Generate Swiftified keys to see if they are used in the code
    swiftified_keys = []
    for category, keys in split_strings.items():
        for key in keys:
            index = keys.index(key)
            capitalized_category = category.capitalize()
            swiftified_key = swiftify_key(key["key"])
            swiftified_keys.append(f"{capitalized_category}.{swiftified_key}")
            split_strings[category][index]["unused_key"] = f"{capitalized_category}.{swiftified_key}"


    unused_keys = find_unused_keys(args, swiftified_keys)

    os.makedirs(os.path.dirname(args.output_swift), exist_ok=True)

    # Generate the Swift file
    with open(args.output_swift, "w", encoding="utf-8") as f:
        # Write the header
        f.write("// swiftlint:disable all\n")
        f.write(f"// Generated from {os.path.basename(args.input)}\n")
        f.write(f"// Do not edit manually\n\n")
        f.write("import Foundation\n\n")
        f.write(f"public enum {args.enum_name}: Equatable, Hashable {{\n")

        for category, keys in split_strings.items():
            f.write(f"  // MARK: - {category.capitalize()}\n")

            # Write category enum
            f.write(f" public enum {category.capitalize()} {{\n")

            # Write keys
            for key in keys:
                swift_key = swiftify_key(key["key"])
                string_value = key["value"]
                types = extract_placeholder_types(string_value)
                typesArg = []

                if types and len(types) > 0:
                    types = [typ.capitalize() for typ in types]
                    typesArg = [f"_ p{idx}: {typ}" for idx, typ in enumerate(types)]
                else:
                    types = []
                    typesArg = []

                string_value_with_args = string_value
                for idx, typ in enumerate(types):
                    if typ == "String":
                        string_value_with_args = re.sub(r"%@", f"\(p{idx})", string_value_with_args, count=1)
                    elif typ == "Int":
                        string_value_with_args = re.sub(r"%d", f"\(p{idx})", string_value_with_args, count=1)
                    elif typ == "Double":
                        string_value_with_args = re.sub(r"%f", f"\(p{idx})", string_value_with_args, count=1)
                    elif typ == "Character":
                        string_value_with_args = re.sub(r"%c", f"\(p{idx})", string_value_with_args, count=1)
                    elif typ == "Int64":
                        string_value_with_args = re.sub(r"%li", f"\(p{idx})", string_value_with_args, count=1)
                    elif typ == "UInt":
                        string_value_with_args = re.sub(r"%u", f"\(p{idx})", string_value_with_args, count=1)
                    else:
                        print(f"Unknown type {typ} for key {key}")
                
                comment = f"    /// {sanitize_comment(key['comment'])}"

                if key["unused_key"] in unused_keys:
                    comment = f"    #warning(\"L10n.{key['unused_key']} is unused\")\n" + comment
                f.write(f"{comment}\n")
                if types:
                    f.write(f"    public static func {swift_key}({', '.join(typesArg)}) -> LocalizedStringResource {{\n")
                    f.write(f"      LocalizedStringResource(\n")
                    f.write(f"          \"{key['original_key']}\",\n")
                    f.write(f"          defaultValue: \"{string_value_with_args}\"\n")
                    f.write(f"      )\n")
                    f.write(f"    }}\n")
                elif "\n" in string_value:
                    f.write(f"    public static let {swift_key} = LocalizedStringResource(\n")
                    f.write(f"        \"{key['original_key']}\",\n")
                    f.write(f"        defaultValue: \"\"\"\n{string_value}\n\"\"\"\n")
                    f.write(f"    )\n")
                else:
                    f.write(f"    public static let {swift_key} = LocalizedStringResource(\n")
                    f.write(f"        \"{key['original_key']}\",\n")
                    f.write(f"        defaultValue: \"{string_value}\"\n")
                    f.write(f"    )\n")
                
                if key != keys[-1]:
                    f.write("\n")

            f.write("  }\n\n")
        f.write("}\n\n")

    print(f"Generated {args.output_swift} with {len(sorted_keys)} keys.")

def parse_args():
    parser = argparse.ArgumentParser(description="Generate Swift localization enum and check unused keys.")
    parser.add_argument("--input", default="Localizable.xcstrings", help="Path to .xcstrings file")
    parser.add_argument("--output-swift", default="Generated/Strings+Generated.swift", help="Path to output .swift file")
    parser.add_argument("--output-unused", default="Unused.txt", help="File to write unused keys to")
    parser.add_argument("--source-dir", default=".", help="Directory to scan Swift source code")
    parser.add_argument("--ignore-dirs", nargs="+", default=["Pods", "Carthage", "DerivedData"], help="Directories to ignore during scanning")
    parser.add_argument("--enum-name", default="L10n", help="Name of the generated enum")
    return parser.parse_args()

def main():
    args = parse_args()
    generate_strings(args)

if __name__ == "__main__":
    main()
