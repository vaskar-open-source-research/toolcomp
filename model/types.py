from enum import Enum


class GENERATION_STRATEGY(Enum):
    """
    Enum for model load strategy
    """
    OPEN_AI_COMPLETION = 'open_ai_completion'
    LITELLM = 'litellm'
