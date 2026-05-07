#!/usr/bin/env python3
"""Update one TMDL relationship block in place.

This script is intentionally small and text-based so the result stays Git-friendly.
It can switch a relationship's filtering behavior, active state, or any other
single-property value inside a `relationship` block.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Optional


TOP_LEVEL_PREFIXES = (
    "relationship ",
    "table ",
    "model ",
    "role ",
    "perspective ",
    "cultureInfo ",
    "expression ",
    "function ",
)


def iter_lines_with_newlines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def find_relationship_block(lines: list[str], relationship_name: str) -> tuple[int, int]:
    target_prefixes = (
        f"relationship '{relationship_name}'",
        f'relationship "{relationship_name}"',
        f"relationship {relationship_name}",
    )

    start_index: Optional[int] = None
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(target_prefixes):
            start_index = index
            break

    if start_index is None:
        raise ValueError(f"Relationship not found: {relationship_name}")

    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        stripped = lines[index].lstrip()
        if not stripped.strip():
            continue
        if not lines[index].startswith(("\t", "    ")) and stripped.startswith(TOP_LEVEL_PREFIXES):
            end_index = index
            break

    return start_index, end_index


def property_indent(block_lines: list[str], default_indent: str = "\t") -> str:
    for line in block_lines[1:]:
        if line.startswith(("\t", "    ")) and line.strip():
            indent = line[: len(line) - len(line.lstrip())]
            return indent
    return default_indent


def update_or_insert_property(block_lines: list[str], property_name: str, new_value: str) -> list[str]:
    updated = False
    for index in range(1, len(block_lines)):
        stripped = block_lines[index].lstrip()
        if stripped.startswith(f"{property_name}:"):
            indent = block_lines[index][: len(block_lines[index]) - len(stripped)]
            block_lines[index] = f"{indent}{property_name}: {new_value}\n"
            updated = True
            break

    if not updated:
        indent = property_indent(block_lines)
        insert_at = 1
        while insert_at < len(block_lines):
            stripped = block_lines[insert_at].lstrip()
            if stripped.startswith("///"):
                insert_at += 1
                continue
            if stripped.startswith("relationship "):
                insert_at += 1
                continue
            if stripped.strip():
                break
            insert_at += 1
        block_lines.insert(insert_at, f"{indent}{property_name}: {new_value}\n")

    return block_lines


def replace_block(lines: list[str], start: int, end: int, new_block: Iterable[str]) -> list[str]:
    return lines[:start] + list(new_block) + lines[end:]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update a TMDL relationship block for Git-friendly automation."
    )
    parser.add_argument("file", type=Path, help="Path to the .tmdl file to update")
    parser.add_argument("relationship", help="Relationship name as written in the TMDL file")
    parser.add_argument(
        "--cross-filtering",
        choices=("oneDirection", "bothDirections"),
        help="Set crossFilteringBehavior on the relationship",
    )
    parser.add_argument(
        "--is-active",
        choices=("true", "false"),
        help="Set isActive on the relationship",
    )
    parser.add_argument(
        "--property",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Update or insert an arbitrary property inside the relationship block",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the updated content instead of writing the file",
    )
    return parser.parse_args()


def parse_property_args(entries: list[str]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for entry in entries:
        if "=" not in entry:
            raise ValueError(f"Invalid --property value: {entry}. Expected NAME=VALUE")
        name, value = entry.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name:
            raise ValueError(f"Invalid --property value: {entry}. Property name is empty")
        result.append((name, value))
    return result


def main() -> int:
    args = parse_args()
    text = args.file.read_text(encoding="utf-8")
    lines = iter_lines_with_newlines(text)
    start, end = find_relationship_block(lines, args.relationship)

    block_lines = lines[start:end]
    if args.cross_filtering:
        block_lines = update_or_insert_property(
            block_lines, "crossFilteringBehavior", args.cross_filtering
        )
    if args.is_active:
        block_lines = update_or_insert_property(block_lines, "isActive", args.is_active)

    for property_name, value in parse_property_args(args.property):
        block_lines = update_or_insert_property(block_lines, property_name, value)

    updated_lines = replace_block(lines, start, end, block_lines)
    updated_text = "".join(updated_lines)

    if args.dry_run:
        print(updated_text, end="")
    else:
        args.file.write_text(updated_text, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
