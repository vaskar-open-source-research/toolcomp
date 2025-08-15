set -x

export PYTHONPATH=.
export AWS_PROFILE=ml-worker

MODEL_NAME=openai/gpt-4o
TOOL_USE_STRATEGY=native # choice between native or react
GENERATION_STRATEGY=litellm # choice between litellm or afm

python main.py \
    --tool_use_strategy $TOOL_USE_STRATEGY \
    --policy_model_str $MODEL_NAME \
    --policy_max_tokens 8096 \
    --policy_temperature 1.0 \
    --policy_stop "End Action" \
    --policy_stop "End Action\n" \
    --policy_stop "\nEnd Action" \
    --input_file "path/to/data" \
    --num_retries 5 \
    --num_full_retries 3 \
    --max_depth 30 \
    --num_workers 64 \
    --output_dir outputs/$MODEL_NAME-$TOOL_USE_STRATEGY \
    --policy_generation_strategy $GENERATION_STRATEGY && \
python grade/llm_grade.py \
    --input_file outputs/$MODEL_NAME-$TOOL_USE_STRATEGY/native_generations.json \
    --output_dir outputs/$MODEL_NAME-$TOOL_USE_STRATEGY \
    --num_workers 30
