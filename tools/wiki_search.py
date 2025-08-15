import json
import requests
import wikipediaapi
from tools.tool_base_class import ToolBaseClass


class WikiSearch(ToolBaseClass):
    """
    Wikipedia Search - Uses ColBERTv2 to retrieve Wikipedia documents.

    args:
        query: A string, the input query (e.g. "what is a dog?")
        k : The number of documents to retrieve

    output:
        error: A string, an error message if an error occurred
        result: A list of strings, each string is a Wikipedia document

    Adapted from Stanford's DSP: https://github.com/stanfordnlp/dsp/
    Also see: https://github.com/lucabeetz/dsp
    """

    def __init__(self):
        self.tool_name = "wiki_search"

    def get_description(self):
        desc = """wiki_search: A tool to search Wikipedia.
        Your input should be a json (args json schema): {{"query" : string, "num_results": integer }} The Action to trigger this API should be wiki_search and the input parameters should be a json dict string. 
        Pay attention to the type of parameters.
        Here are some example Action Input to this tool:

        {"query": "Cristiano Ronaldo", "num_results": 5}
        """
        return desc
    
    def get_firefunction_spec(self):
        desc = {
            "name": "wiki_search",
            "description": "A tool to search Wikipedia. This tool returns the title and summary of the Wikipedia pages that match the input query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search for.",
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "The number of results to return.",
                    },
                },
                "required": ["query"],
            },
        }
        return desc

    def validate(self, args):
        if "query" not in args or not isinstance(args["query"], str):
            return False

    def call(self, args):
        url = (
            "http://ec2-44-228-128-229.us-west-2.compute.amazonaws.com:8893/api/search"
        )
        try:
            query = args["query"]
        except:
            return {"error": "Required field \"query\" not provided.", "result": ""}
        num_results = args.get("num_results", 5)

        language_code = "en"
        number_of_results = num_results
        headers = {"User-Agent": "tool-use-research"}

        base_url = "https://api.wikimedia.org/core/v1/wikipedia/"
        endpoint = "/search/page"
        url = base_url + language_code + endpoint
        parameters = {"q": query, "limit": number_of_results, "prop": ["extracts", "explaintext"]}

        try:
            response = requests.get(url, headers=headers, params=parameters)
        except:
            return {"error": "Could not connect to Wikipedia API", "result": ""}
        response = json.loads(response.text)

        keys = []

        try:
            for page in response["pages"]:
                keys.append(page["key"])
        except:
            return {"error": "Either we could not find results for this query or the API is down right now.", "result": ""}
        
        wiki_wiki = wikipediaapi.Wikipedia('MyProjectName (merlin@example.com)', 'en')
        pages = [wiki_wiki.page(key) for key in keys]

        results = [
            {
                "title": page.title,
                "summary": page.summary,
            } for page in pages
        ]

        return {"error": "", "result": results}
