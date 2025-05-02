from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Input/Output models for tools

class AddInput(BaseModel):
    a: int
    b: int

class AddOutput(BaseModel):
    result: int

class SqrtInput(BaseModel):
    a: int

class SqrtOutput(BaseModel):
    result: float

class StringsToIntsInput(BaseModel):
    string: str

class StringsToIntsOutput(BaseModel):
    ascii_values: List[int]

class ExpSumInput(BaseModel):
    int_list: List[int]

class ExpSumOutput(BaseModel):
    result: float

class WebPageInput(BaseModel):
    url: str
    content: str

class WebPageOutput(BaseModel):
    success: bool
    error: Optional[str] = None

class SearchInput(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    url: str
    content: str
    score: float
    timestamp: datetime
    hash: str

class SearchOutput(BaseModel):
    results: List[SearchResult]

class HighlightInput(BaseModel):
    text: str
    query: str

class HighlightOutput(BaseModel):
    highlighted_text: str

class IndexedPage(BaseModel):
    url: str
    timestamp: datetime
    hash: str

class IndexedPagesOutput(BaseModel):
    pages: List[IndexedPage]
    error: Optional[str] = None
