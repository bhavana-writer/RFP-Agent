from fastapi import APIRouter, HTTPException, UploadFile
from app.services.writer_service import WriterService
from app.models.writer_models import TextGenInput
from pydantic import BaseModel

from typing import List

router = APIRouter()
writer_service = WriterService()

class QuestionGraphRequest(BaseModel):
    graph_ids: list
    question: str

class TextGenInput(BaseModel):
    id: str
    value: List[str]

class TextGenerationRequest(BaseModel):
    application_id: str
    inputs: List[TextGenInput]
    stream: bool = False

@router.post("/chat/completion")
async def chat_completion_endpoint(
    messages: list, 
    model: str = "palmyra-x-004", 
    tools: list = None, 
    tool_choice: str = None
):
    """
    API endpoint to perform chat completion with optional tool calling.
    """
    try:
        response = writer_service.chat_completion(
            messages=messages,
            model=model,
            tools=tools,
            tool_choice=tool_choice
        )
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/text-generation", response_model=dict)
async def text_generation_endpoint(request: TextGenerationRequest):
    """
    API endpoint to generate content using a Writer text generation application.
    """
    try:
        # Convert Pydantic models to dictionaries
        writer_inputs = [
            {
                "id": input_item.id,
                "value": input_item.value
            }
            for input_item in request.inputs
        ]
        
        response = writer_service.call_writer_text_gen_app(
            application_id=request.application_id,
            inputs=writer_inputs,
            stream=request.stream
        )
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/upload-file")
async def upload_file(file_path: str):
    """
    Endpoint to upload a file to Writer.
    """
    try:
        response = writer_service.upload_file(file_path)
        if "error" in response:
            raise HTTPException(status_code=400, detail=response["error"])
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-graph")
async def create_graph(name: str):
    """
    Endpoint to create a knowledge graph.
    """
    try:
        response = writer_service.create_graph(name)
        if "error" in response:
            raise HTTPException(status_code=400, detail=response["error"])
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-file-to-graph")
async def add_file_to_graph(graph_id: str, file_id: str):
    """
    Endpoint to add a file to a knowledge graph.
    """
    try:
        response = writer_service.add_file_to_graph(graph_id, file_id)
        if "error" in response:
            raise HTTPException(status_code=400, detail=response["error"])
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/question-graph")
async def question_graph_endpoint(request: QuestionGraphRequest):
    """
    API endpoint to query a knowledge graph using a question.
    The subqueries are disabled by default.
    """
    try:
        response = writer_service.question_graph(
            graph_ids=request.graph_ids,
            question=request.question,
            stream=False,
            subqueries=False
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))