"""Markdown parser - tokenizes markdown into typed blocks."""

import re
from typing import Any

BLOCK_H1 = "h1"
BLOCK_H2 = "h2"
BLOCK_H3 = "h3"
BLOCK_H4 = "h4"
BLOCK_H5 = "h5"
BLOCK_H6 = "h6"
BLOCK_PARA = "para"
BLOCK_CODE = "code"
BLOCK_TABLE = "table"
BLOCK_HR = "hr"
BLOCK_BULLET_LIST = "bullet_list"
BLOCK_NUMBER_LIST = "number_list"
BLOCK_QUOTE = "quote"
BLOCK_IMAGE = "image"

HEADER_BLOCKS = [BLOCK_H1, BLOCK_H2, BLOCK_H3, BLOCK_H4, BLOCK_H5, BLOCK_H6]


def skip_frontmatter(content: str) -> str:
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            return content[end + 3 :].lstrip("\n")
    return content


def parse_table(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    headers: list[str] = []
    rows: list[list[str]] = []
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if i == 0:
            headers = cells
        elif i == 1:
            continue
        else:
            rows.append(cells)
    return headers, rows


def parse_markdown(content: str, verbose: bool = False) -> list[tuple[str, Any]]:
    content = skip_frontmatter(content)
    lines = content.split("\n")
    blocks: list[tuple[str, Any]] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            if 1 <= level <= 6 and (len(stripped) == level or stripped[level] == " "):
                header_text = stripped[level:].strip()
                block_type = HEADER_BLOCKS[level - 1]
                blocks.append((block_type, header_text))
                if verbose:
                    print(f"  [H{level}] {header_text[:60]}")
                i += 1
                continue

        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            blocks.append((BLOCK_HR, None))
            i += 1
            continue

        if stripped.startswith("```"):
            code_lines: list[str] = []
            lang = stripped[3:].strip()
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append((BLOCK_CODE, {"lang": lang, "code": "\n".join(code_lines)}))
            if verbose:
                print(f"  [Code] {len(code_lines)} lines ({lang or 'plain'})")
            i += 1
            continue

        if "|" in stripped and stripped.startswith("|"):
            table_lines = [line]
            i += 1
            while i < len(lines) and "|" in lines[i].strip() and lines[i].strip():
                table_lines.append(lines[i])
                i += 1
            if len(table_lines) >= 2:
                headers, rows = parse_table(table_lines)
                blocks.append((BLOCK_TABLE, {"headers": headers, "rows": rows}))
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append((BLOCK_QUOTE, "\n".join(quote_lines)))
            continue

        if re.match(r"^[-*+]\s", stripped):
            list_items: list[str] = []
            while i < len(lines):
                item_line = lines[i].strip()
                if re.match(r"^[-*+]\s", item_line):
                    task_match = re.match(r"^[-*+]\s+\[([ xX])\]\s*(.*)$", item_line)
                    if task_match:
                        checked = task_match.group(1).lower() == "x"
                        prefix = "\u2611 " if checked else "\u2610 "
                        list_items.append(prefix + task_match.group(2))
                    else:
                        list_items.append(item_line[2:].strip())
                    i += 1
                elif (
                    item_line
                    and not re.match(r"^\d+\.\s", item_line)
                    and not item_line.startswith("#")
                ):
                    if list_items:
                        list_items[-1] += " " + item_line
                    i += 1
                else:
                    break
            blocks.append((BLOCK_BULLET_LIST, list_items))
            continue

        if re.match(r"^\d+\.\s", stripped):
            list_items = []
            while i < len(lines):
                item_line = lines[i].strip()
                if re.match(r"^\d+\.\s", item_line):
                    list_items.append(re.sub(r"^\d+\.\s*", "", item_line))
                    i += 1
                elif (
                    item_line
                    and not re.match(r"^[-*+]\s", item_line)
                    and not item_line.startswith("#")
                ):
                    if list_items:
                        list_items[-1] += " " + item_line
                    i += 1
                else:
                    break
            blocks.append((BLOCK_NUMBER_LIST, list_items))
            continue

        image_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if image_match:
            blocks.append(
                (
                    BLOCK_IMAGE,
                    {
                        "alt": image_match.group(1),
                        "path": image_match.group(2),
                    },
                )
            )
            i += 1
            continue

        para_lines: list[str] = []
        while i < len(lines):
            cs = lines[i].strip()
            if (
                not cs
                or cs.startswith("#")
                or cs.startswith("```")
                or cs.startswith(">")
            ):
                break
            if re.match(r"^(-{3,}|\*{3,}|_{3,})$", cs):
                break
            if "|" in cs and cs.startswith("|"):
                break
            if re.match(r"^[-*+]\s", cs) or re.match(r"^\d+\.\s", cs):
                break
            img_inline = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", cs)
            if img_inline:
                if para_lines:
                    blocks.append((BLOCK_PARA, " ".join(para_lines)))
                    para_lines = []
                blocks.append(
                    (
                        BLOCK_IMAGE,
                        {
                            "alt": img_inline.group(1),
                            "path": img_inline.group(2),
                        },
                    )
                )
                i += 1
                continue
            para_lines.append(cs)
            i += 1
        if para_lines:
            blocks.append((BLOCK_PARA, " ".join(para_lines)))

    return blocks
