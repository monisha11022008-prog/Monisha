import sys
from pathlib import Path
from io import BytesIO
from datetime import date

# ---------------------------------------------------------
# Project root
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------
import os

import requests
import streamlit as st
from dotenv import load_dotenv
from docx import Document

from backend.services.formatters import format_pdf


# ---------------------------------------------------------
# Environment
# ---------------------------------------------------------
load_dotenv(PROJECT_ROOT / ".env")

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000"
).rstrip("/")


# ---------------------------------------------------------
# Streamlit configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="LegalEase AI",
    page_icon="⚖️",
    layout="wide",
)


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------
if "document" not in st.session_state:
    st.session_state.document = ""

if "generated" not in st.session_state:
    st.session_state.generated = False

if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False


# ---------------------------------------------------------
# Styling
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        .main-title {
            font-size: 38px;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .subtitle {
            font-size: 18px;
            color: #666666;
            margin-bottom: 25px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.markdown(
    '<div class="main-title">⚖️ LegalEase AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">AI-powered legal document drafting assistant</div>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
with st.sidebar:

    st.header("Document Details")

    document_type = st.text_input(
        "Document Type",
        value="Service Agreement",
        placeholder="Example: Rental Agreement",
    )

    parties = st.text_area(
        "Parties",
        placeholder=(
            "Example:\n"
            "Party 1: ABC Technologies Pvt Ltd\n"
            "Party 2: John Doe"
        ),
        height=130,
    )

    effective_date = st.date_input(
        "Effective Date",
        value=date.today(),
    )

    terms = st.text_area(
        "Terms",
        placeholder=(
            "Enter important terms.\n\n"
            "Example:\n"
            "Payment: Rs. 50,000 per month;\n"
            "Duration: 12 months;\n"
            "Termination notice: 30 days"
        ),
        height=180,
    )

    st.divider()

    generate_button = st.button(
        "Generate Document",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------------------------------
# Generate document
# ---------------------------------------------------------
if generate_button:

    if not document_type.strip():

        st.error("Please enter the document type.")

    elif not parties.strip():

        st.error("Please enter the parties.")

    elif not terms.strip():

        st.error("Please enter the terms.")

    else:

        payload = {
            "document_type": document_type.strip(),
            "parties": parties.strip(),
            "terms": terms.strip(),
            "effective_date": effective_date.isoformat(),
        }

        with st.spinner("Generating document..."):

            try:

                response = requests.post(
                    f"{BACKEND_URL}/generate",
                    json=payload,
                    timeout=120,
                )

                if response.status_code == 200:

                    result = response.json()

                    st.session_state.document = result.get(
                        "document",
                        "",
                    )

                    st.session_state.demo_mode = result.get(
                        "demo_mode",
                        False,
                    )

                    st.session_state.generated = True

                    st.success(
                        "Document generated successfully!"
                    )

                else:

                    try:

                        error_data = response.json()

                        error_message = error_data.get(
                            "detail",
                            "Unknown backend error",
                        )

                    except Exception:

                        error_message = response.text

                    st.error(
                        f"Backend error ({response.status_code}): "
                        f"{error_message}"
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Backend server is not running.\n\n"
                    "Please start FastAPI on port 8000."
                )

            except requests.exceptions.Timeout:

                st.error(
                    "The request timed out. Please try again."
                )

            except Exception as exc:

                st.error(
                    f"Something went wrong: {exc}"
                )


# ---------------------------------------------------------
# DOCX helper
# ---------------------------------------------------------
def create_docx(document_text: str) -> bytes:

    doc = Document()

    title = doc.add_paragraph()

    title.alignment = 1

    run = title.add_run("LegalEase AI")

    run.bold = True

    for line in document_text.splitlines():

        line = line.strip()

        if not line:

            doc.add_paragraph("")

            continue

        if (
            line.isupper()
            or line.startswith("1.")
            or line.startswith("2.")
            or line.startswith("3.")
            or line.startswith("4.")
            or line.startswith("5.")
            or line.startswith("6.")
            or line.startswith("7.")
            or line.startswith("8.")
            or line.startswith("9.")
        ):

            paragraph = doc.add_paragraph()

            run = paragraph.add_run(line)

            run.bold = True

        else:

            doc.add_paragraph(line)

    output = BytesIO()

    doc.save(output)

    return output.getvalue()


# ---------------------------------------------------------
# Generated document
# ---------------------------------------------------------
if st.session_state.generated:

    if st.session_state.demo_mode:

        st.info(
            "Demo mode is active. "
            "The document was generated using the local demo generator."
        )

    else:

        st.success(
            "Gemini AI generation is active."
        )

    st.divider()

    preview_tab, edit_tab, download_tab = st.tabs(
        [
            "Preview",
            "Edit Document",
            "Download",
        ]
    )

    # =====================================================
    # PREVIEW
    # =====================================================

    with preview_tab:

        st.subheader("Document Preview")

        st.text_area(
            "Generated Document",
            value=st.session_state.document,
            height=650,
            disabled=True,
        )

    # =====================================================
    # EDIT
    # =====================================================

    with edit_tab:

        st.subheader("Edit Document")

        edited_document = st.text_area(
            "Modify your document below:",
            value=st.session_state.document,
            height=650,
            key="document_editor",
        )

        if st.button(
            "Save Changes",
            type="primary",
        ):

            st.session_state.document = edited_document

            st.success(
                "Changes saved successfully!"
            )

    # =====================================================
    # DOWNLOAD
    # =====================================================

    with download_tab:

        st.subheader("Download Document")

        document_text = st.session_state.document

        # -------------------------------------------------
        # TXT
        # -------------------------------------------------

        txt_bytes = document_text.encode(
            "utf-8"
        )

        st.download_button(
            label="Download TXT",
            data=txt_bytes,
            file_name="legalease_document.txt",
            mime="text/plain",
            use_container_width=True,
        )

        st.write("")

        # -------------------------------------------------
        # DOCX
        # -------------------------------------------------

        try:

            docx_bytes = create_docx(
                document_text
            )

            st.download_button(
                label="Download DOCX",
                data=docx_bytes,
                file_name="legalease_document.docx",
                mime=(
                    "application/vnd.openxmlformats-"
                    "officedocument.wordprocessingml.document"
                ),
                use_container_width=True,
            )

        except Exception as exc:

            st.error(
                f"DOCX creation failed: {exc}"
            )

        st.write("")

        # -------------------------------------------------
        # PDF
        # -------------------------------------------------

        try:

            pdf_bytes = format_pdf(
                text=document_text,
                doc_type=document_type,
                logo_bytes=None,
            )

            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name="legalease_document.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        except Exception as exc:

            st.error(
                f"PDF creation failed: {exc}"
            )


# ---------------------------------------------------------
# Initial screen
# ---------------------------------------------------------
else:

    st.info(
        "Enter the document details in the sidebar "
        "and click Generate Document."
    )

    st.subheader("Welcome to LegalEase AI")

    st.write(
        "Create a professional legal document draft "
        "using the information you provide."
    )

    st.markdown(
        """
        **How to use**

        1. Select the document type.
        2. Enter the parties.
        3. Select the effective date.
        4. Enter the important terms.
        5. Click **Generate Document**.
        6. Preview or edit the generated document.
        7. Download it as TXT, DOCX, or PDF.
        """
    )

    st.warning(
        "This application creates draft documents for review. "
        "It does not replace advice from a qualified lawyer."
    )