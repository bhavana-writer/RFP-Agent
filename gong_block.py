import os
import requests
import base64
from writer.abstract import register_abstract_template
from writer.blocks.base_block import WorkflowBlock
from writer.ss_types import AbstractTemplate, WriterConfigurationError



class GongIntegration(WorkflowBlock):

    @classmethod
    def register(cls, type: str):
        super(GongIntegration, cls).register(type)
        register_abstract_template(type, AbstractTemplate(
            baseType="workflows_node",
            writer={
                "name": "Gong Integration",
                "description": "Retrieves a transcript for a specific Gong call",
                "category": "Other",
                "fields": {
                    "callId": {
                        "name": "Call ID",
                        "type": "Text",
                        "desc": "The ID of the Gong call to retrieve the transcript for.",
                        "required": True
                    },
                },
                "outs": {
                    "success": {
                        "name": "Success",
                        "description": "The transcript was successfully retrieved.",
                        "style": "success",
                    },
                    "error": {
                        "name": "Error",
                        "description": "The transcript retrieval failed.",
                        "style": "error",
                    },
                },
            }
        ))
    def run(self):
        print("GongIntegration.run()")
        try:
            call_id = self._get_field("callId", required=True)
            access_key = os.getenv("GONG_API_ACCESS_KEY")
            secret_key = os.getenv("GONG_API_SECRET_KEY")

            if not access_key or not secret_key:
                raise WriterConfigurationError("Gong API Access Key and Secret Key must be provided in the environment variables file.")

            # Create base64 encoded authorization token
            auth_string = f"{access_key}:{secret_key}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Content-Type": "application/json"
            }

            # First request to get the call data and transcript
            call_url = f"https://api.gong.io/v2/calls/{call_id}"
            call_response = requests.get(call_url, headers=headers, timeout=30)

            if not call_response.ok:
                error_msg = f"Call details request failed: {call_response.status_code} - {call_response.text}"
                raise WriterConfigurationError(error_msg)

            call_json = call_response.json()
            call_data = call_json.get("call", {})
            
            if not call_data:
                raise WriterConfigurationError(f"No call found with ID: {call_id}")

            # Get transcript from call data
            transcript = call_data.get("transcript", [])
            speakers = call_data.get("parties", [])

            # Map speaker IDs to names
            speaker_map = {speaker["id"]: speaker.get("name", "Unknown") for speaker in speakers}

            # Format the transcript
            formatted_transcript = "Transcript\n"
            for entry in transcript:
                time = entry.get("startTime", 0)
                speaker_id = entry.get("speakerId")
                text = entry.get("text", "")
                speaker_name = speaker_map.get(speaker_id, "Unknown")
                formatted_transcript += f"{time:.2f} | {speaker_name}\n{text}\n"

            # Include full response data along with formatted transcript
            self.result = {
                "call_data": call_data,
                "formatted_transcript": formatted_transcript.strip()
            }
            self.outcome = "success"
        except requests.RequestException as e:
            self.outcome = "error"
            raise WriterConfigurationError(f"API request failed: {str(e)}")
        except BaseException as e:
            self.outcome = "error"
            raise e









