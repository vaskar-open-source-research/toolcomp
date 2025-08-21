set -x
export PYTHONPATH=.

model_names=(
    anthropic/claude-4.1-sonnet-thinking-high
    anthropic/claude-4.1-opus-thinking-high
)

configs=(
    configs/claude-4.1-sonnet-thinking-high.json
    configs/claude-4.1-opus-thinking-high.json
)

pids=()
for i in "${!model_names[@]}"; do
    MODEL_NAME="${model_names[$i]}"
    CONFIG_FILE="${configs[$i]}"
    python inference/llm_as_judge_inference.py \
        --dataset toolcomp_process_supervision_data.jsonl \
        --out "ps_outputs/$MODEL_NAME" \
        --max_workers 32 \
        --config_file "$CONFIG_FILE" &
    pids+=($!)
done

echo $pids

# Wait for all background processes to finish
for pid in "${pids[@]}"; do
    wait "$pid"
done
