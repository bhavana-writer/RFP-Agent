from pydantic import BaseModel
from typing import List, Union, Dict, Any


class TextGenInput(BaseModel):
    id: str  # The identifier
    value: Union[str, List[str]]  # The value can be a string or a list of strings


class TextGenOutput(BaseModel):
    title: str
    suggestion: str


class FileUploadOutput(BaseModel):
    file_id: str


class GraphCreationOutput(BaseModel):
    graph_id: str


class AddFileToGraphOutput(BaseModel):
    file_id: str


class QuestionGraphInput(BaseModel):
    graph_ids: List[str]
    question: str
    stream: bool = False
    subqueries: bool = True


class QuestionGraphOutput(BaseModel):
    question: str
    answer: str
    sources: List[Dict[str, Any]]
