from collections import deque
from typing import Type, List
from tree.react_tree import (ReActStep, ReActNode, ReActTreeManager, get_observation_step)
from prompts.action_plan import get_prompt as get_action_plan_prompt
from prompts.react import get_prompt as get_react_prompt
from tree.react_tree import ReActTreeManager
from model.models import GenerationWrapper


def pre_process(task_batch: List[dict]):
    """
    Pre-processes the task batch into a list of ReActTreeManager objects.

    Args:
        task_batch: List of tasks.
    """
    tree_list=[]
    queue = deque()
    for task in task_batch:
        query = task["prompt"]
        tool = task["tools"]
        manager = ReActTreeManager(query, tool)
        if 'history' in task:
            history = task["history"]
            for node in history:
                thought=ReActStep('Thought', node["thought"])
                action=ReActStep('Action', node["action"])
                action_input=ReActStep('Action Input', node["action_input"])
                if "observation" in node:
                    observation=ReActStep('Observation', node["observation"])
                else:
                    observation, _ = get_observation_step(action, action_input)
                new_node=ReActNode(thought, action, action_input, observation)
                new_node.mgr=manager
                manager.roots[-1].add_child(new_node)
                manager.roots.append(new_node)

        if 'action_plan' in task:
            if task['action_plan']:
                manager.add_action_plan(task['action_plan'])

            tree_list.append(manager)
        else:
            tree_list.append(manager)

        for k,v in task.items():
            if k not in ["prompt", "tools", "history", "action_plan", "ground_truth"]:
                manager.add_metadata(k,v)

        if "answer" in task:
            manager.ground_truth=task["answer"]
            
    for tree in tree_list:
        queue.append(tree.root)
        
    return queue, tree_list

def generate_action_plan(tree_list: Type[ReActTreeManager], model: Type[GenerationWrapper]):
    """
    Generates an action plan for each tree in the batch.

    Args:
        tree_list: List of ReActTreeManager objects.
        model: Model to generate the action plan.
    """
    batch = tree_list
    queries = [tree.query for tree in batch]
    tools = [tree.tools_available for tree in batch]
    hist_dates=[tree.metadata['historical_date'].replace('\\','') if ('historical_data' in tree.metadata and tree.metadata['historical_date']) else None for tree in batch]
    prompts = [get_action_plan_prompt(query, tool, hist_date) for query, tool, hist_date in zip(queries, tools, hist_dates)]
    action_plans = [model.generate(prompt)[0] for prompt in prompts]
    for i, tree in enumerate(batch):
        tree.add_action_plan(action_plans[i])

def get_react_prompts(nodes: List[ReActNode]):
    """
    Retreive the model prompts to get ReAct style generation.

    Args:
        nodes: List of ReActNode objects.
    """

    prompts = []
    for node in nodes:
        action_plan = node.mgr.action_plan if node.mgr.revised_action_plan is None else node.mgr.revised_action_plan
        prompts.append(get_react_prompt(node.mgr.query, node.mgr.tools_available, node.generate_history(), action_plan))
    return prompts
