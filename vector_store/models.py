from pydantic import BaseModel, model_validator
from typing import Optional


class Document(BaseModel):
    """Class for storing a piece of text and associated metadata."""

    page_content: str
    metadata: Optional[dict] = None

