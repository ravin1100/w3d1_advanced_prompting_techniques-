import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

class PipelineLogger:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "logs"
        self.prompts_dir = self.base_dir / "prompts"
        
        # Setup directory structure
        self.reasoning_paths_dir = self.logs_dir / "reasoning_paths"
        self.final_answers_dir = self.logs_dir / "final_answers"
        self.optimization_dir = self.logs_dir / "optimization"
        self.eval_dir = self.base_dir / "evaluation"
        
        # Create directories if they don't exist
        for directory in [self.reasoning_paths_dir, self.final_answers_dir, 
                         self.prompts_dir, self.optimization_dir, self.eval_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Setup logging with colored output for terminal
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / "pipeline.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()

    def _save_json(self, data: Dict[str, Any], file_path: Path) -> None:
        """Save data as JSON with proper formatting."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        self.logger.debug(f"Saved data to {file_path}")  # Changed to debug level

    def log_reasoning_path(self, task_id: str, path_data: Dict[str, Any]) -> None:
        """Log a single reasoning path for a task."""
        self.logger.info(f"Task {task_id}: Saving reasoning path...")
        file_path = self.reasoning_paths_dir / f"{task_id}.json"
        
        # Load existing paths if file exists
        existing_data = {}
        if file_path.exists():
            with open(file_path, 'r') as f:
                existing_data = json.load(f)
        
        # Update or create new data
        if not existing_data:
            existing_data = {
                "task_id": task_id,
                "timestamp": self._get_timestamp(),
                "reasoning_paths": []
            }
        
        existing_data["reasoning_paths"].append(path_data)
        self._save_json(existing_data, file_path)
        self.logger.info(f"Task {task_id}: Reasoning path saved successfully")

    def log_final_answer(self, task_id: str, answer_data: Dict[str, Any]) -> None:
        """Log the final answer for a task."""
        self.logger.info(f"Task {task_id}: Saving final answer...")
        file_path = self.final_answers_dir / f"{task_id}.json"
        
        final_data = {
            "task_id": task_id,
            "timestamp": self._get_timestamp(),
            "final_answer": answer_data
        }
        self._save_json(final_data, file_path)
        self.logger.info(f"Task {task_id}: Final answer saved successfully")

    def save_prompt_version(self, task_id: str, version: str, prompt: str, 
                          metrics: Optional[Dict[str, Any]] = None) -> None:
        """Save a new prompt version."""
        # Save prompt file
        prompt_file = self.prompts_dir / f"{task_id}_{version}.txt"
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        
        # Log optimization data
        opt_file = self.optimization_dir / f"{task_id}_log.json"
        opt_data = {
            "version": version,
            "timestamp": self._get_timestamp(),
            "prompt_file": str(prompt_file.name),
            "metrics": metrics or {}
        }
        
        existing_data = {}
        if opt_file.exists():
            with open(opt_file, 'r') as f:
                existing_data = json.load(f)
        
        if not existing_data:
            existing_data = {
                "task_id": task_id,
                "optimization_history": []
            }
        
        existing_data["optimization_history"].append(opt_data)
        self._save_json(existing_data, opt_file)

    def log_model_output(self, task_id: str, stage: str, output: Union[str, Dict[str, Any]],
                        metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log raw model output with metadata."""
        output_dir = self.logs_dir / "model_outputs" / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            "timestamp": self._get_timestamp(),
            "stage": stage,
            "output": output,
            "metadata": metadata or {}
        }
        
        # Create a semantic filename based on stage and attempt number
        attempt_num = len(list(output_dir.glob(f"{stage}_attempt_*.json"))) + 1
        file_path = output_dir / f"{stage}_attempt_{attempt_num}.json"
        
        self.logger.info(f"Task {task_id}: Processing {stage} (Attempt {attempt_num})")
        self._save_json(output_data, file_path)

    def log_error(self, task_id: str, error: Exception, context: Dict[str, Any]) -> None:
        """Log errors with context for debugging."""
        self.logger.error(f"Task {task_id}: Error occurred - {type(error).__name__}")
        error_dir = self.logs_dir / "errors"
        error_dir.mkdir(parents=True, exist_ok=True)
        
        error_data = {
            "timestamp": self._get_timestamp(),
            "task_id": task_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        
        file_path = error_dir / f"{task_id}_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self._save_json(error_data, file_path)
        self.logger.error(f"Task {task_id}: {error}", exc_info=True)

    def get_prompt_history(self, task_id: str) -> List[Dict[str, Any]]:
        """Retrieve prompt optimization history for a task."""
        opt_file = self.optimization_dir / f"{task_id}_log.json"
        if not opt_file.exists():
            return []
        
        with open(opt_file, 'r') as f:
            data = json.load(f)
            return data.get("optimization_history", []) 