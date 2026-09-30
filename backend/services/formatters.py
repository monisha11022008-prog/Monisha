import html
import re
import textwrap
from io import BytesIO

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from fpdf import FPDF


# =========================================================
# TEXT CLEANING
# =========================================================

def sanitize_text(text: str) -> str:
    if text is None:
        return ""

    text = str(text)

    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
        "\u2022": "-",
        "\ufeff": "",
        "\u200b": "",
        "\u200c": "",
        "\u200d": "",
        "\u2060": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove unsupported control characters.
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    # Normalize spaces while preserving line breaks.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# =========================================================
# DOCX
# =========================================================

def format_docx(
    text: str,
    doc_type: str = "Legal Document",
    terms=None,
    logo_bytes=None,
) -> bytes:

    document = Document()

    section = document.sections[0]

    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    normal_style = document.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(11)

    # -----------------------------------------------------
    # Optional logo
    # -----------------------------------------------------

    if logo_bytes:

        try:
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

            run = paragraph.add_run()

            run.add_picture(
                BytesIO(logo_bytes),
                width=Inches(1.2),
            )

        except Exception:
            pass

    # -----------------------------------------------------
    # Title
    # -----------------------------------------------------

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    title_run = title.add_run(
        f"DRAFT - {doc_type}"
    )

    title_run.bold = True
    title_run.font.size = Pt(16)

    # -----------------------------------------------------
    # Document content
    # -----------------------------------------------------

    clean_text = sanitize_text(text)

    for line in clean_text.splitlines():

        stripped = line.strip()

        if not stripped:
            document.add_paragraph()
            continue

        is_heading = bool(
            re.match(
                r"^\d+[.)]\s+",
                stripped,
            )
        )

        is_uppercase = (
            stripped.isupper()
            and len(stripped) < 100
        )

        # Heading
        if is_heading or is_uppercase:

            paragraph = document.add_paragraph()

            run = paragraph.add_run(stripped)

            run.bold = True
            run.font.size = Pt(12)

        # Bullet
        elif stripped.startswith("- ") or stripped.startswith("* "):

            document.add_paragraph(
                stripped[2:].strip(),
                style="List Bullet",
            )

        # Normal paragraph
        else:

            document.add_paragraph(
                stripped
            )

    # -----------------------------------------------------
    # Terms table
    # -----------------------------------------------------

    if terms:

        parsed_terms = [
            item.strip()
            for item in str(terms).split(";")
            if item.strip()
        ]

        if parsed_terms:

            document.add_page_break()

            heading = document.add_paragraph()

            heading_run = heading.add_run(
                "Terms Table"
            )

            heading_run.bold = True

            table = document.add_table(
                rows=1,
                cols=2,
            )

            table.style = "Table Grid"

            table.rows[0].cells[0].text = "No."
            table.rows[0].cells[1].text = "Term"

            for number, term in enumerate(
                parsed_terms,
                start=1,
            ):

                cells = table.add_row().cells

                cells[0].text = str(number)
                cells[1].text = term

    # -----------------------------------------------------
    # Footer
    # -----------------------------------------------------

    footer = section.footer.paragraphs[0]

    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

    footer.add_run(
        "LegalEase AI - Draft for review"
    )

    # -----------------------------------------------------
    # Return bytes
    # -----------------------------------------------------

    output = BytesIO()

    document.save(output)

    return output.getvalue()


# =========================================================
# PDF CLASS
# =========================================================

class LegalEasePDF(FPDF):

    def __init__(
        self,
        doc_type: str,
        logo_bytes=None,
    ):

        super().__init__(
            orientation="P",
            unit="mm",
            format="A4",
        )

        self.doc_type = sanitize_text(
            doc_type or "Legal Document"
        )

        self.logo_bytes = logo_bytes

        self.set_margins(
            left=18,
            top=20,
            right=18,
        )

        self.set_auto_page_break(
            auto=True,
            margin=18,
        )

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    def header(self):

        self.set_font(
            "Helvetica",
            "B",
            12,
        )

        # Explicit width instead of width=0.
        # This avoids the FPDF horizontal-space error.
        available_width = (
            self.w
            - self.l_margin
            - self.r_margin
        )

        self.set_x(self.l_margin)

        self.cell(
            available_width,
            8,
            f"DRAFT - {self.doc_type}",
            border=0,
            align="C",
        )

        self.ln(10)

    # -----------------------------------------------------
    # Footer
    # -----------------------------------------------------

    def footer(self):

        self.set_y(-15)

        self.set_font(
            "Helvetica",
            "",
            8,
        )

        available_width = (
            self.w
            - self.l_margin
            - self.r_margin
        )

        self.set_x(self.l_margin)

        self.cell(
            available_width,
            8,
            "LegalEase AI - Draft for review",
            border=0,
            align="C",
        )


