from writer.abstract import register_abstract_template
from writer.blocks.base_block import WorkflowBlock
from writer.ss_types import AbstractTemplate
import json

class JSONToString(WorkflowBlock):

    @classmethod
    def register(cls, type: str):
        super(JSONToString, cls).register(type)
        register_abstract_template(type, AbstractTemplate(
            baseType="workflows_node",
            writer={
                "name": "JSON to string",
                "description": "Converts a JSON object to a string.",
                "category": "Other",
                "fields": {
                    "jsonInput": {
                        "name": "JSON input",
                        "type": "Text",
                        "control": "Textarea",
                        "desc": "The JSON object to convert to a string.",
                        "required": True
                    },
                },
                "outs": {
                    "success": {
                        "name": "Success",
                        "description": "If the function doesn't raise an Exception.",
                        "style": "success",
                    },
                    "error": {
                        "name": "Error",
                        "description": "If the function raises an Exception.",
                        "style": "error",
                    },
                },
            }
        ))

    def run(self):
        print("JSONToString.run()")
        try:
            json_input = self._get_field("jsonInput", as_json=True, required=True)
            string_output = json.dumps(json_input)
            self.result = string_output
            self.outcome = "success"
        except BaseException as e:
            self.outcome = "error"
            raise e