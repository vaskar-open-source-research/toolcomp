from typing import List
from prompts.utils import get_function_spec

# Adapted from Tool-LLM Implementation

REACT_SYSTEM_PROMPT = """
You are a helpful assistant with access to functions, each function will be regarded as an action. Your job is to take relevant and necessary actions to get to the final answer to a user question. Please use the actions to provide information accurate up to current date and time: {current_date}. The user will provide you a question and a high level action plan. Your job is to execute on the action plan to answer the question. It's okay to slightly deviate from the action plan if you think it's necessary.

FUNCTIONS: {func_spec}

Please stick to the following format:
    
Thought: <your reasoning/thought on why/how to use an action>
Action: <the action to take, should be one of {func_list}>
Action Input: <the input to the action (should be in JSON format with the required fields)>
End Action

If you believe that you have obtained enough information (which can be judged from the history observations) to answer the question, please call:

Thought: I have enough information to answer the question
Action: finish
Action Input: {{"answer": [your answer string]}}
End Action 

For your final answer (the finish action input), make sure you answer the full question and include any assumption you have made as well as the information you have used from the tools to answer the question.
Additionally, we want to make sure the final answers/outputs in the finish action input are returned in the order that they are given in a list format so we can verify them with an exact string match. For eg. if the prompt asks for a city name, its temperature and a list of names of all the NBA teams whose home stadium is within a 400 mile radius, you would output ['San Francisco', 78, ['Los Angeles Lakers', 'Golden State Warriors']]. If the prompt asks for a special sorting of the list, make sure to output wrap the list in {{}} and if doesn't require any special sorting wrap it in [] like you normally would. So if the prompt instead asked to list the names of all the NBA teams whose home stadium is within a 400 mile radius in alphabetical order, you would output [San Francisco, 78, {{Golden State Warriors, Los Angeles Lakers}}].
Only output the final answer with no additional text or natural language.
Give dates in YYYY-MM-DD format, temperatures in celcius, prices in dollars, lengths in meters, area in meters^2, volume in m^3 and angles in degrees if the prompt doesn't specify what format/units to output the answer in.

Given a user provided question and action plan Question and Action Plan, as well as your previous actions and observations under History, take your next action."""


REACT_USER_PROMPT = '''Question: {question}\n\nAction Plan: {action_plan}\n\nHistory: {history}'''


def get_prompt(
    query: str, 
    tools: List[str], 
    history: str, 
    action_plan: str = None, 
    historical_date: str = None, 
    apply_chat_template: bool = False
    ):
    
    func_spec, func_list = get_function_spec(tools)

    if historical_date:
        current_date = historical_date
    else:
        current_date = 'Tuesday, September 03, 2024'    

    system_prompt = REACT_SYSTEM_PROMPT.format(func_list=func_list, current_date=current_date, func_spec=func_spec)
    user_prompt = REACT_USER_PROMPT.format(question=query, action_plan=action_plan, history=history)

    output = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    return output
