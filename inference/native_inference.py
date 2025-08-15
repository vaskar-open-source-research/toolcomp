from prompts.action_plan import get_prompt as get_action_plan_prompt
from prompts.native import get_prompt as get_func_calling_prompt
import json

def generate(
    input_data,
    policy_model,
    num_full_retries,
    index,
    apply_chat_template
):

    full_retries=0
    
    while full_retries < num_full_retries:
        task_batch = input_data[0]
       
        action_plan_prompts=get_action_plan_prompt(
            task_batch['prompt'], 
            task_batch['tools'], 
            task_batch['historical_date'], 
            apply_chat_template
        )
            
        action_plan_generations, _ = policy_model.generate(action_plan_prompts)
        task_batch.update({'action_plan': action_plan_generations})
        
        function_calling_prompts=get_func_calling_prompt(
            task_batch['prompt'],
            task_batch['tools'], 
            task_batch['action_plan'], 
            task_batch['historical_date'], 
            apply_chat_template
        )
        
        function_calling_generations, full_message_history = policy_model.generate(
            function_calling_prompts, 
            task_batch['tools'], 
            task_batch['historical_date']
        )
        
        if function_calling_generations:
            if '{"final_answer":' in function_calling_generations:
                break
        
        full_retries+=1

    task_batch.update({'policy_answer': function_calling_generations, 'full_message_history': full_message_history})

    return task_batch, index

    
