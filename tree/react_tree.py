# Lightweight implementation of tree node for generating ReAct tool chains
import json
from typing import Dict, List, Optional, Type

from termcolor import colored
from tools.helper import get_all_tools_mapping
import re

class ReActTreeManager:

    def __init__(self, query: str, tools_available: List[str], action_plan_label: int = None, revisied_action_plan_label: int = None):
        self.root = ReActNode(None, None, None, None, is_psuedo_root=True)
        self.root._set_mgr(self)

        # rewrite_root is required if action plan is revised
        self.rewrite_root = ReActNode(None, None, None, None, is_psuedo_root=True)
        self.rewrite_root._set_mgr(self)

        self.generation_status: str = "Pending"
        self.tools_available: List[str] = tools_available
        self.query: str = query
        self.revised_action_plan: Optional[str] = None
        self.revised_action_plan_label: Optional[int] = revisied_action_plan_label
        self.revised_action_plan_gt: Optional[int] = None
        self.action_plan: Optional[str] = None
        self.action_plan_label: Optional[int] = action_plan_label
        self.action_plan_gt: Optional[int] = None
        self.action_plan_correct: Optional[bool] = None
        self.metadata: Dict[str, str] = {}
        self.ground_truth: Optional[str] = None
        self.policy_final_answer: Optional[str] = None
        self.critic_final_answer: Optional[str] = None
        self.full_retries: int = 0

        self.better_action_plan: Optional[List[str]] = None
        self.raw_pairwise_judge_output: Optional[List[str]] = None
        self.pairwise_judge_prompt: Optional[List[str]] = None

    def to_json(self):
        json = {
            "generations": self.root.to_json(),
            "rewrite_generations": self.rewrite_root.to_json(),
            "generation_status": self.generation_status,
            "query": self.query,
            "tools_available": [tool for tool in self.tools_available],
            "action_plan": self.action_plan,
            "revised_action_plan": self.revised_action_plan,
            "revised_action_plan_label": self.revised_action_plan_label,
            "revised_action_plan_gt": self.revised_action_plan_gt,
            "action_plan_correct": self.action_plan_correct,
            "action_plan_label": self.action_plan_label,
            "action_plan_gt": self.action_plan_gt,
            "metadata": self.metadata,
            "policy_final_answer": self.policy_final_answer,
            "critic_final_answer": self.critic_final_answer,
            "better_action_plan": self.better_action_plan,
            "raw_pairwise_judge_output": self.raw_pairwise_judge_output,
            "pairwise_judge_prompt": self.pairwise_judge_prompt,
        }

        if self.ground_truth is not None:
            json["ground_truth"] = self.ground_truth
        
        return json

    def add_metadata(self, key, value):
        self.metadata[key] = value
    
    def add_action_plan(self, action_plan):
        self.action_plan = action_plan
    
    def add_revised_action_plan(self, revised_action_plan):
        self.revised_action_plan = revised_action_plan
        self.action_plan_correct = False
    
    def get_all_flattened_history(self):
        
        full_generations = []

        leaves = self.root.get_all_leaves()
        generations = []
        policy_answer = self.policy_final_answer
        
        for leaf in leaves:
            history = leaf.generate_history_json()
            generations.append({
                "history": history,
                "answer_found": leaf.answer_found,
                "final_answer": leaf.final_answer,
                "depth": leaf.depth,
            })
        flattened_info = {
            "query": self.query,
            "policy_answer": policy_answer,
            "answer": self.ground_truth,
            "tools": self.tools_available,
            "action_plan": self.action_plan,
            "full_message_history": generations,
        }
        full_generations.append(flattened_info)
        return full_generations

    def get_reward_model_data(self):
        return {
            "preferred": self.extract_orm_preferred(),
            "dispreferred": self.extract_orm_dispreferred(),
            "prm": self.extract_prm(),
            "query": self.query,
            "tools_available": self.tools_available,
            "action_plan": self.action_plan,
            "action_plan_correct": self.action_plan_correct,
            "revised_action_plan": self.revised_action_plan,
        }
    
    def extract_orm_dispreferred(self):
        dispreferred = []
        dispreferred.append({
            "action_plan": self.action_plan,
        })
        node = self.root
        while node.children:
            selected_node = None
            for child in node.children:
                if not child.pruned:
                    selected_node = child
                    break
            step = {
                "thought": selected_node.thought.value,
                "action": selected_node.action.value,
                "action_input": selected_node.action_input.value,
                "observation": selected_node.observation.value,
            }
            dispreferred.append(step)
            node = selected_node

        return dispreferred

    def extract_orm_preferred(self):
        preferred = []
        preferred.append({
            "action_plan": self.action_plan if self.action_plan_correct else self.revised_action_plan,
        })
        node = self.root if self.rewrite_root is None else self.rewrite_root
        while node.children:
            selected_node = None
            for child in node.children:
                if not child.pruned:
                    selected_node = child
                    break
            if selected_node.rewrite_node is not None:
                selected_node = selected_node.rewrite_node
            step = {
                "thought": selected_node.thought.value,
                "action": selected_node.action.value,
                "action_input": selected_node.action_input.value,
                "observation": selected_node.observation.value,
            }
            preferred.append(step)
            node = selected_node
        
        return preferred

    def extract_prm(self):
        prm = []
        running_history = []
        if not self.action_plan_correct:
            prm.append(
                {
                    "dispreferred": {
                        "action_plan": self.action_plan,
                    },
                    "preferred": {
                        "action_plan": self.revised_action_plan,
                    },
                    "running_history": [],
                }
            )
            running_history.append(self.revised_action_plan)
        else:
            running_history.append(self.action_plan)
        
        node = self.root if self.rewrite_root is None else self.rewrite_root
        for child in node.children:
            if not child.pruned:
                selected_node = child
                break

        if not node.children:
            return prm

        while True:
            dispreferred_step = {
                "thought": selected_node.thought.value,
                "action": selected_node.action.value,
                "action_input": selected_node.action_input.value,
                "observation": selected_node.observation.value,
            }

            if selected_node.rewrite_node is not None:
                preferred_step = {
                    "thought": selected_node.rewrite_node.thought.value,
                    "action": selected_node.rewrite_node.action.value,
                    "action_input": selected_node.rewrite_node.action_input.value,
                    "observation": selected_node.rewrite_node.observation.value,
                }
                prm.append({
                    "dispreferred": dispreferred_step,
                    "preferred": preferred_step,
                    "running_history": running_history.copy(),
                })
                selected_node = selected_node.rewrite_node
                    
                running_history.append(preferred_step)
            else:
                running_history.append(dispreferred_step)

            if not selected_node.children:
                break
            else:
                for child in selected_node.children:
                    if not child.pruned:
                        selected_node = child
                        break
        return prm


