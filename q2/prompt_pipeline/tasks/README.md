# Tasks Directory

This directory contains JSON and YAML files that define problem statements for the prompt engineering pipeline.

## File Format

Tasks should be defined in either JSON or YAML format with the following structure:

```json
{
  "task_id": "unique_task_id",
  "domain": "category of the task (e.g., math, logic, coding)",
  "problem": "The actual problem statement or question",
  "expected_answer": "The expected solution (optional)"
}
```

## Example Files

- `example_tasks.json`: Contains a set of example tasks across different domains
- Individual task files (e.g., `task_01.json`): Generated from example tasks for pipeline processing 