#!/usr/bin/env python3
"""
Analyze WorldManager class structure for decomposition
"""


def analyze_worldmanager():
    html_file = "/Users/dcversus/Documents/GitHub/dcmaidbot/index.html"

    with open(html_file, "r") as f:
        lines = f.readlines()

    # Find WorldManager class start
    class_start = None
    for i, line in enumerate(lines):
        if "class WorldManager {" in line:
            class_start = i
            break

    if not class_start:
        print("WorldManager class not found")
        return

    print(f"WorldManager class starts at line {class_start + 1}")

    # Find class end (next class or closing script tag)
    class_end = None
    for i in range(class_start + 1, len(lines)):
        line = lines[i]

        if "class " in line and not line.strip().startswith("//"):
            class_end = i
            break

        if "<script>" in line or "</script>" in line:
            class_end = i
            break

    if not class_end:
        class_end = len(lines)

    print(f"WorldManager class ends at line {class_end}")
    print(f"Total lines: {class_end - class_start}")

    # Extract methods
    methods = []
    current_method = None
    method_lines = 0

    for i in range(class_start + 1, class_end):
        line = lines[i].strip()

        # Method signature
        if (
            line
            and not line.startswith("//")
            and not line.startswith("}")
            and "(" in line
            and not line.startswith("if")
            and not line.startswith("for")
            and not line.startswith("while")
        ):
            if current_method:
                methods.append((current_method, method_lines))

            # Extract method name
            method_name = line.split("(")[0].strip()
            if " " in method_name:
                method_name = method_name.split()[-1]

            current_method = method_name
            method_lines = 1

        elif current_method and line:
            method_lines += 1

    # Add last method
    if current_method:
        methods.append((current_method, method_lines))

    # Analyze methods
    print(f"\nFound {len(methods)} methods:")
    total_method_lines = 0
    for method_name, lines_count in methods:
        print(f"  {method_name}: {lines_count} lines")
        total_method_lines += lines_count

    print(f"\nTotal method lines: {total_method_lines}")
    print(
        f"Constructor and other lines: {class_end - class_start - total_method_lines}"
    )

    # Suggest extractions
    print("\n=== DECOMPOSITION SUGGESTIONS ===")

    ui_methods = []
    interaction_methods = []
    data_methods = []

    for method_name, lines_count in methods:
        if any(
            keyword in method_name.lower()
            for keyword in ["create", "build", "show", "hide", "render"]
        ):
            ui_methods.append((method_name, lines_count))
        elif any(
            keyword in method_name.lower() for keyword in ["handle", "execute", "setup"]
        ):
            interaction_methods.append((method_name, lines_count))
        elif any(keyword in method_name.lower() for keyword in ["load", "save", "get"]):
            data_methods.append((method_name, lines_count))

    print("\n1. UI Rendering Methods (extract to UIRenderer class):")
    for method_name, lines_count in ui_methods:
        print(f"   - {method_name}: {lines_count} lines")

    print("\n2. Interaction Methods (extract to InteractionHandler class):")
    for method_name, lines_count in interaction_methods:
        print(f"   - {method_name}: {lines_count} lines")

    print("\n3. Data Methods (extract to DataManager class):")
    for method_name, lines_count in data_methods:
        print(f"   - {method_name}: {lines_count} lines")


if __name__ == "__main__":
    analyze_worldmanager()
