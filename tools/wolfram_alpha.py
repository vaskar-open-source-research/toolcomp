import wolframalpha
from tools.tool_base_class import ToolBaseClass
import os
from utils.keystore import auth_tools


class WolframAlpha(ToolBaseClass):

    def __init__(self):
        self.tool_name = "wolfram_alpha"
        self.api_key = os.getenv("WOLFRAM_ALPHA_API_KEY")

    def get_description(self):
        desc = """wolfram_alpha: A computational knowledge engine: it generates output by doing computations from the Wolfram Knowledgebase. Please be aware that wolfram_alpha is not a search engine, so some questions may not be supported in the Wolfram Knowledgebase.
        Your input should be a json (args json schema): {{"expression" : string }} The Action to trigger this API should be wolfram_alpha and the input parameters should be a json dict string. 
        Pay attention to the type of parameters.
        Here are some example Action Input to this tool:

        {"input_query": "what is 4 + 5?"}
        {"input_query": "what is Ronaldo's age?"}
        """
        return desc

    def get_firefunction_spec(self):
        desc = {
            "name": "wolfram_alpha",
            "description": "A computational knowledge engine: it generates output by doing computations from the Wolfram Knowledgebase. Please be aware that wolfram_alpha is not a search engine, so some questions may not be supported in the Wolfram Knowledgebase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search for.",
                    }
                },
                "required": ["query"],
            }
        }
        return desc

    def validate(self, args={}):
        if "query" not in args or not isinstance(args["query"], str):
            return False
        return True

    def call(self, args={}):
        try:
            input_query = args["query"]
        except:
            return {"error": "Required field \"query\" not provided.", "result": ""}
        
        if not self.validate(args):
            return {
                "error": "Invalid Input: could not find query as an argument",
                "result": "",
            }
        wolfram_client = wolframalpha.Client(self.api_key)
        try:
            response = wolfram_client.query(input_query)
            if not response["@success"]:
                return {
                    "error": "This information is not in the Wolfram Knowledgebase",
                    "result": "",
                }
            return {"error": "", "result": next(response.results).text}
        except Exception as e:
            return {"error": str(e), "result": ""}
