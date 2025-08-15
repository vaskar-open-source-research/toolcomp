from tools.tool_base_class import ToolBaseClass
from tools.code import SphereEngineCodeExecutor

code_executor = SphereEngineCodeExecutor(verbose=False)

class PythonInterpreter(ToolBaseClass):
    def __init__(self):
        self.tool_name = "python_interpreter"

    def get_firefunction_spec(self):

        desc = {
            "name": "python_interpreter",
            "description": "Python interpreter tool. This tool allows you to run Python code. The supported libraries are numpy, pandas, and scipy on top of the basic python libraries. Make sure to add print statements to any variables or expressions you want to see the output of. Additionally, make sure to use new line characters (\\n) to separate lines of code. You may NOT call other tools from this tool, it will not work.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to run. Make sure to add print statements to any variables or expressions you want to see the output of. Additionally, make sure to use new line characters (\\n) to separate lines of code.",
                    },
                },
                "required": ["code"],
            },
        }

        return desc

    def validate(self, args={}):
        if "code" not in args or not isinstance(args["code"], str):
            return False
        return True

    def call(self, args={}):
        try:
            code = args["code"]
        except:
            return {"error": "Required field \"code\" not provided.", "result": ""}
        if not code:
            return {"error": "Code field is empty.", "result": ""}
        if not self.validate(args):
            return {"error": "Invalid input.", "result": ""}

        executed = code_executor.execute_sync(
            code, 'Python 3.x', version='python 3.9.5'
        )
        
        return {"result": executed.output, "error": executed.cmpinfo if executed.cmpinfo else ""}
