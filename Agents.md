# markpdf

Markdown to PDF converter. `uv tool install git+https://github.com/araa47/markpdf`

## Dev

```bash
uv sync --all-extras --dev
uv run pytest
uv run markpdf input.md
```

## Layout

- `src/markpdf/cli.py` — typer CLI
- `src/markpdf/parser.py` — markdown tokenizer
- `src/markpdf/renderer.py` — reportlab PDF builder
- `src/markpdf/themes.py` — light/dark tokens
- `skills/markpdf/SKILL.md` — agent skill
