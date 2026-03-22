"""Tests for markpdf. Each fixture markdown is converted and validated."""

import shutil
import subprocess
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
ALL_FIXTURES = sorted(FIXTURES_DIR.glob("*.md"))
FIXTURE_IDS = [f.stem for f in ALL_FIXTURES]

MARKPDF = shutil.which("markpdf")


@pytest.fixture(autouse=True)
def _require_markpdf():
    if not MARKPDF:
        pytest.skip("markpdf CLI not found in PATH")


def run_markpdf(
    md_path: Path, output_path: Path, verbose: bool = False, dark: bool = False
) -> subprocess.CompletedProcess:
    assert MARKPDF is not None
    cmd = [MARKPDF, str(md_path), "-o", str(output_path)]
    if verbose:
        cmd.append("-v")
    if dark:
        cmd.append("--dark")
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


@pytest.mark.parametrize("md_file", ALL_FIXTURES, ids=FIXTURE_IDS)
def test_fixture_produces_pdf(md_file: Path, tmp_path: Path):
    output = tmp_path / f"{md_file.stem}.pdf"
    result = run_markpdf(md_file, output, verbose=True)
    assert (
        result.returncode == 0
    ), f"Failed for {md_file.name}:\n{result.stderr}\n{result.stdout}"
    assert output.exists(), f"PDF not created for {md_file.name}"
    assert output.stat().st_size > 0, f"PDF is empty for {md_file.name}"
    assert output.read_bytes()[:5] == b"%PDF-", f"Not a valid PDF for {md_file.name}"


@pytest.mark.parametrize("md_file", ALL_FIXTURES, ids=FIXTURE_IDS)
def test_fixture_dark_mode(md_file: Path, tmp_path: Path):
    output = tmp_path / f"{md_file.stem}-dark.pdf"
    result = run_markpdf(md_file, output, dark=True)
    assert (
        result.returncode == 0
    ), f"Dark mode failed for {md_file.name}:\n{result.stderr}"
    assert output.exists()
    assert output.read_bytes()[:5] == b"%PDF-"


def test_default_output_name(tmp_path: Path):
    assert MARKPDF is not None
    md = FIXTURES_DIR / "headers.md"
    result = subprocess.run(
        [MARKPDF, str(md)],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0
    assert (tmp_path / "headers.pdf").exists()


def test_verbose_output(tmp_path: Path):
    output = tmp_path / "verbose.pdf"
    result = run_markpdf(FIXTURES_DIR / "headers.md", output, verbose=True)
    assert result.returncode == 0
    assert "Parsed" in result.stdout or "[H" in result.stdout


def test_missing_file(tmp_path: Path):
    result = run_markpdf(Path("/nonexistent/file.md"), tmp_path / "nope.pdf")
    assert result.returncode != 0


def test_image_rendering(tmp_path: Path):
    output = tmp_path / "images.pdf"
    result = run_markpdf(FIXTURES_DIR / "images.md", output, verbose=True)
    assert result.returncode == 0
    assert output.stat().st_size > 500


def test_empty_file(tmp_path: Path):
    output = tmp_path / "empty.pdf"
    result = run_markpdf(FIXTURES_DIR / "empty.md", output)
    assert result.returncode == 0
    assert output.exists()


def test_heading_orphan_prevention():
    """Headings should be wrapped with CondPageBreak and KeepTogether to avoid orphans."""
    from reportlab.platypus import CondPageBreak, KeepTogether

    from markpdf.parser import parse_markdown
    from markpdf.renderer import build_story, create_styles
    from markpdf.themes import THEME_LIGHT

    md = "# Title\n\nSome text.\n\n## Section\n\nMore text.\n\n### Subsection\n\nDetails."
    blocks = parse_markdown(md)
    styles = create_styles(THEME_LIGHT)
    story = build_story(blocks, styles, THEME_LIGHT, Path("."), {})

    cond_breaks = [f for f in story if isinstance(f, CondPageBreak)]
    keep_togethers = [f for f in story if isinstance(f, KeepTogether)]

    # 3 headings -> 3 CondPageBreak + 3 KeepTogether (one per heading block)
    assert len(cond_breaks) == 3, f"Expected 3 CondPageBreak, got {len(cond_breaks)}"
    assert (
        len(keep_togethers) >= 3
    ), f"Expected >=3 KeepTogether, got {len(keep_togethers)}"


def test_heading_keepwithnext_style():
    """All heading styles should have keepWithNext=True."""
    from markpdf.renderer import create_styles
    from markpdf.themes import THEME_LIGHT

    styles = create_styles(THEME_LIGHT)
    for level in range(1, 7):
        style = styles[f"Heading{level}Custom"]
        assert style.keepWithNext is True, f"Heading{level}Custom missing keepWithNext"


def test_heading_orphan_long_document(tmp_path: Path):
    """A long document with many sections should produce a valid PDF with orphan prevention."""
    # Generate a markdown document with many sections to force page breaks
    sections = []
    for i in range(20):
        sections.append(f"## Section {i + 1}")
        sections.append("")
        # Add enough content per section to push headings near page boundaries
        for j in range(8):
            sections.append(f"This is paragraph {j + 1} of section {i + 1}. " * 4)
            sections.append("")
    md_content = "\n".join(sections)

    md_file = tmp_path / "long_headings.md"
    md_file.write_text(md_content)
    output = tmp_path / "long_headings.pdf"
    result = run_markpdf(md_file, output)
    assert result.returncode == 0
    assert output.exists()
    assert output.stat().st_size > 1000
