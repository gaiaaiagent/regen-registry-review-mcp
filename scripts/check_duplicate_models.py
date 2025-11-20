#!/usr/bin/env python3
"""Detect duplicate Pydantic model definitions across models/ directory.

This script scans all Python files in src/registry_review_mcp/models/ and identifies
any class names that are defined in multiple files, which could lead to import confusion
and maintenance issues.

Usage:
    python scripts/check_duplicate_models.py

Exit codes:
    0: No duplicates found
    1: Duplicates detected (fails CI)
"""

import ast
import sys
from pathlib import Path
from collections import defaultdict


def find_model_classes(file_path: Path) -> list[str]:
    """Extract all class names that inherit from BaseModel.

    Args:
        file_path: Path to Python file to analyze

    Returns:
        List of class names that inherit from BaseModel
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except SyntaxError as e:
        print(f"⚠️  Syntax error in {file_path}: {e}", file=sys.stderr)
        return []

    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if inherits from BaseModel
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "BaseModel":
                    classes.append(node.name)
                    break
                # Handle cases like "base.BaseModel"
                elif isinstance(base, ast.Attribute) and base.attr == "BaseModel":
                    classes.append(node.name)
                    break

    return classes


def check_duplicates() -> int:
    """Scan models/ directory for duplicate class names.

    Returns:
        Exit code: 0 if no duplicates, 1 if duplicates found
    """
    # Get models directory
    script_dir = Path(__file__).parent
    models_dir = script_dir.parent / "src" / "registry_review_mcp" / "models"

    if not models_dir.exists():
        print(f"❌ Models directory not found: {models_dir}", file=sys.stderr)
        return 1

    # Map: class_name -> [file1, file2, ...]
    class_files = defaultdict(list)

    # Scan all Python files except __init__.py
    for file_path in sorted(models_dir.glob("*.py")):
        if file_path.name == "__init__.py":
            continue

        classes = find_model_classes(file_path)
        for cls in classes:
            class_files[cls].append(file_path.name)

    # Report duplicates
    duplicates = {cls: files for cls, files in class_files.items() if len(files) > 1}

    if duplicates:
        print("❌ Duplicate model definitions found:\n", file=sys.stderr)
        for cls, files in sorted(duplicates.items()):
            print(f"   • {cls}:", file=sys.stderr)
            for f in files:
                print(f"      - {f}", file=sys.stderr)
        print(f"\n💡 Fix: Keep one canonical version and remove duplicates", file=sys.stderr)
        print(f"📖 See: CONTRIBUTING.md for model organization guidelines\n", file=sys.stderr)
        return 1
    else:
        # Count total models found
        total_models = sum(len(files) for files in class_files.values())
        total_files = len(list(models_dir.glob("*.py"))) - 1  # Exclude __init__.py

        print(f"✅ No duplicate models found", file=sys.stderr)
        print(f"   Scanned: {total_models} models across {total_files} files", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(check_duplicates())
