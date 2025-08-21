# ToolComp Evaluation

This repository contains code for running and evaluating language models on the ToolComp benchmark, which tests a model's ability to use tools effectively.

<img src="imgs/diagram.png" alt="Figure for ToolComp data collection." width="100%"/>


<div align="center">

[📄 Paper](https://arxiv.org/abs/2501.01290) | [🤗 Final Answer Dataset](https://huggingface.co/datasets/vaskarnath/toolcomp) | [🤗 Process Supervision Dataset](https://huggingface.co/datasets/vaskarnath/toolcomp_process_supervision_eval) | [🏆 Chat Leaderboard](https://scale.com/leaderboard/tool_use_chat) | [🏆 Enterprise Leaderboard](https://scale.com/leaderboard/tool_use_enterprise)

</div>

## Prerequisites

Before running the evaluation, ensure you have:

1. Installed all required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up API keys via environment variables or a local .env file

## Running the Evaluation

The main evaluation script is located in the `scripts` directory. It runs the model against the ToolComp benchmark and then grades the results.

### Quick Start

To run the evaluation with default settings:

```bash
cd /path/to/toolcomp
bash scripts/run_toolcomp.sh
```

### Configure API Keys

This project looks for API keys in standard environment variables and also supports a local `.env` file (loaded automatically via `python-dotenv`). Create a `.env` file at the repo root by copying the example and filling in your values:

```bash
cp env.example .env
# then edit .env
```

Supported keys:

- LiteLLM proxy and providers
  - `LITE_LLM_API_KEY`
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `LLAMA_API_KEY`
  - `GEMINI_API_KEY`
- Tools
  - `SEARCHAPI_API_KEY` 
  - `ALPHA_VANTAGE_API_KEY`
  - `OPENWEATHER_API_KEY`
  - `WOLFRAM_ALPHA_API_KEY`
  - `SPHERE_ENGINE_API_KEY` (Sphere Engine Compilers; only needed if you use the code execution tool)

Notes:
- If `LITE_LLM_API_KEY` is set, it will be used as a fallback for missing `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` during runtime.

### Script Configuration

The `run_toolcomp.sh` script sets up the following:

1. Environment variables:
   - `PYTHONPATH=.` - Sets the Python path to include the current directory

2. Configuration parameters:
   - `MODEL_CONFIG` - The path to the model config to specify model and sampling configs
   - `INFERENCE_STRATEGY` - The inference strategy to use (options: native or react)

3. Runs the main evaluation:
   ```bash
   python main.py \
        --tool_use_strategy $TOOL_USE_STRATEGY \
        --config_file $MODEL_CONFIG \
        --input_file full_toolcomp_data_audited.jsonl \
        --num_retries 5 \
        --num_full_retries 3 \
        --max_depth 30 \
        --num_workers 32 \
        --output_dir outputs/$MODEL_NAME-$TOOL_USE_STRATEGY \
        --policy_generation_strategy $GENERATION_STRATEGY
   ```

4. Grades the evaluation results:
   ```bash
   python toolcomp/grade/llm_grade.py \
       --input_file toolcomp/outputs/$MODEL_NAME-$INFERENCE_STRATEGY/generations.json \
       --output_dir toolcomp/outputs/$MODEL_NAME-$INFERENCE_STRATEGY \
       --num_workers 30
   ```

### Customizing the Evaluation

To customize the evaluation, you can modify the following parameters in the script:

- `MODEL_CONFIG`: Change this to evaluate a different model
- `INFERENCE_STRATEGY`: Switch between "native" or "react" inference strategies
- `--policy_max_tokens`: Adjust the maximum token length for generation
- `--policy_temperature`: Modify the temperature setting for generation
- `--num_workers`: Change the number of parallel workers for processing
- `--max_depth`: Adjust the maximum depth of tool invocations

### Output

Evaluation results will be saved to the specified output directory:
```
toolcomp/outputs/$MODEL_NAME-$INFERENCE_STRATEGY/
```

This will include:
- The raw model generations
- Grading results 

## Process Supervision Evaluation

Evaluate LLM-as-judge performance on ToolComp process supervision labels (step- and plan-level pairwise comparisons).

### Quick Start

```bash
cd /path/to/toolcomp
bash scripts/run_toolcomp_process_supervision.sh
```

The script runs multiple models in parallel and writes outputs under `ps_outputs/$MODEL_NAME/`.

### Dataset

- **Source**: See the Process Supervision dataset linked above. Download it and place it at the repo root as `toolcomp_process_supervision_data.jsonl`, or pass a custom path via `--dataset`.

### Run a Single Model

```bash
python inference/llm_as_judge_inference.py \
  --dataset toolcomp_process_supervision_data.jsonl \
  --config_file configs/claude-4-sonnet-thinking-high.json \
  --out ps_outputs/claude-4-sonnet-thinking-high \
  --max_workers 32
```

You can swap `--config_file` with any file in `configs/` (e.g., `gpt-4o-native.json`, `gpt-4o-react.json`, `o3.json`, `gemini-2.5-pro.json`, `llama-4-scout.json`). If the batch script references config files you don’t have, update the arrays in `scripts/run_toolcomp_process_supervision.sh` to match the files present in `configs/`.

### CLI Flags

- **--dataset**: Path to the process supervision JSONL dataset.
- **--config_file** (required): Model/sampling config (LiteLLM format) from `configs/`.
- **--out**: Output directory. Recommended to set; results are saved inside.
- **--limit**: Optional cap on number of samples.
- **--max_workers**: Thread pool size for concurrent requests.

### Outputs

Each run writes to `ps_outputs/$MODEL_NAME/` (or your chosen `--out`):

- `llm_as_judge.jsonl`: One JSON object per sample, including prompts, raw model outputs, parsed labels, and the final decision.
- `metrics.json`: Summary metrics (also printed to stdout):
  - `total_accuracy`, `num_samples`
  - `action_plan_only_accuracy`, `action_plan_only_count`
  - `react_steps_accuracy`, `react_steps_count`
- `config.json`: Captures CLI args and the resolved sampling configuration used.

Notes:
- API keys are loaded via the same mechanism described above (LiteLLM providers). Ensure relevant keys are set.
- The script launches multiple models concurrently and waits for all to complete.

## Citation

If you found this work useful, please cite:

```
@article{nath2025toolcompmultitoolreasoning,
      title={ToolComp: A Multi-Tool Reasoning & Process Supervision Benchmark}, 
      author={Vaskar Nath and Pranav Raja and Claire Yoon and Sean Hendryx},
      year={2025},
      eprint={2501.01290},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2501.01290}, 
}
```