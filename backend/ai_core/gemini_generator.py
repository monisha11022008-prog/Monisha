import os

from dotenv import load_dotenv


load_dotenv()


class GeminiDocumentGenerator:
    def __init__(self):
        self.api_key = os.getenv(
            "GEMINI_API_KEY",
            "",
        ).strip()

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )

        self.demo_mode = os.getenv(
            "DEMO_MODE",
            "true",
        ).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    def _build_prompt(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
    ) -> str:

        return f"""
You are LegalEase AI, an assistant for drafting
legal-document templates.

Create a professional editable draft.

Document type:
{document_type}

Parties:
{parties}

Effective date:
{effective_date}

Terms:
{terms}

Rules:

1. Use only facts supplied by the user.
2. Never invent names, addresses, amounts, dates,
   obligations, or other facts.
3. Use a clear document title.
4. Use numbered sections.
5. Include relevant provisions based on the supplied
   information.
6. If information is missing, use a clear placeholder.
7. Use plain but professional legal language.
8. Mark the document as DRAFT FOR REVIEW.
9. Do not claim that the document is legally valid.
10. Do not claim that it is suitable for a particular
    jurisdiction.
11. Return only the document text.
12. Do not use Markdown code fences.
13. Include signature blocks where appropriate.
""".strip()

    def _demo_document(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
    ) -> str:

        term_lines = []

        for term in terms.split(";"):
            term = term.strip()

            if term:
                term_lines.append(
                    f"- {term}"
                )

        terms_text = "\n".join(term_lines)

        if not terms_text:
            terms_text = "- [Terms to be specified]"

        return f"""DRAFT FOR REVIEW

{document_type.upper()}

Effective Date: {effective_date}

PARTIES

{parties}

1. PURPOSE

This draft sets out the principal terms for the
{document_type} described by the parties above.

2. AGREED TERMS

{terms_text}

3. ADDITIONAL PROVISIONS

The parties should complete any provisions required
for the intended transaction, including governing law,
dispute resolution, notices, confidentiality, term,
termination, representations, and other
jurisdiction-specific requirements.

4. REVIEW

This is an AI-generated draft prepared from the
information supplied by the user.

It should be reviewed and revised as appropriate
before signature or use.

SIGNATURES

Party 1:

Signature: ______________________________

Name: __________________________________

Date: ___________________________________


Party 2:

Signature: ______________________________

Name: __________________________________

Date: ___________________________________
"""

    def generate_document(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
    ):

        if not self.api_key:

            if self.demo_mode:
                return (
                    self._demo_document(
                        document_type,
                        parties,
                        terms,
                        effective_date,
                    ),
                    True,
                )

            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Add it to .env or enable DEMO_MODE."
            )

        try:
            from google import genai

        except ImportError as exc:

            raise RuntimeError(
                "google-genai is not installed. "
                "Run: pip install -r requirements.txt"
            ) from exc

        try:
            client = genai.Client(
                api_key=self.api_key
            )

            response = client.models.generate_content(
                model=self.model,
                contents=self._build_prompt(
                    document_type,
                    parties,
                    terms,
                    effective_date,
                ),
            )

        except Exception as exc:

            raise RuntimeError(
                f"Gemini generation failed: {exc}"
            ) from exc

        generated_text = getattr(
            response,
            "text",
            None,
        )

        if not generated_text:

            raise RuntimeError(
                "Gemini returned an empty response."
            )

        generated_text = generated_text.strip()

        if not generated_text:

            raise RuntimeError(
                "Gemini returned an empty document."
            )

        return generated_text, False