class ReActNode:

    def __init__(
        self, thought, action, action_input, observation, is_psuedo_root: bool = False
    ):

        # core react steps
        self.thought: Type[ReActStep] = thought
        self.action: Type[ReActStep] = action
        self.action_input: Type[ReActStep] = action_input
        self.observation: Type[ReActStep] = observation

        # judge rewrites
        self.rewrite_node: Optional[Type[ReActNode]] = None
        self.thought_label: Optional[str] = None
        self.action_label: Optional[str] = None
        self.action_input_label: Optional[str] = None
        self.ready_to_judge: bool = False
        self.judge_reasoning: Optional[str] = None
        
        self.better_child: Optional[int] = None
        self.raw_pairwise_judge_output: Optional[str] = None
        self.pairwise_judge_prompt: Optional[str] = None

        # gt labels
        self.judge_prompt: Optional[str] = None
        self.raw_judge_output: Optional[str] = None
        self.thought_gt: Optional[str] = None
        self.action_gt: Optional[str] = None
        self.action_input_gt: Optional[str] = None


        # pointers
        self.parent: Optional[Type[ReActNode]] = None
        self.children: List[Type[ReActNode]] = []

        # if this node is a terminal node where the final answer is found
        self.answer_found: bool = False
        self.final_answer: str = ""

        # tracking if this node has been pruned
        self.pruned: bool = False
        self.pruned_reason: str = ""

        # metadata
        self.metadata: Dict[str, str] = (
            {}
        )  # generic place to capture additional ad-hoc metrics/metadata
        self.num_retries: int = 0
        self.num_total_chain_retries: int = 0
        self.num_judge_retries: int = 0
        self.depth: int = 0
        self.errors: List[str] = []
        self.rewrite_errors: List[str] = []

        # pseudo-root node
        # we want a pseudo-root node to be able to store the root nodes of the tree
        self.is_pseudo_root = is_psuedo_root

        # search metadata
        self.expanded = False
        self.N = 0
        self.Q = 0
        self.llm_score = 0

    def _inherit_as_child(self, node):
        node._set_depth(self.depth + 1)
        node.num_total_chain_retries = self.num_total_chain_retries
        node.mgr = self.mgr

    def add_child(self, node):
        node.parent = self
        self._inherit_as_child(node)
        self.children.append(node)
        # potentially add ready_to_judge = true

    def add_rewrite_node(self, node):
        self.rewrite_node = node
        node._set_mgr(self.mgr)
        node.depth = self.depth
        node.parent = self.parent

    def _set_mgr(self, mgr):
        self.mgr = mgr

    def _set_depth(self, depth):
        self.depth = depth

    def update_errors(self, error: str):
        self.num_retries += 1
        self.num_total_chain_retries += 1
        self.errors.append(error)
    
    def update_judge_errors(self, error: str):
        self.num_judge_retries += 1
        self.rewrite_errors.append(error)

    def print(self, should_print: bool = False):
        if self.rewrite_node is not None:
            return self.rewrite_node.print(should_print)
        else:
            val = (
                self.thought.print(should_print) 
                + "\n"
                + self.action.print(should_print)
                + "\n"
                + self.action_input.print(should_print) 
                + "\n"
                + self.observation.print(should_print) 
            )
        return val

    def generate_history(self, should_print: bool = False):
        val = ""
        curr = self
        while not curr.is_pseudo_root:
            val = curr.print(should_print) + "\n\n" + val
            curr = curr.parent
        return val
    
    def generate_history_json(self):
        curr = self
        history = []
        while not curr.is_pseudo_root:
            full_json = curr.to_json()
            react_json = {
                "thought": full_json["thought"],
                "action": full_json["action"],
                "action_input": full_json["action_input"],
                "observation": full_json["observation"],
            }
            history = [react_json] + history
            curr = curr.parent
        return history

    def get_all_ancestors(self):
        ancestors = []
        curr = self.parent
        while curr is not None and not curr.is_pseudo_root:
            ancestors.append(curr)
            curr = curr.parent
        return ancestors[::-1]

    def get_root_node(self):
        if self.parent.is_pseudo_root:
            return self
        else:
            return self.parent.get_root_node()

    def add_metadata(self, key, value):
        self.metadata[key] = value

    def update_judge_labels(self, labels):
        self.thought_label, self.action_label, self.action_input_label = labels

    def to_json(self):
        if self.is_pseudo_root:
            return {
                "children": [child.to_json() for child in self.children],
                "metadata": self.metadata,
                "num_retries": self.num_retries,
                "errors": self.errors,
                "rewrite_node": self.rewrite_node.to_json() if self.rewrite_node is not None else None,
                "depth": self.depth,
                "better_child": self.better_child,
                "raw_pairwise_judge_output": self.raw_pairwise_judge_output,
                "pairwise_judge_prompt": self.pairwise_judge_prompt,
            }
        else:
            return {
                "thought": self.thought.value,
                "action": self.action.value,
                "action_input": self.action_input.value,
                "observation": self.observation.value,
                "judge_prompt": self.judge_prompt,
                "raw_judge_output": self.raw_judge_output,
                "thought_label": self.thought_label,
                "action_label": self.action_label,
                "action_input_label": self.action_input_label,
                "better_child": self.better_child,
                "raw_pairwise_judge_output": self.raw_pairwise_judge_output,
                "pairwise_judge_prompt": self.pairwise_judge_prompt,
                "thought_gt": self.thought_gt,
                "action_gt": self.action_gt,
                "action_input_gt": self.action_input_gt,
                "judge_reasoning": self.judge_reasoning,
                "children": [child.to_json() for child in self.children],
                "rewrite_node": self.rewrite_node.to_json() if self.rewrite_node is not None else None,
                "metadata": self.metadata,
                "num_retries": self.num_retries,
                "depth": self.depth,
                "errors": self.errors,
                "rewrite_errors": self.rewrite_errors,
                "final_answer": self.observation.value if self.answer_found else None,
                "final_answer_found": self.answer_found,
                "pruned": self.pruned,
                "pruned_reason": self.pruned_reason,
            }

    def get_all_leaves(self):
        leaves = []
        if not self.children:
            leaves.append(self)
            if self.rewrite_node is not None:
                leaves.extend(self.rewrite_node.get_all_leaves())
        else:
            for child in self.children:
                leaves.extend(child.get_all_leaves())
        return leaves
    
    def prune(self, reason: str):
        self.pruned = True
        self.pruned_reason = reason


