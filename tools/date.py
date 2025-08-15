import calendar
import datetime

from tools.tool_base_class import ToolBaseClass


class Date(ToolBaseClass):
    """
    Date - Uses Python's datetime and calendar libraries to retrieve the current date.

    args:
        None
    output:
        error: A string, an error message if an error occurred
        result: A string, the current date.
    """

    def get_description(self):
        desc = """date: Returns todays date
        No input is required.
        Here are some example Action Input to this tool:
        {}
        """
        return desc

    def get_firefunction_spec(self):

        desc = {
            "name": "date",
            "description": "This tool only returns the current date and time. It requires no arguments and does not provide any other functionality.",
            "parameters": {
                "type": "object",
                "properties": {
                    "none": {
                        "type": "string",
                        "description": "No input is required."
                    }
                },
                "required": ["none"],
            },
        }

        return desc

    def __init__(self):
        self.tool_name = "date"

    def validate(self, args={}):
        return True

    def call(self, args={}):
        historical_date = args.get("historical_date", None)
        if historical_date:
            date_string = args["historical_date"]
            date_obj = datetime.datetime.strptime(date_string, "%m/%d/%Y")

            # Format the datetime object to the desired output format
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
            return {
            "error": "",
            "result": f"Today is {formatted_date}.",
            }

        now = datetime.datetime.now()
        return {
            "error": "",
            "result": f"Today is {list(calendar.day_name)[now.weekday()]}, {calendar.month_name[now.month]} {now.day}, {now.year}.",
        }
