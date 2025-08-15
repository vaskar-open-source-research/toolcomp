import json
from tools.helper import get_all_tools_mapping
from datetime import datetime

def get_function_spec(tools):
    map = get_all_tools_mapping()
    tool_list = [map[tool] for tool in tools]
    func_spec = [tool.get_firefunction_spec() for tool in tool_list]
    func_list = [tool.tool_name for tool in tool_list]

    finish_spec = { 
            "name": "finish",
            "description": "Finish the task and provide answer to the user question. The finish step should only be used if you have the final answer to the entire question, calling it intermittently will prematurely end the conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": """Make sure you answer the full question. Additionally, we want to make sure the final answers/outputs in the finish action input are returned in the order that they are given in a list format so we can verify them with an exact string match. For eg. if the prompt asks for a city name, its temperature and a list of names of all the NBA teams whose home stadium is within a 400 mile radius, you would output ['San Francisco', 78, ['Los Angeles Lakers', 'Golden State Warriors']]. If the prompt asks for a special sorting of the list, make sure to output wrap the list in {{}} and if doesn't require any special sorting wrap it in [] like you normally would. So if the prompt instead asked to list the names of all the NBA teams whose home stadium is within a 400 mile radius in alphabetical order, you would output [San Francisco, 78, {{Golden State Warriors, Los Angeles Lakers}}]. Only output the final answer with no additional text or natural language or units. Give dates in YYYY-MM-DD format, temperatures in celcius, prices in dollars, lengths in meters, area in meters^2, volume in m^3 and angles in degrees if the prompt doesn't specify what format/units to output the answer in.""",      
                },
                "required": ["answer"]
            },
        }
    }

    func_spec.append(finish_spec)
    func_list.append("finish")
    func_spec = json.dumps(func_spec, indent=4)

    return func_spec, func_list

def current_date(historical_date=None):
    if historical_date:
        date_obj = datetime.strptime(historical_date, "%m/%d/%Y")
        return date_obj.strftime("%A, %B %d, %Y")

    return datetime.now().strftime("%A, %B %d, %Y")
