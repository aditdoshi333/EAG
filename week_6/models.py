from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator

# Pydantic models for input validation
class PaperRetrievalInput(BaseModel):
    keywords: Optional[List[str]] = Field(None, description="List of keywords to search for in paper titles and abstracts")
    authors: Optional[List[str]] = Field(None, description="List of author names to search for")
    topics: Optional[List[str]] = Field(None, description="List of topics to filter papers by")
    year: Optional[int] = Field(None, description="Publication year to filter papers by")
    
    @field_validator('year')
    @classmethod
    def validate_year(cls, v):
        if v is not None and (v < 1900 or v > 2100):
            raise ValueError('Year must be between 1900 and 2100')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "keywords": ["quantum computing", "artificial intelligence"],
                "authors": ["Yoshua Bengio"],
                "topics": ["machine learning"],
                "year": 2023
            }
        }
    }

class DatasetExplorerInput(BaseModel):
    dataset_id: str = Field(..., description="ID or URL of the dataset to analyze")
    analysis_type: str = Field("summary", description="Type of analysis to perform (summary, distribution, correlation)")
    
    @field_validator('analysis_type')
    @classmethod
    def validate_analysis_type(cls, v):
        allowed_types = ["summary", "distribution", "correlation"]
        if v not in allowed_types:
            raise ValueError(f"Analysis type must be one of: {', '.join(allowed_types)}")
        return v

class CitationNetworkInput(BaseModel):
    paper_ids: List[str] = Field(..., description="List of paper IDs to analyze")
    analysis_depth: int = Field(1, description="Depth of citation analysis (1-3)")
    
    @field_validator('analysis_depth')
    @classmethod
    def validate_depth(cls, v):
        if v < 1 or v > 3:
            raise ValueError('Analysis depth must be between 1 and 3')
        return v

class ConceptExtractorInput(BaseModel):
    paper_ids: Optional[List[str]] = Field(None, description="List of paper IDs to extract concepts from")
    text: Optional[str] = Field(None, description="Text to extract concepts from")
    
    @field_validator('paper_ids', 'text')
    @classmethod
    def validate_input(cls, v, info):
        field_name = info.field_name
        if field_name == 'paper_ids' and v is None and info.data.get('text') is None:
            raise ValueError('Either paper_ids or text must be provided')
        if field_name == 'text' and v is None and info.data.get('paper_ids') is None:
            raise ValueError('Either paper_ids or text must be provided')
        return v

class CrossDomainConnectorInput(BaseModel):
    domain1: str = Field(..., description="First domain or field")
    domain2: str = Field(..., description="Second domain or field")

# Output models
class Paper(BaseModel):
    id: str
    title: str
    authors: List[str]
    abstract: str
    year: int
    categories: List[str]
    pdf_link: str

class PaperRetrievalOutput(BaseModel):
    papers: List[Paper]
    count: int
    query_params: Dict[str, Any]

# User query and response models
class UserQuery(BaseModel):
    query_text: str
    session_id: str

class AgentResponse(BaseModel):
    response_text: str
    tool_used: Optional[str] = None
    data: Optional[Dict[str, Any]] = None 