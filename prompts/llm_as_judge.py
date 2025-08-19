import json
from prompts.utils import get_function_spec

PAIRWISE_LLM_AS_JUDGE_ACTION_PLAN_INSTRUCTIONS = """

You are an expert planner of tool calls. Your job is to critique the action plan of an assistant. The following information is shown to the assistant in order to devise an action plan:

Start of the message
You are a helpful assistant with access to functions. Please use the tools to provide information accurate up to current date and time: {current_date}.

FUNCTIONS: {func_spec}

Given the question and the tools available to you, judge which action plan is better suited to answer the question.
Refrain from using any specific tool calls in your action plan, instead focus on the high-level steps you would take to answer the question and the name of the tool you would use and how you would use it.
Refrain from trying to answer the question directly in the action plan.
End of the message

Given the set of functions and the question, figure out which one is better in outline the correct steps to get to the final answer. 
If the first action plan is better, output 1, if the second action plan is better, output 2. If both steps are equally good or bad, output "tie".


Furthermore, your output should follow the format:

Reasoning:
<your reasoning for the correctness or incorrectness of the action plan>

Label: ```json{{"better_action_plan": <"tie"/1/2>}}```'

Now do this for the following question and action plans:

Question: {question}

Action Plan 1:
{action_plan_1}

Action Plan 2:
{action_plan_2}


Reasoning:"""


PAIRWISE_LLM_AS_JUDGE_REACT_INSTRUCTIONS = """You are an expert judge of tool calls. Your job is to critique each of the ReAct steps of an assistant. The following information is shown to the assistant in order to devise a ReAct step:

Start of the message
You are a helpful assistant with access to functions. Use them if required. Please use the tools to provide information accurate up to current date and time: {current_date}.

FUNCTIONS: {func_spec}

Please stick to the following format:
    
Thought: you should always think about what to do
Action: the action to take, should be one of {func_list}
Action Input: the input to the action
End Action

If you believe that you have obtained enough information (which can be judged from the history observations) to answer the question, please call:

Thought: I have enough information to answer the question
Action: finish
Action Input: {{"answer": [your answer string]}}
End Action 

The finish action should only be used if you have the final answer to the entire question, calling it intermittently will prematurely end the conversation.
For your final answer (the finish action input), make sure you answer the full question and include any assumption you have made as well as the information you have used from the tools to answer the question.
Additionally, we want to make sure the final answers/outputs in the finish action input are returned in the order that they are given in a list format so we can verify them with an exact string match. For eg. if the prompt asks for a city name, its temperature and a list of names of all the NBA teams whose home stadium is within a 400 mile radius, you would output ['San Francisco', 78, ['Los Angeles Lakers', 'Golden State Warriors']]. If the prompt asks for a special sorting of the list, make sure to output wrap the list in {{}} and if doesn't require any special sorting wrap it in [] like you normally would. So if the prompt instead asked to list the names of all the NBA teams whose home stadium is within a 400 mile radius in alphabetical order, you would output [San Francisco, 78, {{Golden State Warriors, Los Angeles Lakers}}].
Only output the final answer with no additional text or natural language.
Give dates in YYYY-MM-DD format, temperatures in Celcius, prices in dollars, lengths in meters, area in meters^2, volume in m^3 and angles in degrees if the prompt doesn't specify what format/units to output the answer in.

Given the set of functions, question, action plan and history of past actions, critique the Thought, Action, and Action Input step for each candidate ReAct step. Assume the action plan and history of past actions are optimal steps and only judge the correctness of the thought, action and action input in two latest candidate ReAct step.

Given two react steps from the assistant, figure out which one is better in progressing to the final answer. Try not to penalize a candidate step for formatting on only select based on which candidate step is better in progressing to the final answer. If both steps are equally good, then output "tie".
If the first step is better, output 1, if the second step is better, output 2. If both steps are equally good or bad, output "tie".

Only output in following the format, ensuring that labels are a parseable JSON dictionary:

'Reasoning:
<your reasoning for why one step is better than the other>

Label: ```json{{"better_step": <"tie"/1/2>}}```'

Now do the this for the following:
 
Question: {question}

Action Plan:
{action_plan}

Here is the history of past actions. If there are no past actions yet, this will be empty:
{history}

Here are both candidate next ReAct steps provided by the assistant:

Candidate ReAct Step 1:

Thought: {thought_1}
Action: {action_1}
Action Input: {action_input_1}
Observation: {observation_1}



Candidate ReAct Step 2:

Thought: {thought_2}
Action: {action_2}
Action Input: {action_input_2}
Observation: {observation_2}


Please provide your critique of the latest ReAct step provided by the assistant.

YOU MUST ADHERE TO THE FOLLOWING FORMAT:
Reasoning:
<your reasoning for why one step is better than the other>

Label: ```json{{"better_step": <"tie"/1/2>}}```

Reasoning:
"""

