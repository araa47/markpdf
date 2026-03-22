"""CLI entry point for markpdf."""

import asyncio
import sys
import tempfile
from pathlib import Path
from typing import Annotated, Any, Optional

import aiofiles
import aiohttp
import typer

from .parser import BLOCK_IMAGE, parse_markdown
from .renderer import build_story, create_styles, group_sections, render_pdf
from .themes import THEME_DARK, THEME_LIGHT

app = typer.Typer(
    name="markpdf",
    help="Convert markdown to beautiful PDF documents.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


async def fetch_remote_image(url: str, session: aiohttp.ClientSession) -> str | None:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return None
            data = await resp.read()
            suffix = Path(url.split("?")[0]).suffix or ".png"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(data)
            tmp.close()
            return tmp.name
    except Exception:
        return None


async def prefetch_images(
    blocks: list[tuple[str, Any]],
    verbose: bool = False,
) -> dict[str, str | None]:
    remote_urls = [
        content.get("path", "")
        for btype, content in blocks
        if btype == BLOCK_IMAGE
        and content.get("path", "").startswith(("http://", "https://"))
    ]

    if not remote_urls:
        return {}

    if verbose:
        print(f"  Fetching {len(remote_urls)} remote image(s) concurrently...")

    resolved: dict[str, str | None] = {}
    async with aiohttp.ClientSession() as session:
        tasks = {
            url: asyncio.create_task(fetch_remote_image(url, session))
            for url in remote_urls
        }
        for url, task in tasks.items():
            resolved[url] = await task

    fetched = sum(1 for v in resolved.values() if v is not None)
    if verbose:
        print(f"  Fetched {fetched}/{len(remote_urls)} remote images")
    return resolved


async def convert(
    markdown_file: str,
    output_pdf: str | None = None,
    verbose: bool = False,
    dark: bool = False,
    keep_together: bool = False,
) -> str:
    theme = THEME_DARK if dark else THEME_LIGHT
    md_path = Path(markdown_file)

    if not md_path.exists():
        print(f"Error: File not found: {markdown_file}")
        sys.exit(1)

    if output_pdf is None:
        output_pdf = str(md_path.stem) + ".pdf"

    if verbose:
        mode = "dark" if dark else "light"
        print(f"Input:  {markdown_file}")
        print(f"Output: {output_pdf}")
        print(f"Theme:  {mode}")
        if keep_together:
            print("Keep-together: on")

    async with aiofiles.open(markdown_file, "r", encoding="utf-8") as f:
        content = await f.read()

    blocks = parse_markdown(content, verbose)
    if verbose:
        print(f"Parsed {len(blocks)} blocks")

    remote_cache = await prefetch_images(blocks, verbose)
    styles = create_styles(theme)
    story = build_story(blocks, styles, theme, md_path, remote_cache, verbose)

    if keep_together:
        story = group_sections(story)

    try:
        render_pdf(story, output_pdf, theme)
        print(f"PDF created: {output_pdf}")
        return output_pdf
    except Exception as e:
        print(f"Error creating PDF: {e}")
        sys.exit(1)


@app.command()
def main(
    markdown_file: Annotated[
        Path,
        typer.Argument(
            help="Path to the markdown file to convert.",
            exists=True,
            readable=True,
        ),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option(
            "-o",
            "--output",
            help="Output PDF path. Defaults to [bold]<input>.pdf[/bold] in the current directory.",
        ),
    ] = None,
    dark: Annotated[
        bool,
        typer.Option(
            "-d",
            "--dark",
            help="Use [bold]dark mode[/bold] theme (zinc palette on dark background).",
        ),
    ] = False,
    keep_together: Annotated[
        bool,
        typer.Option(
            "-k",
            "--keep-together",
            help="Try to keep each section (heading + content) on the same page.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "-v",
            "--verbose",
            help="Print parsing details and block counts.",
        ),
    ] = False,
) -> None:
    """Convert a markdown file to a beautifully styled PDF.

    Supports headers, bold, italic, code blocks, tables, lists, images,
    blockquotes, task lists, ==highlight==, ^super^, ~sub~, and more.

    \b
    Examples:
      markpdf report.md
      markpdf report.md --dark -o report-dark.pdf
      markpdf README.md --keep-together -v
    """
    try:
        import uvloop

        uvloop.install()
    except ImportError:
        pass

    out = str(output) if output else None
    asyncio.run(
        convert(
            str(markdown_file),
            out,
            verbose,
            dark,
            keep_together,
        )
    )