# =========================================================
# PDF SAFE TEXT WRITER
# =========================================================

def _pdf_write_line(
    pdf: FPDF,
    text: str,
    height: float = 6,
    bold: bool = False,
):
    """
    Safely writes one or more wrapped lines.

    Important:
    - Uses explicit printable width.
    - Resets X position before every line.
    - Never uses multi_cell(width=0).
    - Prevents the FPDF horizontal-space exception.
    """

    if text is None:
        return

    text = sanitize_text(str(text))

    if not text:
        pdf.ln(height)
        return

    if bold:

        pdf.set_font(
            "Helvetica",
            "B",
            11,
        )

    else:

        pdf.set_font(
            "Helvetica",
            "",
            11,
        )

    printable_width = (
        pdf.w
        - pdf.l_margin
        - pdf.r_margin
    )

    # Use a conservative character width.
    chunks = textwrap.wrap(
        text,
        width=85,
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=True,
        drop_whitespace=True,
    )

    if not chunks:
        return

    for chunk in chunks:

        chunk = chunk.strip()

        if not chunk:
            continue

        pdf.set_x(pdf.l_margin)

        pdf.multi_cell(
            w=printable_width,
            h=height,
            text=chunk,
            border=0,
            align="L",
            new_x="LMARGIN",
            new_y="NEXT",
        )


# =========================================================
# PDF
# =========================================================

def format_pdf(
    text: str,
    doc_type: str = "Legal Document",
    logo_bytes=None,
) -> bytes:

    pdf = LegalEasePDF(
        doc_type=doc_type,
        logo_bytes=logo_bytes,
    )

    pdf.add_page()

    clean_text = sanitize_text(text)

    if not clean_text:

        _pdf_write_line(
            pdf,
            "No document content available.",
        )

        return bytes(pdf.output())

    # -----------------------------------------------------
    # Process every line
    # -----------------------------------------------------

    for raw_line in clean_text.splitlines():

        line = raw_line.strip()

        # Empty line
        if not line:

            pdf.ln(4)

            continue

        # -------------------------------------------------
        # Heading
        # -------------------------------------------------

        is_heading = bool(
            re.match(
                r"^\d+[.)]\s+",
                line,
            )
        )

        is_uppercase = (
            line.isupper()
            and len(line) < 100
        )

        if is_heading or is_uppercase:

            _pdf_write_line(
                pdf,
                line,
                height=7,
                bold=True,
            )

            continue

        # -------------------------------------------------
        # Bullet
        # -------------------------------------------------

        if line.startswith("- ") or line.startswith("* "):

            bullet_text = line[2:].strip()

            if bullet_text:

                bullet_lines = textwrap.wrap(
                    bullet_text,
                    width=78,
                    break_long_words=True,
                    break_on_hyphens=False,
                    replace_whitespace=True,
                    drop_whitespace=True,
                )

                for index, bullet_line in enumerate(
                    bullet_lines
                ):

                    if not bullet_line.strip():
                        continue

                    if index == 0:
                        output_line = (
                            "- " + bullet_line
                        )
                    else:
                        output_line = (
                            "  " + bullet_line
                        )

                    _pdf_write_line(
                        pdf,
                        output_line,
                        height=6,
                        bold=False,
                    )

            continue

        # -------------------------------------------------
        # Normal paragraph
        # -------------------------------------------------

        _pdf_write_line(
            pdf,
            line,
            height=6,
            bold=False,
        )

    # -----------------------------------------------------
    # Return PDF bytes
    # -----------------------------------------------------

    return bytes(pdf.output())


# =========================================================
# HTML PREVIEW
# =========================================================

def format_html_preview(
    text: str,
) -> str:

    clean_text = sanitize_text(text)

    escaped = html.escape(
        clean_text
    )

    paragraphs = re.split(
        r"\n\s*\n",
        escaped,
    )

    body_parts = []

    for paragraph in paragraphs:

        if not paragraph.strip():
            continue

        body_parts.append(
            "<p>"
            + paragraph.replace(
                "\n",
                "<br>",
            )
            + "</p>"
        )

    body = "".join(body_parts)

    return f"""
    <div style="
        background:#111827;
        color:#f9fafb;
        padding:24px;
        border-radius:14px;
        border:1px solid #374151;
        max-height:650px;
        overflow-y:auto;
        font-family:Georgia,'Times New Roman',serif;
        line-height:1.65;
        box-sizing:border-box;
    ">
        {body}
    </div>
    """