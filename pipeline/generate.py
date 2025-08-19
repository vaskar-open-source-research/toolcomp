import os

from inference.react_inference import generate as react_generate
from inference.native_inference import generate as native_generate
from pipeline.utils import save_json
from model.utils import load_model
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import time


class GenerationPipeline:

    def __init__(self, args):
        self.args = args
    
    def prepare_inference_func(self, input_data, args):
            
        policy_model = load_model(args.policy_sampling_params['model'], args.policy_generation_strategy, args.policy_sampling_params)

        inference_func = react_generate
        inference_args = {
            "input_data": input_data,
            "policy_model": policy_model,
            "num_retries": args.num_retries,
            "num_full_retries": args.num_full_retries,
            "max_depth": args.max_depth,
        }
                
        return inference_func, inference_args
    
    def save_data(self, react_trees):
        generations_file_path = os.path.join(self.args.output_dir, f"generations.json")
        os.makedirs(self.args.output_dir, exist_ok=True)
        save_json(react_trees, generations_file_path)
       
    def iter_save_data(self, running_futures, react_trees, n_samples):
         with tqdm(total=n_samples) as pbar:
            while running_futures:
                indices = set()
                for i, future in enumerate(running_futures):
                    if future.done():
                        generation, _ = future.result()
                        react_trees.append(generation)
                        indices.add(i)
                        pbar.update(1)
                temp=[]
                if indices:
                    for fi, future in enumerate(running_futures):
                        if fi not in indices:
                            temp.append(future)
                    running_futures=temp
                    self.save_data(react_trees)

                time.sleep(60)

            self.save_data(react_trees)
            return react_trees

    def generate(self, input_data, react_trees):
        n_samples = len(input_data)
        args = self.args

        inference_func, inference_args = self.prepare_inference_func(input_data, args)
        executor=ThreadPoolExecutor(max_workers=args.num_workers)
        
        if self.args.tool_use_strategy == "react":
            
            futures = [executor.submit(
                inference_func, 
                [input_sample], 
                inference_args['policy_model'], 
                inference_args['num_retries'], 
                inference_args['num_full_retries'], 
                inference_args['max_depth'], 
                index) for index, input_sample in enumerate(input_data)]
                
        elif self.args.tool_use_strategy == "native":
            
            futures = [executor.submit(
                native_generate, 
                [input_sample], 
                inference_args['policy_model'], 
                inference_args['num_full_retries'], 
                index, args.apply_chat_template
                ) for index, input_sample in enumerate(input_data)]
        else:
            raise ValueError(f"Unsupported tool call format: {args.tool_call_format}")

        executor.shutdown(wait=False)
        running_futures = futures.copy()
        react_trees=self.iter_save_data(running_futures, react_trees, n_samples)
