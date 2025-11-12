#!/usr/bin/env python3
"""
Template Validation Script

Validates that all Python templates and examples have correct syntax.
Run this before distributing the skill to ensure all files are valid.

Usage:
    python validate-templates.py
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


def validate_python_file(file_path: Path) -> Tuple[bool, str]:
    """Validate Python file syntax.

    Args:
        file_path: Path to Python file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        content = file_path.read_text()
        ast.parse(content)
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in directory.

    Args:
        directory: Directory to search

    Returns:
        List of Python file paths
    """
    return sorted(directory.rglob("*.py"))


def main():
    """Run validation on all templates and examples."""
    print("MCP Architect Skill - Template Validation")
    print("=" * 60)

    # Get skill directory
    skill_dir = Path(__file__).parent.parent
    print(f"Skill directory: {skill_dir}\n")

    # Find Python files
    templates_dir = skill_dir / "templates"
    examples_dir = skill_dir / "examples"

    template_files = find_python_files(templates_dir)
    example_files = find_python_files(examples_dir)

    all_files = template_files + example_files

    if not all_files:
        print("❌ No Python files found!")
        sys.exit(1)

    print(f"Found {len(all_files)} Python files to validate:\n")

    # Validate each file
    results = []
    for file_path in all_files:
        rel_path = file_path.relative_to(skill_dir)
        print(f"Validating: {rel_path}")

        is_valid, error_msg = validate_python_file(file_path)
        results.append((rel_path, is_valid, error_msg))

        if is_valid:
            print(f"  ✅ Valid\n")
        else:
            print(f"  ❌ Invalid: {error_msg}\n")

    # Summary
    print("=" * 60)
    print("SUMMARY\n")

    valid_count = sum(1 for _, is_valid, _ in results if is_valid)
    total_count = len(results)

    print(f"Valid:   {valid_count}/{total_count}")
    print(f"Invalid: {total_count - valid_count}/{total_count}")

    # Details of failures
    failures = [(path, msg) for path, is_valid, msg in results if not is_valid]
    if failures:
        print("\nFAILURES:\n")
        for path, msg in failures:
            print(f"  ❌ {path}")
            print(f"     {msg}\n")

    # Exit code
    if valid_count == total_count:
        print("\n🎉 All templates validated successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ {len(failures)} file(s) failed validation")
        sys.exit(1)


if __name__ == "__main__":
    main()
