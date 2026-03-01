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
    assert result.returncode == 0, f"Failed for {md_file.name}:\n{result.stderr}\n{result.stdout}"
    assert output.exists(), f"PDF not created for {md_file.name}"
    assert output.stat().st_size > 0, f"PDF is empty for {md_file.name}"
    assert output.read_bytes()[:5] == b"%PDF-", f"Not a valid PDF for {md_file.name}"


@pytest.mark.parametrize("md_file", ALL_FIXTURES, ids=FIXTURE_IDS)
def test_fixture_dark_mode(md_file: Path, tmp_path: Path):
    output = tmp_path / f"{md_file.stem}-dark.pdf"
    result = run_markpdf(md_file, output, dark=True)
    assert result.returncode == 0, f"Dark mode failed for {md_file.name}:\n{result.stderr}"
    assert output.exists()
    assert output.read_bytes()[:5] == b"%PDF-"


def test_default_output_name(tmp_path: Path):
    md = FIXTURES_DIR / "headers.md"
    result = subprocess.run(
        [MARKPDF, str(md)],
        capture_output=True, text=True, timeout=30, cwd=str(tmp_path),
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
