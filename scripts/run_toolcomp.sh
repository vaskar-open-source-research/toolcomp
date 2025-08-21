set -x
export PYTHONPATH=.

TOOL_USE_STRATEGY=native # choice between native or react
GENERATION_STRATEGY=litellm # choice between litellm

model_names=(
    anthropic/claude-4-sonnet-thinking-high
    anthropic/claude-4-opus-thinking-high
)

configs=(
    configs/claude-4-sonnet-thinking-high.json
    configs/claude-4-opus-thinking-high.json
)

for i in "${!model_names[@]}"; do
    MODEL_NAME="${model_names[$i]}"
    MODEL_CONFIG="${configs[$i]}"

    python main.py \
        --tool_use_strategy $TOOL_USE_STRATEGY \
        --config_file $MODEL_CONFIG \
        --input_file full_toolcomp_data_audited.jsonl \
        --num_retries 5 \
        --num_full_retries 3 \
        --max_depth 30 \
        --num_workers 32 \
        --output_dir outputs/$MODEL_NAME-$TOOL_USE_STRATEGY \
        --policy_generation_strategy $GENERATION_STRATEGY && \
    python grade/llm_grade.py \
        --input_file outputs/$MODEL_NAME-$TOOL_USE_STRATEGY/generations.json \
        --output_dir outputs/$MODEL_NAME-$TOOL_USE_STRATEGY \
        --num_workers 30
done