class ReActStep:

    def __init__(self, node_type=None, value=None):
        self.node_type = node_type  # "Thought", "Action", "Action Input", "Observation"
        self.value = value  # The string value of the node
        self.step_metadata = {}

    def print(self, should_print=False):
        color_converter = {
            "Thought": "red",
            "Action": "blue",
            "Action Input": "cyan",
            "Final Answer": "green",
            "Observation": "blue",
        }
        if self.node_type == "Observation":
            return f"Observation: {self.value}\n"
        elif self.node_type == "Action Input":
            if should_print:
                print(
                    colored(
                        f"{self.node_type}: {self.value}\nEnd Action",
                        color=color_converter[self.node_type],
                    )
                )
            return f"{self.node_type}: {self.value}\nEnd Action"
        else:
            if should_print:
                print(
                    colored(
                        f"{self.node_type}: {self.value}",
                        color=color_converter[self.node_type],
                    )
                )
            return f"{self.node_type}: {self.value}"

    def add_metadata(self, key, value):
        self.step_metadata[key] = value


def process_policy_output(raw_string, historical_date=None):

    raw_string = raw_string.strip()
    # find the first "Thought:"
    thought_idx = raw_string.find("Thought:")
    action_idx = raw_string.find("Action:")
    action_input_idx = raw_string.find("Action Input:")
    end_action_idx = raw_string.find("End Action")

    if thought_idx == -1:
        raise ValueError(f"Invalid raw string: please begin with 'Thought:'. Got: {raw_string}")
    
    if action_idx == -1:
        raise ValueError(f"Invalid raw string: please include 'Action:' after generating your thought step. Got: {raw_string}")
    
    if action_input_idx == -1:
        raise ValueError(f"Invalid raw string: please include 'Action Input:' after generating your action step. Got: {raw_string}")
    
    if end_action_idx == -1:
        raise ValueError(f"Invalid raw string: please include 'End Action' in a new line after generating your action input step. Got: {raw_string}")


    thought_string = raw_string[thought_idx + len("Thought:") : action_idx].strip().replace("\n", " ")
    action_string = raw_string[action_idx + len("Action:") : action_input_idx].strip().replace("\n", " ")
    action_input_string = raw_string[action_input_idx + len("Action Input:") : end_action_idx].strip().replace("\n", " ")

    nodes = [
        ReActStep("Thought", thought_string),
        ReActStep("Action", action_string),
        ReActStep("Action Input", action_input_string.strip('```').strip('json').strip('python')),
    ]

    # check node is not None
    for node in nodes:
        if node is None:
            raise ValueError(f"Invalid raw string: {raw_string} with nodes list: {nodes}")

    thought_node = nodes[0]
    action_node = nodes[1]
    action_input_node = nodes[2]

    try:
        observation_step, found_answer = get_observation_step(
            action_node, action_input_node, historical_date
        )
    except Exception as e:
        raise ValueError(f"Error in getting observation step: {str(e)} with action: {action_node.value} and action input: {action_input_node.value}")
    
    react_node = ReActNode(thought_node, action_node, action_input_node, observation_step)

    if found_answer:
        react_node.answer_found = True
        react_node.final_answer = observation_step.value

    return react_node, found_answer

