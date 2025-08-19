from collections import deque
from typing import List, Optional, Type
from inference.inference_utils import generate_action_plan, get_react_prompts, pre_process
from tree.react_tree import ReActNode, process_policy_output
from model.models import GenerationWrapper

def post_process(prompts: List[str], generations: List[str], curr_nodes: List[ReActNode], num_retries: int, max_depth: int, propogate_final_answer_found: bool = False):
    """
    Post processes the output of the model.

    Args:
        prompts: List of prompts used to generate the generations.
        generations: List of generations.
        curr_nodes: List of nodes to post process.
        num_retries: Number of retries for each node.
        max_depth: Maximum depth of the chain.
        propogate_final_answer_found: Whether to propogate the final answer found in the chain. This is to allow policy model to generate a final answer step and judge model to still judge the final answer step.
    """

    add_to_queue = []
    for i, generation in enumerate(generations):

        try:
            historical_date = None
            if 'historical_date' in curr_nodes[i].mgr.metadata and  curr_nodes[i].mgr.metadata['historical_date']:
                historical_date = curr_nodes[i].mgr.metadata['historical_date'].replace('\\','')
            react_node, found_answer = process_policy_output('Thought:'+generation.strip('Thought:').strip('End Action').strip() +'\nEnd Action', historical_date)
            react_node.add_metadata("prompt", prompts[i])
            curr_nodes[i].add_child(react_node)
        except Exception as e:
            curr_nodes[i].update_errors(str(e))
            found_answer = False
            react_node = curr_nodes[i]

        if not (found_answer or react_node.num_retries >= num_retries or react_node.depth >= max_depth):
            add_to_queue.append(react_node)
        if propogate_final_answer_found and found_answer:
            add_to_queue.append(react_node)
        if not propogate_final_answer_found and found_answer:
            react_node.mgr.policy_final_answer = react_node.observation.value

    return add_to_queue

def _generate(nodes: Type[ReActNode], model: Type[GenerationWrapper], num_retries: int, max_depth: int, propogate_final_answer_found: bool = False):
    """
    Generates the next nodes in the chain given the current nodes and the model.

    Args:
        nodes: List of nodes to generate the next nodes from.
        model: Model to generate the next nodes.
        num_retries: Number of retries for each node.
        max_depth: Maximum depth of the chain.
        propogate_final_answer_found: Whether to propogate the final answer found in the chain. 
            This is to allow policy model to generate a final answer step and judge model to still judge the final answer step.
    """

    prompts = get_react_prompts(nodes)
    generations = [model.generate(prompt)[0] for prompt in prompts]
    next_nodes = post_process(prompts, generations, nodes, num_retries, max_depth, propogate_final_answer_found=propogate_final_answer_found)
    
    return next_nodes

def generate(
    input_data: List[dict],
    policy_model: Type[GenerationWrapper],
    num_retries: int,
    num_full_retries: int,
    max_depth: int,
    index: int
):
    """
    Generated a single chain of tool calls for each task in the input data. Optionally, the chain can be judged by a critic model.

    Important Note: This function handles only one task at a time. This is done to support multithreading multiple tasks concurrently. If you have multiple tasks, you should call this function for each task. 

    Args:
        input_data: List of tasks to generate tool calls for.
        policy_model: Model to generate tool calls.
        num_retries: Number of retries for each node in the chain.
        num_full_retries: Number of retries for the entire chain.
        max_depth: Maximum depth of the chain.
        should_judge: Whether to judge the generated chain.
        index: Global index of the task.
    """
    full_retries = 0

    while full_retries < num_full_retries:
        task_batch = input_data
        generation_queue, tree_list = pre_process(task_batch)

        generate_action_plan(tree_list, policy_model)

        # generate policy model full chain
        while generation_queue:
            curr_nodes: List[Type[ReActNode]] = [generation_queue.popleft() for _ in range(len(generation_queue))]
            next_nodes = _generate(curr_nodes, policy_model, num_retries, max_depth)
            generation_queue.extend(next_nodes)

        for tree in tree_list:
            if tree.policy_final_answer is not None:
                break
    
        full_retries += 1

    return tree_list[0].get_all_flattened_history()[0], index
