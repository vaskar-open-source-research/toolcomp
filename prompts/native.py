from prompts.utils import current_date
from typing import List


FUNCTION_CALLING_SYSTEM_PROMPT = """
You are a helpful assistant with access to tools to answer the user's request.
The user will provide you a question and a high level action plan. Your job is to execute on the action plan to answer the question. It's okay to slightly deviate from the action plan if you think it's necessary.

Please use the tools to provide information accurate up to current date: {current_date}.

Only output the final answer with no additional text or natural language.
Give dates in YYYY-MM-DD format, temperatures in celcius, prices in dollars, lengths in meters, area in meters^2, volume in m^3 and angles in degrees if the prompt doesn't specify what format/units to output the answer in.

Your final answer should be in the following format:

```json
{{"final_answer": [your answer list]}}
```
"""

USER_PROMPT = '''Question: {question} \n Action Plan: {action_plan}'''

def get_prompt(query: str, tools: List[str], action_plan: str = None, historical_date: str = None, apply_chat_template: bool = False):    

    user_content = USER_PROMPT.format(question=query, action_plan=action_plan)
    if historical_date:
        user_content += f"\n You can assume the current date is {historical_date}."

    if historical_date:
        current_date = historical_date
    else:
        current_date = 'Tuesday, September 03, 2024'

    messages = [
        {"role": "system", "content": FUNCTION_CALLING_SYSTEM_PROMPT.format(current_date=current_date)},
        {"role": "user", "content": user_content},
    ]

    return messages