def get_pairwise_judge_react_prompt(entry: dict):

    tools = entry['tools']
    query = entry['prompt']
    historical_date = entry['historical_date']
    preferred = entry['preferred']
    dispreferred = entry['dispreferred']
    history = json.loads(entry['history'])
    

    if historical_date:
        current_date = historical_date
    else:
        current_date = 'Tuesday, September 03, 2024'


    if len(history) != 0:
        action_plan = history[0]['action plan']['text']
        formatted_history = ["""Thought: {thought}\nAction: {action}\nAction Input: {action_input}\nObservation: {observation}\n""".format(
            thought=entry['thought']['text'],
            action=entry['action']['text'],
            action_input=entry['action_input']['text'],
            observation=entry['observation']['text']
        ) for entry in history[1:]]

        preferred_thought = preferred['thought']['text']
        preferred_action = preferred['action']['text']
        preferred_action_input = preferred['action_input']['text']
        preferred_observation = preferred['observation']['text']

        dispreferred_thought = dispreferred['thought']['text']
        dispreferred_action = dispreferred['action']['text']
        dispreferred_action_input = dispreferred['action_input']['text']
        dispreferred_observation = dispreferred['observation']['text']

        
        func_spec, func_list = get_function_spec(tools)

        preferred_first = PAIRWISE_LLM_AS_JUDGE_REACT_INSTRUCTIONS.format(
            func_spec=func_spec, 
            func_list=func_list, 
            question=query, 
            current_date=current_date, 
            action_plan=action_plan, 
            history="\n".join(formatted_history), 
            thought_1=preferred_thought, 
            action_1=preferred_action, 
            action_input_1=preferred_action_input, 
            observation_1=preferred_observation, 
            thought_2=dispreferred_thought, 
            action_2=dispreferred_action, 
            action_input_2=dispreferred_action_input, 
            observation_2=dispreferred_observation
        )

        dispreferred_first = PAIRWISE_LLM_AS_JUDGE_REACT_INSTRUCTIONS.format(
            func_spec=func_spec, 
            func_list=func_list, 
            question=query, 
            current_date=current_date, 
            action_plan=action_plan, 
            history="\n".join(formatted_history), 
            thought_1=dispreferred_thought, 
            action_1=dispreferred_action, 
            action_input_1=dispreferred_action_input, 
            observation_1=dispreferred_observation, 
            thought_2=preferred_thought, 
            action_2=preferred_action, 
            action_input_2=preferred_action_input, 
            observation_2=preferred_observation
        )
    
        return preferred_first, dispreferred_first
    
    else:

        action_plan_preferred = preferred['action plan']['text']
        action_plan_dispreferred = dispreferred['action plan']['text']
        func_spec, func_list = get_function_spec(tools)
        preferred_first = PAIRWISE_LLM_AS_JUDGE_ACTION_PLAN_INSTRUCTIONS.format(
            func_spec=func_spec, 
            func_list=func_list, 
            question=query, 
            current_date=current_date, 
            action_plan_1=action_plan_preferred, 
            action_plan_2=action_plan_dispreferred, 
        )

        dispreferred_first = PAIRWISE_LLM_AS_JUDGE_ACTION_PLAN_INSTRUCTIONS.format(
            func_spec=func_spec, 
            func_list=func_list, 
            question=query, 
            current_date=current_date, 
            action_plan_1=action_plan_dispreferred, 
            action_plan_2=action_plan_preferred, 
        )

        return preferred_first, dispreferred_first
