#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
Skill Generator Script

A helper script for creating new Claude Code skills with proper structure.
Can be run interactively or with command-line arguments.

Usage:
    uv run create_skill.py --name my-skill --scope personal --interactive
    uv run create_skill.py --name my-skill --scope project --template minimal
    python create_skill.py --name my-skill --scope personal --interactive
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Literal
import yaml


def validate_skill_name(name: str) -> bool:
    """Validate skill name follows conventions."""
    if len(name) > 64:
        print(f"❌ Skill name too long: {len(name)} characters (max 64)")
        return False

    if not name.islower():
        print(f"❌ Skill name must be lowercase: {name}")
        return False

    if " " in name:
        print(f"❌ Skill name cannot contain spaces (use hyphens): {name}")
        return False

    if not all(c.isalnum() or c == "-" for c in name):
        print(f"❌ Skill name can only contain lowercase letters, numbers, and hyphens: {name}")
        return False

    return True


def get_skill_directory(name: str, scope: Literal["personal", "project"]) -> Path:
    """Get the target directory for the skill."""
    if scope == "personal":
        base = Path.home() / ".claude" / "skills"
    else:
        # Find project root (look for .git directory)
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                base = current / ".claude" / "skills"
                break
            current = current.parent
        else:
            # Fallback to current directory
            base = Path.cwd() / ".claude" / "skills"

    return base / name


def create_skill_structure(skill_dir: Path, include_extras: bool = False):
    """Create the directory structure for a skill."""
    skill_dir.mkdir(parents=True, exist_ok=True)

    if include_extras:
        (skill_dir / "templates").mkdir(exist_ok=True)
        (skill_dir / "scripts").mkdir(exist_ok=True)
        (skill_dir / "examples").mkdir(exist_ok=True)
        print(f"✓ Created skill structure with templates, scripts, and examples directories")
    else:
        print(f"✓ Created skill directory")


def generate_skill_md(
    name: str,
    description: str,
    title: str,
    overview: str,
    instructions: str,
    examples: str,
    allowed_tools: str = None,
    template_type: Literal["minimal", "full"] = "minimal"
) -> str:
    """Generate SKILL.md content."""

    # Build YAML frontmatter
    frontmatter = {
        "name": name,
        "description": description
    }

    if allowed_tools:
        frontmatter["allowed-tools"] = allowed_tools

    yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

    # Build markdown content
    content = f"""---
{yaml_str.strip()}
---

# {title}

{overview}

## Instructions

{instructions}

## Examples

{examples}
"""

    if template_type == "full":
        content += """
## Best Practices

1. [Add best practice]
2. [Add best practice]
3. [Add best practice]

## Troubleshooting

**[Common Issue]**
- [Solution]

## When to Use This Skill

Use this skill when:
- [Trigger condition 1]
- [Trigger condition 2]
- [Trigger condition 3]
"""

    return content


