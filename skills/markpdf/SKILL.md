---
name: markpdf
description: Convert markdown to beautiful, styled PDFs with light/dark themes. Use when the user needs to send a formatted document in chat, email, or messaging where markdown rendering isn't supported. Converts .md files to .pdf with headers, code blocks, tables, images, and more.
license: MIT
compatibility:
  - Claude Code
  - Cursor
  - Codex
  - Gemini CLI
allowed-tools: Bash(markpdf:*) Read Write
---

# markpdf

Convert markdown files to styled PDFs.

## Setup

```bash
uv tool install git+https://github.com/araa47/markpdf
```

## Usage

```bash
markpdf input.md                   # creates input.pdf
markpdf input.md -o report.pdf     # custom output
markpdf input.md --dark            # dark mode
markpdf input.md -k                # keep sections on same page
```
