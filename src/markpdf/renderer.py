"""PDF renderer - builds reportlab flowables from parsed blocks."""

import re
from pathlib import Path
from typing import Any

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    CondPageBreak,
    HRFlowable,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .parser import (
    BLOCK_BULLET_LIST,
    BLOCK_CODE,
    BLOCK_H1,
    BLOCK_H2,
    BLOCK_H3,
    BLOCK_H4,
    BLOCK_H5,
    BLOCK_H6,
    BLOCK_HR,
    BLOCK_IMAGE,
    BLOCK_NUMBER_LIST,
    BLOCK_PARA,
    BLOCK_QUOTE,
    BLOCK_TABLE,
)

HEADING_DEFS = [
    {"size": 30, "tk": "h1", "sb": 20, "sa": 6, "ld": 36},
    {"size": 22, "tk": "h2", "sb": 24, "sa": 4, "ld": 28},
    {"size": 17, "tk": "h3", "sb": 18, "sa": 4, "ld": 23},
    {"size": 14, "tk": "h4", "sb": 14, "sa": 4, "ld": 19},
    {"size": 12, "tk": "h5", "sb": 12, "sa": 2, "ld": 17},
    {"size": 11, "tk": "h6", "sb": 10, "sa": 2, "ld": 16},
]


def sanitize_text(text: str) -> str:
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    for old, new in {
        "\u2013": "-",
        "\u2014": "--",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00a0": " ",
    }.items():
        text = text.replace(old, new)
    return text


def process_inline_formatting(text: str, theme: dict[str, str | None]) -> str:
    text = sanitize_text(text)

    text = re.sub(
        r"`([^`]+)`",
        rf'<font face="Courier" size="9" backColor="{theme["code_inline_bg"]}" color="{theme["code_inline_text"]}"> \1 </font>',
        text,
    )
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)
    text = re.sub(r"___(.+?)___", r"<b><i>\1</i></b>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    text = re.sub(
        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text
    )
    text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"<i>\1</i>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        rf'<link href="\2"><u><font color="{theme["link"]}">\1</font></u></link>',
        text,
    )
    text = re.sub(r"~~(.+?)~~", r"<strike>\1</strike>", text)
    text = re.sub(
        r"==(.+?)==",
        rf'<font backColor="{theme["highlight_bg"]}">&nbsp;\1&nbsp;</font>',
        text,
    )
    text = re.sub(r"\^(.+?)\^", r"<super>\1</super>", text)
    text = re.sub(r"~(?!~)(.+?)~(?!~)", r"<sub>\1</sub>", text)
    return text


def create_styles(theme: dict[str, str | None]) -> dict:
    styles = getSampleStyleSheet()

    for i, hd in enumerate(HEADING_DEFS, 1):
        styles.add(
            ParagraphStyle(
                name=f"Heading{i}Custom",
                parent=styles["Heading1"],
                fontSize=hd["size"],
                textColor=colors.HexColor(theme[hd["tk"]]),
                spaceAfter=hd["sa"],
                spaceBefore=hd["sb"],
                leading=hd["ld"],
                fontName="Helvetica-Bold",
                keepWithNext=True,
            )
        )

    styles["Normal"].fontSize = 10.5
    styles["Normal"].leading = 17
    styles["Normal"].textColor = colors.HexColor(theme["body"])
    styles["Normal"].spaceAfter = 6

    styles.add(
        ParagraphStyle(
            name="CodeBlock",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=8.5,
            leading=13,
            textColor=colors.HexColor(theme["code_text"]),
            backColor=colors.HexColor(theme["code_bg"]),
            borderPadding=(10, 12, 10, 12),
            leftIndent=0,
            rightIndent=0,
            spaceBefore=4,
            spaceAfter=4,
            borderColor=colors.HexColor(theme["code_border"]),
            borderWidth=0.5,
            borderRadius=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeLang",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7,
            textColor=colors.HexColor(theme["muted_foreground"]),
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BlockQuote",
            parent=styles["Normal"],
            fontSize=10.5,
            leading=17,
            textColor=colors.HexColor(theme["quote_text"]),
            leftIndent=20,
            borderPadding=(8, 10, 8, 10),
            spaceBefore=8,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ListItem",
            parent=styles["Normal"],
            fontSize=10.5,
            leading=17,
            leftIndent=20,
            spaceBefore=2,
            spaceAfter=2,
            textColor=colors.HexColor(theme["body"]),
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["Normal"],
            fontSize=9,
            leading=14,
            alignment=TA_LEFT,
            textColor=colors.HexColor(theme["card_foreground"]),
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["Normal"],
            fontSize=9,
            leading=14,
            fontName="Helvetica-Bold",
            alignment=TA_LEFT,
            textColor=colors.HexColor(theme["table_header_text"]),
        )
    )
    styles.add(
        ParagraphStyle(
            name="ImageCaption",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor(theme["muted_foreground"]),
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=10,
        )
    )
    return styles


