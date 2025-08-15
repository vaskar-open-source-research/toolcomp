
from typing import List
from prompts.utils import get_function_spec
from prompts.utils import current_date


FORMAT_INSTRUCTIONS_USER_FUNCTION = """
You are a helpful assistant with access to functions. Please use the tools to provide information accurate up to current date: {current_date}.

FUNCTIONS: {func_spec}

Question: {question}

Given the question and the tools available to you above, please formulate an action plan to answer the question in a bulleted list for each step. 
Refrain from using any specific tool calls in your action plan, instead focus on the high-level steps you would take to answer the question and the name of the tool you would use and how you would use it.
Refrain from trying to answer the question directly in the action plan.

"""

ACTION_PLAN_SYSTEM_PROMPT = """
You are a helpful action planner with access to functions. Please use the tools to provide information accurate up to current date: {current_date}.

Given the tools available to you above, please formulate an action plan to answer the question in a bulleted list for each step. 
Refrain from using any specific tool calls in your action plan, instead focus on the high-level steps you would take to answer the question and the name of the tool you would use and how you would use it.
Refrain from trying to answer the question directly in the action plan.
"""

ACTION_PLAN_USER_PROMPT = '''Question: {question}'''


def get_prompt(query: str, tools: List[str], historical_date: str = None, apply_chat_template: bool = False):
    func_spec, func_list = get_function_spec(tools)

    if historical_date:
        current_date = historical_date
    else:
        current_date = 'Tuesday, September 03, 2024'

    sys = FORMAT_INSTRUCTIONS_USER_FUNCTION.format(
        func_spec=func_spec,
        question=query,
        current_date=current_date
    )
    usr = ACTION_PLAN_USER_PROMPT.format(
        question=query,
        current_date=current_date
    )

    output = [
        {"role": "system", "content": sys},
        {"role": "user", "content": usr},
    ]

    return output
