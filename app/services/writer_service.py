import os
from writerai import Writer
from app.config import settings
from typing import List, Dict, Optional, Any
from typing import Union
import json
from app.models.writer_models import (
    TextGenInput,
    TextGenOutput,
    FileUploadOutput,
    GraphCreationOutput,
    AddFileToGraphOutput,
    QuestionGraphInput,
    QuestionGraphOutput,
)

class WriterService:
    """
    Service for interacting with Writer APIs, including chat completion,
    application content generation, and tool function handling.
    """

    def __init__(self):
        """
        Initialize the Writer API client using the API key from the environment variable.
        """
        self.client = Writer(api_key=settings.WRITER_API_KEY)

    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "palmyra-x-004", 
        tools: Optional[List[Dict[str, Any]]] = None, 
        tool_choice: Optional[str] = None
    ) -> Dict:
        """
        Generate chat completion using the Writer API, with optional tool calling.

        :param messages: A list of message dictionaries with "content" and "role".
                         Example: [{"content": "Hello, world!", "role": "user"}]
        :param model: The model to use for the chat completion. Default is "palmyra-x-004".
        :param tools: Optional list of tool definitions for tool calling.
        :param tool_choice: Optional tool selection strategy. Default is None.
        :return: The response dictionary from the Writer API, including tool calls if any.
        """
        try:
            response = self.client.chat.chat(
                messages=messages,
                model=model,
                tools=tools,
                tool_choice=tool_choice
            )

            # Check for tool calls
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                # Process the tool call
                return self._process_tool_call(tool_call, messages, tools, model)

            return {
                "id": response.id,
                "choices": response.choices,
                "created": response.created,
                "model": response.model,
                "usage": response.usage,
            }
        except Exception as e:
            return {"error": str(e)}

    def _process_tool_call(
        self, 
        tool_call: Dict, 
        messages: List[Dict[str, str]], 
        tools: List[Dict[str, Any]], 
        model: str
    ) -> Dict:
        """
        Handles processing of tool calls by executing the tool and getting the final model response.

        :param tool_call: The tool call object from the initial response.
        :param messages: The list of messages for the chat session.
        :param tools: The tools passed to the model.
        :param model: The model being used for chat completion.
        :return: The final response from the Writer API after processing the tool call.
        """
        try:
            # Parse the tool call and arguments
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            # Placeholder for tool execution (extend this logic based on actual tools)
            if tool_name in self._available_tools():
                result = self._available_tools()[tool_name](**arguments)
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": str(result),
                    }
                )
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            # Get the final response
            second_response = self.client.chat.chat(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            return {
                "id": second_response.id,
                "choices": second_response.choices,
                "created": second_response.created,
                "model": second_response.model,
                "usage": second_response.usage,
            }
        except Exception as e:
            return {"error": f"Tool processing failed: {str(e)}"}

    def _available_tools(self) -> Dict[str, Any]:
        """
        Returns a dictionary of available tools mapped to their execution functions.

        :return: Dictionary with tool names as keys and callable functions as values.
        """
        # Add actual tool functions here
        return {
            # Example: "tool_name": self._tool_function
            # Extend with actual tool logic
        }

    def call_writer_text_gen_app(self, application_id: str, inputs: List[TextGenInput]) -> Dict:
        """
        Call the Writer text generation application to generate content.

        :param application_id: The ID of the Writer application to use.
        :param inputs: A list of dictionaries with `id` and `value`.
        :return: A dictionary containing the title and suggestion.
        """
        try:
            # Convert TextGenInput models to dictionaries
            input_dicts = [input_item.dict() for input_item in inputs]

            # Call Writer API
            response = self.client.applications.generate_content(
                application_id=application_id,
                inputs=input_dicts
            )

            # Return structured output
            return {
                "title": response.title,
                "suggestion": response.suggestion,
            }
        except Exception as e:
            return {"error": str(e)}
    
    def upload_file(self, file_path: str) -> Dict:
        """
        Upload a file to Writer.

        :param file_path: The file path to upload.
        :return: The uploaded file's metadata or an error message.
        """
        try:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}

            with open(file_path, 'rb') as f:
                content = f.read()

            content_type = "application/pdf" if file_path.endswith('.pdf') else "text/plain"
            uploaded_file = self.client.files.upload(
                content=content,
                content_type=content_type,
                content_disposition=f"attachment; filename=\"{os.path.basename(file_path)}\"",
            )
            return {"file_id": uploaded_file.id}
        except Exception as e:
            return {"error": str(e)}

    def create_graph(self, name: str) -> Dict:
        """
        Create a knowledge graph.

        :param name: The name of the graph.
        :return: The created graph's metadata or an error message.
        """
        try:
            graph = self.client.graphs.create(name=name)
            return {"graph_id": graph.id}
        except Exception as e:
            return {"error": str(e)}

    def add_file_to_graph(self, graph_id: str, file_id: str) -> Dict:
        """
        Add a file to a graph.

        :param graph_id: The ID of the graph.
        :param file_id: The ID of the file to add.
        :return: The added file's metadata or an error message.
        """
        try:
            file = self.client.graphs.add_file_to_graph(
                graph_id=graph_id,
                file_id=file_id
            )
            return {"file_id": file.id}
        except Exception as e:
            return {"error": str(e)}

    def question_graph(self, graph_ids: List[str], question: str, stream: bool = False, subqueries: bool = True) -> Dict:
        """
        Ask a question to a graph.

        :param graph_ids: List of graph IDs to query.
        :param question: The question to ask.
        :param stream: Whether to stream the response. Default is False.
        :param subqueries: Whether to allow subqueries. Default is True.
        :return: The response from the graph or an error message.
        """
        try:
            response = self.client.graphs.question(
                graph_ids=graph_ids,
                question=question,
                stream=stream,
                subqueries=subqueries,
            )
            return {
                "question": response.question,
                "answer": response.answer,
                "sources": response.sources,
            }
        except Exception as e:
            return {"error": str(e)}
    
