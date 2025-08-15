
from model.models import LiteLLMWrapper
from model.types import GENERATION_STRATEGY


def load_model(model, generation_strategy, sampling_params):

    if generation_strategy == GENERATION_STRATEGY.LITELLM.value:
        return LiteLLMWrapper(model, sampling_params)
    else:
        raise ValueError(f"Unsupported model strategy: {generation_strategy}")
    
def load_sampling_params(args, strategy, tool_use_strategy):    
    
    if strategy in [generation_strategy.value for generation_strategy in GENERATION_STRATEGY]:
        sampling_params = {
            "max_tokens": args.policy_max_tokens,
            "temperature": args.policy_temperature,
        }

        if tool_use_strategy == "react":
            sampling_params["stop"] = args.policy_stop if args.policy_stop else None

        return sampling_params

    else:
        raise ValueError(f"Unsupported model strategy: {strategy}")
    