def resolve_image(
    img_src: str,
    md_path: Path,
    remote_cache: dict[str, str | None],
) -> str | None:
    if img_src.startswith(("http://", "https://")):
        return remote_cache.get(img_src)
    full = md_path.parent / img_src
    if full.exists():
        return str(full)
    if Path(img_src).exists():
        return str(Path(img_src))
    return None


def load_image_flowable(
    path: str, max_w: float, max_h: float
) -> Image | None:
    try:
        pil = PILImage.open(path)
        iw, ih = pil.size
        aspect = ih / float(iw)
        dw = min(iw, max_w)
        dh = dw * aspect
        if dh > max_h:
            dh = max_h
            dw = dh / aspect
        img = Image(path)
        img.drawWidth = dw
        img.drawHeight = dh
        img.hAlign = "CENTER"
        return img
    except Exception:
        return None


def _add_page_number(canvas, doc, theme: dict[str, str | None]):
    n = canvas.getPageNumber()
    canvas.saveState()
    if theme["page_bg"]:
        canvas.setFillColor(colors.HexColor(theme["page_bg"]))
        canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor(theme["border"]))
    canvas.setLineWidth(0.5)
    canvas.line(
        doc.leftMargin,
        0.6 * inch,
        letter[0] - doc.rightMargin,
        0.6 * inch,
    )
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor(theme["muted_foreground"]))
    canvas.drawCentredString(letter[0] / 2, 0.4 * inch, str(n))
    canvas.restoreState()


def _fmt(text: str, theme: dict[str, str | None]) -> str:
    return process_inline_formatting(text, theme)


