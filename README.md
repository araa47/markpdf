# markpdf

Beautiful PDFs from markdown. One command, zero config.

```bash
markpdf report.md
```

## Install

Agent skill (Claude Code, Cursor, Codex, Gemini CLI):

```bash
npx skills add araa47/markpdf
```

CLI:

```bash
uv tool install git+https://github.com/araa47/markpdf
```

## Usage

```bash
markpdf report.md                        # creates report.pdf
markpdf report.md --dark                  # dark mode
markpdf report.md -o final.pdf            # custom output path
markpdf report.md -k                      # keep sections on same page
```

## Output

<table>
<tr>
<td><strong>Light</strong></td>
<td><strong>Dark</strong></td>
</tr>
<tr>
<td><img src="examples/showcase-light-p1.png" width="400" /></td>
<td><img src="examples/showcase-dark-p1.png" width="400" /></td>
</tr>
<tr>
<td><img src="examples/showcase-light-p4.png" width="400" /></td>
<td><img src="examples/showcase-dark-p4.png" width="400" /></td>
</tr>
</table>

> Source: [`tests/fixtures/showcase.md`](tests/fixtures/showcase.md) | Full PDFs: [`examples/`](examples/)

## Why markpdf?

Most messaging apps (Slack, Discord, Teams, WhatsApp, email) don't render markdown. `markpdf` turns it into a polished PDF — no browser, no LaTeX, no config.

- Full markdown — headers, lists, tables, code blocks, blockquotes, images, task lists
- Extended syntax — `==highlight==`, `^super^`, `~sub~`, `~~strike~~`
- Light & dark themes — shadcn/ui zinc palette
- Remote images fetched concurrently
- Async I/O with optional uvloop
- Single binary-style command, agent-friendly
