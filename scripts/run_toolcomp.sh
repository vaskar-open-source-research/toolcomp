set -x

export PYTHONPATH=.
export AWS_PROFILE=ml-worker

MODEL_NAME=openai/o3
MODEL_CONFIG=configs/o3.json
TOOL_USE_STRATEGY=native # choice between native or react
GENERATION_STRATEGY=litellm # choice between litellm

python main.py \
    --tool_use_strategy $TOOL_USE_STRATEGY \
    --config_file $MODEL_CONFIG \
    --input_file full_toolcomp_data_audited.jsonl \
    --num_retries 5 \
    --num_full_retries 3 \
    --max_depth 30 \
    --num_workers 64 \
    --output_dir outputs/$MODEL_NAME-$TOOL_USE_STRATEGY \
    --policy_generation_strategy $GENERATION_STRATEGY && \
python grade/llm_grade.py \
    --input_file outputs/$MODEL_NAME-$TOOL_USE_STRATEGY/generations.json \
    --output_dir outputs/$MODEL_NAME-$TOOL_USE_STRATEGY \
    --num_workers 30
