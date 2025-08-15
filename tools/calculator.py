from tools.calculator_impl import Calculator as CalculatorImpl
from tools.tool_base_class import ToolBaseClass


class Calculator(ToolBaseClass):

    def __init__(self):
        self.tool_name = "calculator"
        self.calculator = CalculatorImpl()

    def get_description(self):
        desc = """calculator: Calculates the expression for multiplication, addition, substraction, division, exponentiation with brackets.
        Your input should be a json (args json schema): {{"expression" : string }} The Action to trigger this API should be calculator and the input parameters should be a json dict string. 
        Pay attention to the type of parameters.
        Here are some example Action Input to this tool:

        {"expression": "2 * 3.14 * 5"}
        {"expression": "2 * (7+1) / (2 + 5 + (10-9)) "}
        {"expression" : "1^2"}
        """
        return desc
    
    def get_firefunction_spec(self):
        desc = {
            "name": "calculator",
            "description": "Computes numerical expressions involving float numbers and operators like +, -, *, /, ^. For unary minus, use brackets, for example, (-5).",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": 'The expression to be calculated, for example "2 * 3.14 * 5".',
                    }
                },
                "required": ["operation"],
            }
        }
        return desc

    def validate(self, args={}):
        if "operation" not in args or not isinstance(args["operation"], str):
            return False
        return True

    def call(self, args={}):
        try:
            input_query = args["operation"]
        except:
            return {"error": "Required field \"operation\" not provided.", "result": ""}
        if not self.validate(args):
            return {
                "error": "Invalid Input: could not find operation as an argument",
                "result": "",
            }
        
        try:
            result = self.calculator.calculate(input_query)
            return {"error": "", "result": str(result)}
        except Exception as e:
            return {"error": str(e), "result": ""}
