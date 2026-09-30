import os

from pydantic import BaseModel, Field, field_validator


MAX_INPUT_CHARS = int(
    os.getenv("MAX_INPUT_CHARS", "20000")
)


class DocumentRequest(BaseModel):
    document_type: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    parties: str = Field(
        ...,
        min_length=2,
        max_length=MAX_INPUT_CHARS,
    )

    terms: str = Field(
        ...,
        min_length=2,
        max_length=MAX_INPUT_CHARS,
    )

    effective_date: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    @field_validator(
        "document_type",
        "parties",
        "terms",
        "effective_date",
    )
    @classmethod
    def clean_value(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Value cannot be empty."
            )

        return value


class GenerateResponse(BaseModel):
    document: str
    demo_mode: bool = False