def extract_json_from_text(text):
    # Regex pattern to find text within triple backticks labeled as json
    pattern = r"```json\s*(.*?)\s*```"
    
    # Using re.DOTALL to make '.' match newlines as well
    matches = re.findall(pattern, text, re.DOTALL)
    
    return matches

def extract_labels(labels_string):
    labels_string = extract_json_from_text(labels_string)[-1]
    d=json.loads(labels_string)
    labels = [d['thought'], d['action'], d['action_input']]
    return labels

def get_observation_step(action_node, action_input_node, historical_date=None):
    if type(action_input_node.value) == str:
        if "python_interpreter" in action_node.value:    
            args = json.loads(action_input_node.value.replace('\n', '~!`>!~'))
            args["code"] = args["code"].replace('~!`>!~', '\n')
        else:
            args = json.loads(action_input_node.value)
    else:
        args = action_input_node.value
    found_answer = False

    if action_node.value == "finish":
        final_answer = args["answer"]
        observation_node = ReActStep("Observation", final_answer)
        found_answer = True
    else:
        tool_map = get_all_tools_mapping()
        tool = tool_map[action_node.value]
        if historical_date:
            args["historical_date"] = historical_date
        result = tool.call(args)
        observation_node = ReActStep("Observation", result)

    return observation_node, found_answer
