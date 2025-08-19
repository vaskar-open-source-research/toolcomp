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

    with open(args.config_file) as f:
        config = json.load(f)
    args.policy_sampling_params = config
    print(f"config: {config}")

    # save args + config to output dir
    with open(os.path.join(args.output_dir, "config.json"), "w") as f:
        json.dump({"args": args.__dict__, "config": config}, f)

    react_trees, input_data = load_data(args)
    pipeline = GenerationPipeline(args)
    pipeline.generate(input_data, react_trees)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ReAct Generation Pipeline")
    parser.add_argument(
        "--policy_generation_strategy",
        type=str,
        choices=[strategy.value for strategy in GENERATION_STRATEGY],
        default=GENERATION_STRATEGY.LITELLM.value,
        help="The generation strategy to use for the policy model",
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

    # policy model config
    parser.add_argument(
        "--config_file",
        type=str,
        help="The config file to use for generation",
        required=True,
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
