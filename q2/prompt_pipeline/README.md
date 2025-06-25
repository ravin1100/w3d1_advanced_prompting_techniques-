# Prompt Engineering Pipeline

A comprehensive prompt engineering pipeline that implements Tree-of-Thought (ToT) reasoning, Self-Consistency, and automated prompt optimization using a local quantized LLM through Ollama.

## Features

- **Tree-of-Thought Reasoning**: Generates multiple reasoning paths for each task
- **Self-Consistency**: Aggregates multiple responses to find the most consistent answer
- **Automated Prompt Optimization**: Uses OPRO/TextGrad-style feedback loops to improve prompts
- **Local LLM Integration**: Works with Ollama using the DeepSeek-R1-Distill-Qwen-1.5B model
- **Comprehensive Logging**: Tracks all attempts, versions, and performance metrics

## Project Structure

```
prompt_pipeline/
├── README.md
├── tasks/                 # JSON/YAML files defining problem statements
├── prompts/               # Initial and optimized prompt versions
├── src/
│   ├── task_loader.py     # Load tasks from files
│   ├── model_runner.py    # Interface with Ollama
│   ├── tot_generator.py   # Generate reasoning paths
│   ├── aggregator.py      # Self-consistency logic
│   ├── optimizer.py       # OPRO/TextGrad-style prompt improvement
│   └── pipeline.py        # Main runner to coordinate everything
├── logs/                  # Store raw outputs and versions
└── evaluation/            # Final metrics and analysis
```

## Prerequisites

1. Python 3.8+
2. Ollama installed and running
3. DeepSeek-R1-Distill-Qwen-1.5B model pulled in Ollama

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install pyyaml
   ```
3. Ensure Ollama is installed and running:
   ```bash
   ollama run hf.co/lmstudio-community/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q4_K_M
   ```

## Usage

1. Create a task file in the `tasks` directory (JSON or YAML format):
   ```json
   {
     "id": "task_1",
     "problem_statement": "Your problem here",
     "expected_answer": "Expected solution (optional)"
   }
   ```

2. Run the pipeline:
   ```python
   from src.pipeline import PromptPipeline
   
   pipeline = PromptPipeline()
   results = pipeline.run_pipeline("task_1")
   ```

## Components

### Task Loader
- Loads task definitions from JSON/YAML files
- Supports multiple file formats
- Validates task structure

### Model Runner
- Interfaces with Ollama
- Handles model responses and errors
- Supports configurable parameters

### ToT Generator
- Implements Tree-of-Thought reasoning
- Generates multiple solution paths
- Tracks reasoning steps

### Aggregator
- Implements Self-Consistency
- Clusters similar answers
- Calculates confidence scores

### Optimizer
- Implements automated prompt optimization
- Uses feedback loops to improve prompts
- Tracks prompt versions and performance

### Pipeline
- Coordinates all components
- Handles logging and evaluation
- Provides a simple interface

## Evaluation Metrics

The pipeline tracks several metrics:
- Confidence: How confident the model is in its answer
- Consistency: How many reasoning paths lead to similar answers
- Correctness: How close the answer is to the expected solution (if provided)

## Logging

All runs are logged with:
- Timestamps
- Reasoning paths
- Prompt versions
- Performance metrics
- Final results

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License 