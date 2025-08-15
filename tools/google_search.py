import requests

from serpapi import GoogleSearch
from tools.tool_base_class import ToolBaseClass
from tools.tool_utils import format_search_results, format_knowledge_graph
from utils.keystore import auth_tools
import os


class GoogleAPI(ToolBaseClass):
    """
    Google Search

    Uses Google's Custom Search API to retrieve Google Search results.

    input_query - The query to search for.
    num_results - The number of results to return.

    output - A list of dictionaries, each dictionary is a Google Search result
    """

    def __init__(self):
        self.tool_name = "google_search"
        self.api_key = os.getenv("SEARCHAPI_API_KEY")

    def get_description(self):
        desc = """google_search: Google Search tool.
        Your input should be a json (args json schema): {{"query" : string, "num_results": integer }} The Action to trigger this API should be google_search and the input parameters should be a json dict string. 
        Pay attention to the type of parameters.
        Here are some example Action Input to this tool:

        {"input_query": "what is 4 + 5?", "num_results": 5}
        {"input_query": "what is Ronaldo's age?", "num_results": 5}
        """
        return desc

    def get_firefunction_spec(self):

        desc = {
            "name": "google_search",
            "description": "This tool allows you to search Google for a query. Some queriable information includes trivia, general knowledge, current events, weather, and more.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search for.",
                    },
                    "location": {
                        "type": "string",
                        "description": "The location to search from. Default is None."
                    }
                },
                "required": ["query"],
            },
        }

        return desc

    def validate(self, args={}):
        if "query" not in args or not isinstance(args["query"], str):
            return False
        return True

    def get_response(self, search_data):
        organic_results = search_data['organic_results']
        num_organic_results = len(organic_results)
        results = []
        for k in range(num_organic_results):
            results.append(format_search_results(organic_results[k]))

        if 'knowledge_graph' in search_data:
            knowledge_graph = format_knowledge_graph(search_data['knowledge_graph'])
            results.append(knowledge_graph)

        return results

    def call(self, args={}):
        try:
            input_query = args["query"]
        except:
            return {"error": "Required field \"query\" not provided.", "result": ""}
        location = args.get("location", None)
        params = {
            "engine": "google",
            "q": input_query,
            "hl": "en",
            "gl": "us",
            "google_domain": "google.com",
            "api_key": self.api_key,
        }

        if location:
            params["location"] = location

        try:
            search = GoogleSearch(params)
            response = search.get_dict()

            if "error" in response:
                return {"error": response["error"], "result": ""}
            results = self.get_response(response)
            return {"error": "", "result": results}
        except Exception as e:
            return {"error": str(e), "result": ""}
