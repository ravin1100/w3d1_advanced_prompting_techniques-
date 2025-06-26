# Prompts Directory

This directory stores initial and optimized versions of prompts for each task.

## File Structure

For each task, the following files are created:

- `{task_id}_initial.txt`: The initial prompt template
- `{task_id}_initial.json`: Metadata for the initial prompt
- `{task_id}_v{n}.txt`: Optimized prompt versions
- `{task_id}_v{n}.json`: Metadata for optimized versions

## Metadata Format

The JSON metadata files contain:
```json
{
  "task_id": "task identifier",
  "version": "version identifier (initial or v1, v2, etc.)",
  "version_number": "numeric version (0 for initial)",
  "timestamp": "creation timestamp",
  "metrics": {
    "confidence": "model confidence score",
    "consistency": "self-consistency score",
    "correctness": "answer correctness score"
  }
}
``` 