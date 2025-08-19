set -x

export PYTHONPATH=.
export AWS_PROFILE=ml-worker

MODEL_NAME=openai/gpt-5

model_names=(
    # openai/gpt-5
    # anthropic/claude-4.1-thinking-high
    openai/o3
    # gemini/gemini-2.5-pro
)

configs=(
    # configs/gpt-5.json
    # configs/claude-4.1-thinking-high.json
    configs/o3.json
    # configs/gemini-2.5-pro.json
)

pids=()
for i in "${!model_names[@]}"; do
    MODEL_NAME="${model_names[$i]}"
    CONFIG_FILE="${configs[$i]}"
    python inference/llm_as_judge_inference.py \
        --dataset toolcomp_process_supervision_data.jsonl \
        --out "ps_outputs/$MODEL_NAME" \
        --max_workers 64 \
        --config_file "$CONFIG_FILE"
    pids+=($!)
done

echo $pids

# Wait for all background processes to finish
for pid in "${pids[@]}"; do
    wait "$pid"
done

# for i in "${!model_names[@]}"; do
#     MODEL_NAME="${model_names[$i]}"
#     CONFIG_FILE="${configs[$i]}"
#     python inference/llm_as_judge_inference.py \
#         --dataset toolcomp_process_supervision_data.jsonl \
#         --out "ps_outputs/$MODEL_NAME" \
#         --max_workers 256 \
#         --config_file "$CONFIG_FILE"
# done

# python inference/llm_as_judge_inference.py \
#     --dataset toolcomp_process_supervision_data.jsonl \
#     --out ps_outputs/$MODEL_NAME \
#     --max_workers 256 \
#     --config_file configs/gpt-5.json
