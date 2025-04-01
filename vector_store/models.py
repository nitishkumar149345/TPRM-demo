from pydantic import BaseModel, model_validator
from typing import Optional


class Document(BaseModel):
    """Class for storing a piece of text and associated metadata."""

    page_content: str
    metadata: Optional[dict] = None



class MilvusConfig(BaseModel):
    """
    configuration class for Milvus connection
    """

    uri: str # Milvus server uri
    token: Optional[str] = None # Optional token for aithentication
    user: Optional[str]
    password: Optional[str]
    
    @model_validator(mode="before")
    @classmethod
    def validate_config(cls, values:dict) -> dict:
        """
        Validate the configuration values.
        Raises ValueError if required fields are missing.
        """
        if not values.get("uri"):
            raise ValueError("config MILVUS_URI is required")
        

    def to_milvus_params(self,):
        """
        convert the cinfiguration to dictionary of Milvus connection parameters"""
        return {
            "uri":self.uri
        }