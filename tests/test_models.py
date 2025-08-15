import unittest
import os
import json
import sys

from model.models import LiteLLMWrapper, AFMWrapper
from utils.keystore import auth_litellm, auth_tools

class TestModelWrappers(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sampling_params = {
            "temperature": 0.7,
            "max_tokens": 1024,
            "top_p": 1.0
        }
        self.sample_messages = [
            {"role": "user", "content": "What is the capital of France?"}
        ]

        auth_litellm()
        auth_tools()
        
    def test_litellm_wrapper_gpt4o(self):
        """Test LiteLLMWrapper with GPT-4o model."""
        # Initialize the wrapper
        wrapper = LiteLLMWrapper("gpt-4o", self.sampling_params)
        
        # Generate a response
        response_text, _ = wrapper.generate(self.sample_messages)
        
        # Assert response is not empty
        self.assertIsNotNone(response_text)
        self.assertTrue(len(response_text) > 0)
        
        # Print out the response for manual verification
        print(f"\nLiteLLM GPT-4o Response: {response_text[:100]}...")
    
    def test_afm_wrapper(self):
        """Test AFMWrapper with real API."""
        # Initialize the wrapper
        wrapper = AFMWrapper("afm-text-074", self.sampling_params)
        
        # Generate a response
        response_text, _ = wrapper.generate(self.sample_messages)
        
        # Assert response is not empty
        self.assertIsNotNone(response_text)
        self.assertTrue(len(response_text) > 0)
        
        # Print out the response for manual verification
        print(f"\nAFM Response: {response_text[:100]}...")

    def test_tool_usage(self):
        """Test tool usage with both wrappers."""
        tool_messages = [
            {"role": "user", "content": "What is the current weather in San Francisco?"}
        ]
        
        # Test with LiteLLM wrapper
        litellm_wrapper = LiteLLMWrapper("gpt-4o", self.sampling_params)
        litellm_response, litellm_history = litellm_wrapper.generate(
            tool_messages.copy(), 
            tool_list=["current_weather"]
        )
        
        # Test with AFM wrapper
        afm_wrapper = AFMWrapper("afm-text-074", self.sampling_params)
        afm_response, afm_history = afm_wrapper.generate(
            tool_messages.copy(), 
            tool_list=["current_weather"]
        )

        print(afm_history)
        
        # Assert both responses contain tool usage
        print(f"\nLiteLLM Tool Test Response: {litellm_response[:100]}...")
        print(f"LiteLLM tool history has {len(litellm_history)} messages")
        
        print(f"\nAFM Tool Test Response: {afm_response[:100]}...")
        print(f"AFM tool history has {len(afm_history)} messages")
        
        # Check for tool calls in history
        has_litellm_tool_calls = any("tool_calls" in msg if isinstance(msg, dict) else False for msg in litellm_history)
        has_afm_tool_calls = any("tool_calls" in msg if isinstance(msg, dict) else False for msg in afm_history)
        
        # At least one of the models should have made tool calls
        self.assertTrue(has_litellm_tool_calls or has_afm_tool_calls, 
                        "Neither model made tool calls")

if __name__ == "__main__":
    unittest.main()
