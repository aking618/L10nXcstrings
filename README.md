# 🔤 Localization Keys Generator & Cleaner for iOS (SwiftGen-style)

This script (`L10nXcstrings.py`) automates the management of iOS localization strings using the new `Localizable.xcstrings` format. It helps you:

* ✅ Generate a Swift enum (`L10n`) with categorized static properties or methods
* ✅ Annotate unused keys with `#warning(...)` at compile-time
* ✅ Export a list of unused localization keys to `Unused.txt`
* ✅ Safely handle format placeholders (`%@`, `%d`, etc.)

> 📦 Fork maintained by [@aking618](https://github.com/aking618)

---

## 🛠 Features

* **Supports `.xcstrings`**: Parses Xcode's new JSON-based localization format.
* **CamelCase key formatting**: Converts `login.title_screen` → `L10n.Login.titleScreen`.
* **Safe enum generation**: Outputs a clean, categorized `Strings+Generated.swift` with `LocalizedStringResource` properties and methods.
* **Placeholder support**: Detects `%@`, `%d`, etc., and generates typed Swift functions.
* **Usage analysis**: Scans your Swift codebase for usage of `L10n.<category>.<key>`.
* **Unused key detection**: Marks unused keys with `#warning(...)` and writes to `Unused.txt`.
* **Category grouping**: Automatically organizes strings into nested enums based on dot-prefixes.

---

## 📦 File Structure Sample

```
SRC/
├── Resources/
│   ├── Localizable.xcstrings
│   └── Generated/
│       └── Strings+Generated.swift   ← ✅ Auto-generated
└── Unused.txt                        ← 📄 List of unused keys (if any)
```

---

## 🚀 Usage

0. **Install the script via Homebrew**
   (Original repo tap)

   ```bash
   brew tap disconnecter/l10n https://github.com/Disconnecter/homebrew-l10n
   brew install l10n-xcstrings
   ```

1. **Place your `.xcstrings` file** in the expected path (e.g., `Resources/Localizable.xcstrings`)

2. **Run the script**:

   ```bash
   python3 L10nXcstrings.py
   ```

3. **Or run with custom arguments**:

   ```bash
   python3 L10nXcstrings.py \
     --input Resources/Localizable.xcstrings \
     --output-swift Resources/Generated/Strings+Generated.swift \
     --output-unused Unused.txt \
     --source-dir ./MyApp \
     --ignore-dirs Pods Carthage \
     --enum-name L10n
   ```

4. **🎉 You’ll get:**

* `Strings+Generated.swift` (clean, categorized output)
* `Unused.txt` (if unused keys found)
* Terminal output showing unused count and warnings

---

## 🧪 Requirements

* Python 3.6+
* Xcode `.xcstrings` file (JSON format)
* Swift codebase using `L10n.<category>.<key>` access style

---

## 📝 Notes

* Keys like `k-about.welcome_screen` become `L10.K-about.welcomeScreen`
* Strings are grouped into nested enums using their key prefix (`login.title` → `Login.title`)
* Keys with format specifiers like `%@`, `%d` generate Swift functions with typed arguments
* Unused keys are flagged in code like:

```swift
#warning("L10n.Login.loginTitle is unused")
/// Login screen title
public static let loginTitle = LocalizedStringResource(
    "login.title",
    defaultValue: "Welcome!"
)
```

---

## 🎮 Parameters

| Argument          | Description                       | Default                               |
| ----------------- | --------------------------------- | ------------------------------------- |
| `--input`         | Path to `.xcstrings` file         | `Localizable.xcstrings`               |
| `--output-swift`  | Output `.swift` file path         | `Generated/Strings+Generated.swift`   |
| `--output-unused` | Output path for unused keys       | `Unused.txt`                          |
| `--source-dir`    | Swift source directory to scan    | `.` (current directory)               |
| `--ignore-dirs`   | Folders to ignore during scanning | `["Pods", "Carthage", "DerivedData"]` |
| `--enum-name`     | Name of the top-level enum        | `L10n`                                |

---

## ✅ TODO (Completed)

* ✅ Format string placeholder typing
* ✅ Homebrew installation support

---

## 📄 License

MIT — free to use, modify, and contribute.

---

🙌 Contributions

Open issues or PRs welcome! Feature ideas include:

* Folder filtering for `.xcstrings` parsing
* `.localized()` usage detection
* Optional SwiftPM plugin support (blocked by SPM sandboxing)
* Tests and formatter integrations

---

Let me know if you'd like a badge, example screenshot, or install instructions customized for your personal fork.
