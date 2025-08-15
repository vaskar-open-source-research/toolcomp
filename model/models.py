import os
import json
import litellm
from utils.keystore import auth_litellm
from tools.helper import get_all_tools_mapping
import OpenSSL
import requests
import time
import random


class GenerationWrapper:
    """Base wrapper for LLM generation."""
    
    def __init__(self, model, sampling_params):
        self.model = model
        self.sampling_params = sampling_params
        self.tool_mapping = get_all_tools_mapping()
    
    def generate(self, prompt, tool_list=[], historical_date=None):
        """Generate text with the model."""
        pass


class LiteLLMWrapper(GenerationWrapper):
    """LiteLLM implementation for tool use."""
    
    def __init__(self, model, sampling_params):
        super().__init__(model, sampling_params)

        api_key = auth_litellm()
        litellm.api_base = "https://litellm.ml-serving-internal.scale.com"
    
    def _parse_functions(self, response_message):
        """Parse function/tool calls from response."""
        tool_calls = (
            response_message.tool_calls if hasattr(response_message, "tool_calls") else None
        )
        return tool_calls
    
    def _hit_litellm(self, messages, tools=None, tool_choice='auto'):
        """Make a request to LiteLLM API."""
        max_retries_rate_limit = 15
        max_retries_other = 3
        base_delay = 15  # starting delay in seconds
        retry_count_rate_limit = 0
        retry_count_other = 0
        
        while retry_count_rate_limit < max_retries_rate_limit or retry_count_other < max_retries_other:
            try:
                litellm.drop_params = True
                response = litellm.completion(
                    model=self.model,
                    messages=messages,
                    tools=tools if tools else None,
                    tool_choice=tool_choice if tools else None,
                    max_tokens=self.sampling_params.get('max_tokens', 1024),
                    temperature=self.sampling_params.get('temperature', 0.7),
                    stop=self.sampling_params.get('stop', None),
                    thinking={
                        "effort" : "high"
                    }
                )
                return response.choices[0].message
            except Exception as e:
                error = e
                
                # Only apply exponential backoff for rate limit errors
                if "litellm.RateLimitError" in str(e):
                    retry_count_rate_limit += 1
                    if retry_count_rate_limit >= max_retries_rate_limit:
                        break
                    # Calculate delay with exponential backoff and jitter
                    delay = base_delay * (2 ** (retry_count_rate_limit - 1))  # exponential increase
                    delay = delay * (0.5 + random.random())  # add jitter (50-150% of delay)
                    if "litellm.RateLimitError" in str(e):
                        print(f"LiteLLM rate limit error, retrying with backoff in {delay:.2f}s (attempt {retry_count_rate_limit}/{max_retries_rate_limit})")

                else:
                    print(e)
                    retry_count_other += 1
                    if retry_count_other >= max_retries_other:
                        break
                    # For other errors, use a simple fixed delay
                    delay = 15
                    print(f"LiteLLM request failed, retrying in {delay}s (attempt {retry_count_other}/{max_retries_other})")
                
                time.sleep(delay)
        
        raise Exception(f"Max retries ({max_retries_rate_limit}) exceeded: {error}")
    
    def _call_tools(self, messages, tool_calls, tool_list, historical_date=None):
        """Call the tools and add responses to messages."""
        available_functions = {tool: self.tool_mapping[tool].parse_and_hit_tool for tool in tool_list}
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            if function_name not in available_functions:
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": f"The tool you are trying to call {function_name} is not available.",
                    }
                )
                continue
            
            function_to_call = available_functions[function_name]
            function_args = tool_call.function.arguments
            function_response = function_to_call(function_args, historical_date)
            
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
        return messages

    def _generate(self, messages, tool_list=[], historical_date=None):
        """Generate a response with tool use."""
        tools = [self.tool_mapping[tool].get_gpt_spec() for tool in tool_list if tool in tool_list]
        response_message = self._hit_litellm(messages, tools, tool_choice='auto')
        
        if not tools:
            return response_message['content'], messages
        
        tool_calls = self._parse_functions(response_message)
        
        messages.append(response_message)  # extend conversation with assistant's reply
        max_steps = 100  # limit the number of tool call iterations
        steps = 0
        
        while tool_calls and steps < max_steps:
            messages = self._call_tools(messages, tool_calls, tool_list, historical_date)
            response_message = self._hit_litellm(messages, tools, tool_choice='auto')
            tool_calls = self._parse_functions(response_message)
            
            messages.append(response_message)
            steps += 1

        messages = [
            message.dict() if not isinstance(message, dict) else message for message in messages
        ]
        
        return messages[-1]["content"], messages

    def generate(self, prompt, tool_list=[], historical_date=None):
        """Generate a response with tool use, with retries."""
        max_retries = 5
        while True:
            try:
                messages = prompt.copy()
                final_output_text, full_message_history = self._generate(messages, tool_list, historical_date)
                break
            except Exception as e:
                max_retries -= 1
                if max_retries == 0:
                    print(f"Error in generation: {e}")
                    return str(e), prompt
        
        return final_output_text, full_message_history
