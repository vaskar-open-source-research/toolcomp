"""
ReAct Generation Pipeline
"""

import argparse
import json
import os
import pandas as pd

from pipeline.generate import GenerationPipeline
from model.types import GENERATION_STRATEGY
from model.utils import load_sampling_params
from utils.keystore import auth_tools, auth_litellm

def load_data(args):
    with open(args.input_file) as f:
        if 'jsonl' in args.input_file:
            input_data = [json.loads(line) for line in f]
        else:
            input_data = json.load(f)

    input_data = [data for data in input_data if data['prompt']]

    path=os.path.join(args.output_dir, f"native_generations.json")
    
    react_trees = []
    if os.path.exists(path):
        with open(path) as f:
            react_trees = json.load(f)
        queries=[data['prompt'] for data in react_trees]
        input_data = [data for data in input_data if data['prompt'] not in queries]

    return react_trees, input_data

def main(args):

    auth_tools()
    auth_litellm()

    policy_sampling_params = load_sampling_params(args, args.policy_generation_strategy, args.tool_use_strategy)
    args.policy_sampling_params = policy_sampling_params

    react_trees, input_data = load_data(args)
    pipeline = GenerationPipeline(args)
    pipeline.generate(input_data, react_trees)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ReAct Generation Pipeline")
    parser.add_argument(
        "--policy_model_str",
        type=str,
        default="fireworks-ai/firefunction-v1",
        help="The model string to use for generation",
    )
    parser.add_argument(
        "--policy_generation_strategy",
        type=str,
        choices=[strategy.value for strategy in GENERATION_STRATEGY],
        default=GENERATION_STRATEGY.LITELLM.value,
        help="The generation strategy to use for the policy model",
    )
    parser.add_argument(
        "--policy_max_tokens",
        type=int,
        default=10240,
        help="The maximum number of tokens to generate for the policy",
    )
    parser.add_argument(
        "--policy_temperature",
        type=float,
        default=0.5,
        help="The temperature to use for the policy sampling",
    )
    parser.add_argument(
        "--policy_stop",
        type=str,
        nargs="+",
        default=[],
        help="The stop strings to use for the policy sampling",
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default="scripts/data/test/small_test.json",
        help="The file to read the input from",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="scripts/data/test/",
        help="The directory to save the output",
    )
    parser.add_argument(
        "--num_retries",
        type=int,
        default=3,
        help="The number of times to retry the generation if it fails",
    )
    parser.add_argument(
        "--num_full_retries",
        type=int,
        default=1,
        help="The number of times to retry the generation if it fails",
    )
    
    # inference strategy
    parser.add_argument(
        "--tool_use_strategy",
        type=str,
        default="native",
        help="The tool use strategy to use for generation",
        choices=["native", "react"],
    )


    # hyperparameters for dataset loader
    parser.add_argument(
        "--num_workers", type=int, default=1, help="The batch size for inference"
    )
    # hyperparameters for generation
    parser.add_argument(
        "--max_depth",
        type=int,
        default=10,
        help="The maximum number of tool invocations to use for generation",
    )
    parser.add_argument(
        "--apply_chat_template",
        action="store_true",
        help="Whether to apply the chat template to the generation",
    )

    args = parser.parse_args()
    # make output dir
    os.makedirs(args.output_dir, exist_ok=True)
    main(args)
