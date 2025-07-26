import os

def generate_module_map(base_path):
    module_structure = []
    file_found = False

    for root, dirs, files in os.walk(base_path):
        if any(part.startswith('.') or part == '__pycache__' for part in root.split(os.sep)):
            continue

        indent_level = root.replace(base_path, "").count(os.sep)
        indent = "│   " * indent_level + "├── " if indent_level else ""
        module_structure.append(f"{indent}{os.path.basename(root)}/")

        for f in files:
            if f.endswith((".py", ".qss")):
                file_found = True
                sub_indent = "│   " * (indent_level + 1) + "├── "
                module_structure.append(f"{sub_indent}{f}")
    
    if not file_found:
        module_structure.append("\n⚠️ No .py or .qss files found.")
    
    return "\n".join(module_structure)

def save_structure(base_path):
    structure_text = generate_module_map(base_path)
    output_dir = os.path.join(base_path, "..", "structure")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "module_map.txt")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(structure_text)

    return output_file

if __name__ == "__main__":
    print("📁 Tritiq ERP Module Structure Generator")

    default_path = "./src" if os.path.exists("./src") else "."
    print(f"\nDetected project path: {default_path}")

    base_path = input(f"Enter path to ERP root folder [{default_path}]: ").strip()
    base_path = base_path or default_path

    if not os.path.exists(base_path):
        print("❌ Error: Path does not exist.")
    else:
        output_file = save_structure(base_path)
        print(f"\n✅ Structure map saved to:\n{output_file}")
        print("📝 Open module_map.txt in any editor or use it in your Grok prompt.")

    input("\nPress Enter to exit...")
