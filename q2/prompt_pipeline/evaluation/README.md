# Evaluation Directory

This directory contains final evaluation metrics and analysis for each task run through the pipeline.

## Files

- `{task_id}_evaluation.json`: Contains final metrics for each task
- `summary.json`: Overall performance summary across all tasks
- `coherence_notes.md`: Analysis of prompt improvement patterns and effectiveness

## Metrics Format

The evaluation files contain:
```json
{
  "task_id": "task identifier",
  "timestamp": "evaluation timestamp",
  "metrics": {
    "confidence": "final confidence score",
    "consistency": "final self-consistency score",
    "correctness": "final answer correctness",
    "improvement": {
      "confidence_delta": "improvement in confidence",
      "consistency_delta": "improvement in consistency",
      "correctness_delta": "improvement in correctness"
    }
  },
  "prompt_versions": {
    "initial": "initial prompt used",
    "final": "final optimized prompt"
  }
}
``` 