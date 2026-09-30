from .formatters import (
    format_docx,
    format_pdf,
)


def build_txt(text: str) -> bytes:
    return text.encode("utf-8")


def build_docx(
    text: str,
    doc_type: str,
    terms: str,
    logo_bytes=None,
) -> bytes:
    return format_docx(
        text=text,
        doc_type=doc_type,
        terms=terms,
        logo_bytes=logo_bytes,
    )


def build_pdf(
    text: str,
    doc_type: str,
    logo_bytes=None,
) -> bytes:
    return format_pdf(
        text=text,
        doc_type=doc_type,
        logo_bytes=logo_bytes,
    )