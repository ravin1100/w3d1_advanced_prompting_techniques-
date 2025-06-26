# Logs Directory

This directory stores detailed logs of pipeline execution, including raw outputs, versions, and prompt attempts.

## Directory Structure

- `final_answers/`: Final answers generated for each task
- `optimization/`: Logs from the prompt optimization process
- `prompts/`: Raw prompt attempts and variations
- `reasoning_paths/`: Tree-of-Thought reasoning paths generated
- `runs/`: Complete run logs with all pipeline stages

## Log Format

Each log file is in JSON format and includes:
- Timestamp
- Task ID
- Stage/Component identifier
- Input/Output data
- Error information (if any)
- Performance metrics
- Metadata specific to the pipeline stage

## File Naming Convention

Log files follow the pattern:
`{task_id}_{timestamp}_{stage}.json`

Example:
`task_01_20240315_123456_reasoning_paths.json` 