def build_story(
    blocks: list[tuple[str, Any]],
    styles: dict,
    theme: dict[str, str | None],
    md_path: Path,
    remote_cache: dict[str, str | None],
    verbose: bool = False,
) -> list:
    story: list = []
    avail_w = letter[0] - 1.5 * inch
    avail_h = letter[1] - 2.5 * inch

    for btype, content in blocks:
        try:
            if btype in (
                BLOCK_H1,
                BLOCK_H2,
                BLOCK_H3,
                BLOCK_H4,
                BLOCK_H5,
                BLOCK_H6,
            ):
                level = int(btype[1])
                text = _fmt(content, theme)
                # Avoid orphaned headings: break page if insufficient space
                story.append(CondPageBreak(1.2 * inch))
                heading_para = Paragraph(
                    text, styles[f"Heading{level}Custom"]
                )
                if level == 2:
                    story.append(
                        KeepTogether(
                            [
                                heading_para,
                                Spacer(1, 2),
                                HRFlowable(
                                    width="100%",
                                    thickness=0.5,
                                    color=colors.HexColor(
                                        theme["border"]
                                    ),
                                    spaceBefore=0,
                                    spaceAfter=8,
                                ),
                            ]
                        )
                    )
                else:
                    story.append(
                        KeepTogether([heading_para, Spacer(1, 4)])
                    )

            elif btype == BLOCK_PARA:
                story.append(
                    Paragraph(_fmt(content, theme), styles["Normal"])
                )
                story.append(Spacer(1, 4))

            elif btype == BLOCK_CODE:
                lang = content.get("lang", "")
                code = sanitize_text(content.get("code", ""))
                code = (
                    code.replace("\n", "<br/>")
                    .replace("  ", "&nbsp;&nbsp;")
                    .replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
                )
                if lang:
                    story.append(
                        Paragraph(
                            f'<font face="Helvetica" size="7" color="{theme["muted_foreground"]}">{lang}</font>',
                            styles["CodeLang"],
                        )
                    )
                    story.append(Spacer(1, 2))
                story.append(
                    Paragraph(
                        f'<font face="Courier" size="8.5">{code}</font>',
                        styles["CodeBlock"],
                    )
                )
                story.append(Spacer(1, 8))

            elif btype == BLOCK_TABLE:
                headers = content.get("headers", [])
                rows = content.get("rows", [])
                h_p = [
                    Paragraph(_fmt(h, theme), styles["TableHeader"])
                    for h in headers
                ]
                r_p = [
                    [
                        Paragraph(_fmt(c, theme), styles["TableCell"])
                        for c in r
                    ]
                    for r in rows
                ]
                nc = len(headers)
                cw = (letter[0] - 1.5 * inch) / nc
                row_bg = colors.HexColor(theme["background"] or "#ffffff")
                alt_bg = colors.HexColor(theme["table_alt_row"])
                t = Table([h_p] + r_p, colWidths=[cw] * nc)
                t.setStyle(
                    TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (-1, 0),
                                colors.HexColor(theme["table_header_bg"]),
                            ),
                            (
                                "TEXTCOLOR",
                                (0, 0),
                                (-1, 0),
                                colors.HexColor(theme["table_header_text"]),
                            ),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                            ("TOPPADDING", (0, 0), (-1, 0), 8),
                            ("BACKGROUND", (0, 1), (-1, -1), row_bg),
                            (
                                "ROWBACKGROUNDS",
                                (0, 1),
                                (-1, -1),
                                [row_bg, alt_bg],
                            ),
                            (
                                "LINEBELOW",
                                (0, 0),
                                (-1, -1),
                                0.5,
                                colors.HexColor(theme["table_border"]),
                            ),
                            ("LEFTPADDING", (0, 0), (-1, -1), 10),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                            ("TOPPADDING", (0, 1), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    )
                )
                story.append(t)
                story.append(Spacer(1, 12))

            elif btype == BLOCK_HR:
                story.append(Spacer(1, 6))
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.5,
                        color=colors.HexColor(theme["hr"]),
                        spaceBefore=2,
                        spaceAfter=2,
                    )
                )
                story.append(Spacer(1, 6))

            elif btype == BLOCK_BULLET_LIST:
                items = [
                    ListItem(
                        Paragraph(_fmt(t, theme), styles["ListItem"])
                    )
                    for t in content
                ]
                story.append(
                    ListFlowable(
                        items,
                        bulletType="bullet",
                        start=None,
                        bulletFontSize=5,
                        bulletColor=colors.HexColor(theme["bullet_color"]),
                        leftIndent=18,
                        spaceBefore=4,
                        spaceAfter=4,
                    )
                )
                story.append(Spacer(1, 4))

            elif btype == BLOCK_NUMBER_LIST:
                items = [
                    ListItem(
                        Paragraph(_fmt(t, theme), styles["ListItem"])
                    )
                    for t in content
                ]
                story.append(
                    ListFlowable(
                        items,
                        bulletType="1",
                        bulletFontSize=10,
                        bulletColor=colors.HexColor(
                            theme["muted_foreground"]
                        ),
                        leftIndent=18,
                        spaceBefore=4,
                        spaceAfter=4,
                    )
                )
                story.append(Spacer(1, 4))

            elif btype == BLOCK_QUOTE:
                formatted = _fmt(content, theme)
                para = Paragraph(
                    f"<i>{formatted}</i>", styles["BlockQuote"]
                )
                tbl = Table(
                    [["", para]], colWidths=[3, None], hAlign="LEFT"
                )
                tbl.setStyle(
                    TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (0, 0),
                                colors.HexColor(theme["quote_border"]),
                            ),
                            (
                                "BACKGROUND",
                                (1, 0),
                                (1, 0),
                                colors.HexColor(theme["quote_bg"]),
                            ),
                            ("LEFTPADDING", (0, 0), (0, 0), 0),
                            ("RIGHTPADDING", (0, 0), (0, 0), 0),
                            ("LEFTPADDING", (1, 0), (1, 0), 14),
                            ("TOPPADDING", (0, 0), (-1, -1), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ]
                    )
                )
                story.append(Spacer(1, 4))
                story.append(tbl)
                story.append(Spacer(1, 8))

            elif btype == BLOCK_IMAGE:
                src = content.get("path", "")
                alt = content.get("alt", "")
                resolved = resolve_image(src, md_path, remote_cache)
                if resolved:
                    flowable = load_image_flowable(
                        resolved, avail_w, avail_h
                    )
                    if flowable:
                        elems: list = [flowable]
                        if alt:
                            elems.append(
                                Paragraph(
                                    f"<i>{sanitize_text(alt)}</i>",
                                    styles["ImageCaption"],
                                )
                            )
                        story.append(KeepTogether(elems))
                        story.append(Spacer(1, 12))
                    elif verbose:
                        print(f"  Warning: Could not render image {src}")
                else:
                    if verbose:
                        print(f"  Warning: Image not found: {src}")
                    story.append(
                        Paragraph(
                            f'<font color="{theme["muted_foreground"]}">[Image: {sanitize_text(src)}]</font>',
                            styles["Normal"],
                        )
                    )

        except Exception as e:
            if verbose:
                print(f"  Warning: Failed to render {btype}: {e}")
            continue

    return story


def group_sections(story: list) -> list:
    """Wrap each section (heading + following content until next heading) in KeepTogether.

    Falls back gracefully: if a section is too tall for a page, reportlab
    will break it across pages automatically.
    """
    from reportlab.platypus import Paragraph as _Para

    grouped: list = []
    current_section: list = []

    def _is_heading(flowable) -> bool:
        if not isinstance(flowable, _Para):
            return False
        style_name = getattr(flowable, "style", None)
        if style_name is None:
            return False
        return getattr(style_name, "name", "").startswith("Heading")

    for item in story:
        if _is_heading(item) and current_section:
            grouped.append(KeepTogether(current_section))
            current_section = []
        current_section.append(item)

    if current_section:
        grouped.append(KeepTogether(current_section))

    return grouped


def render_pdf(
    story: list,
    output_pdf: str,
    theme: dict[str, str | None],
) -> str:
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.85 * inch,
    )

    def on_page(canvas, doc_inner):
        _add_page_number(canvas, doc_inner, theme)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return output_pdf