def interactive_mode():
    """Run interactive skill creation."""
    print("\n🎨 Skill Builder - Interactive Mode\n")
    print("Let's create a new Claude Code skill together.\n")

    # Gather basic information
    print("📝 Basic Information\n")

    name = input("Skill name (lowercase-with-hyphens): ").strip()
    while not validate_skill_name(name):
        name = input("Skill name (lowercase-with-hyphens): ").strip()

    title = input(f"Skill title (display name) [{name.replace('-', ' ').title()}]: ").strip()
    if not title:
        title = name.replace("-", " ").title()

    print("\n📋 Description (what it does AND when to use it)")
    print("Example: 'Convert PDF files to markdown. Use when working with PDFs or document conversion.'\n")
    description = input("Description: ").strip()
    while len(description) > 1024:
        print(f"❌ Description too long: {len(description)} characters (max 1024)")
        description = input("Description: ").strip()

    print("\n📍 Scope")
    print("  personal - ~/.claude/skills/ (just for you)")
    print("  project  - .claude/skills/ (shared with team via git)")
    scope = input("Scope [personal/project]: ").strip().lower()
    while scope not in ["personal", "project"]:
        scope = input("Scope [personal/project]: ").strip().lower()

    print("\n🎯 Overview")
    overview = input("Brief overview of what this skill does: ").strip()

    print("\n📖 Instructions")
    print("Enter the main instructions (workflow steps). Press Ctrl+D when done:")
    instructions_lines = []
    try:
        while True:
            line = input()
            instructions_lines.append(line)
    except EOFError:
        pass
    instructions = "\n".join(instructions_lines)

    print("\n💡 Examples")
    print("Enter usage examples. Press Ctrl+D when done:")
    examples_lines = []
    try:
        while True:
            line = input()
            examples_lines.append(line)
    except EOFError:
        pass
    examples = "\n".join(examples_lines)

    print("\n🔧 Tool Restrictions (optional)")
    print("Example: Read, Write, Bash, Grep, Glob")
    allowed_tools = input("Allowed tools (leave empty for unrestricted): ").strip()
    if not allowed_tools:
        allowed_tools = None

    print("\n📦 Additional Resources")
    include_extras = input("Include templates/scripts/examples directories? [y/N]: ").strip().lower() == "y"

    template_type = "full" if include_extras else "minimal"

    # Create the skill
    skill_dir = get_skill_directory(name, scope)

    print(f"\n🚀 Creating skill at: {skill_dir}")

    create_skill_structure(skill_dir, include_extras)

    skill_md_content = generate_skill_md(
        name=name,
        description=description,
        title=title,
        overview=overview,
        instructions=instructions,
        examples=examples,
        allowed_tools=allowed_tools,
        template_type=template_type
    )

    skill_md_path = skill_dir / "SKILL.md"
    skill_md_path.write_text(skill_md_content)
    print(f"✓ Created {skill_md_path}")

    # Create README for humans
    readme_content = f"""# {title}

{overview}

## Usage

{instructions}

## Examples

{examples}
"""
    readme_path = skill_dir / "README.md"
    readme_path.write_text(readme_content)
    print(f"✓ Created {readme_path}")

    print(f"\n✅ Skill '{name}' created successfully!")
    print(f"\n📍 Location: {skill_dir}")
    print(f"\n⚠️  Remember to restart Claude Code for changes to take effect")

    if scope == "project":
        print(f"\n💡 Next steps:")
        print(f"   1. Review the generated files")
        print(f"   2. git add .claude/skills/{name}/")
        print(f"   3. git commit -m 'Add {name} skill'")
        print(f"   4. Push to share with team")


def main():
    parser = argparse.ArgumentParser(
        description="Create a new Claude Code skill with proper structure"
    )
    parser.add_argument(
        "--name",
        help="Skill name (lowercase-with-hyphens, max 64 chars)"
    )
    parser.add_argument(
        "--scope",
        choices=["personal", "project"],
        default="personal",
        help="Skill scope: personal (~/.claude/skills) or project (.claude/skills)"
    )
    parser.add_argument(
        "--description",
        help="Skill description (what it does and when to use it, max 1024 chars)"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--template",
        choices=["minimal", "full"],
        default="minimal",
        help="Template type to use"
    )

    args = parser.parse_args()

    if args.interactive or not args.name:
        interactive_mode()
    else:
        # Non-interactive mode
        if not validate_skill_name(args.name):
            sys.exit(1)

        if not args.description:
            print("❌ --description is required in non-interactive mode")
            sys.exit(1)

        skill_dir = get_skill_directory(args.name, args.scope)
        create_skill_structure(skill_dir, args.template == "full")

        title = args.name.replace("-", " ").title()

        skill_md_content = generate_skill_md(
            name=args.name,
            description=args.description,
            title=title,
            overview="[Add overview]",
            instructions="[Add instructions]",
            examples="[Add examples]",
            template_type=args.template
        )

        skill_md_path = skill_dir / "SKILL.md"
        skill_md_path.write_text(skill_md_content)

        print(f"✅ Skill '{args.name}' created at {skill_dir}")
        print("⚠️  Remember to:")
        print("   1. Edit SKILL.md to add instructions and examples")
        print("   2. Restart Claude Code")


if __name__ == "__main__":
    main()
