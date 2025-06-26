import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from .utils.logging_utils import PipelineLogger

logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self, prompts_dir: Optional[str] = None, base_dir: str = "."):
        self.logger = PipelineLogger(base_dir=base_dir)
        self.prompts_dir = Path(prompts_dir) if prompts_dir else self.logger.prompts_dir
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
    def save_initial_prompt(self, task_id: str, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save the initial prompt for a task."""
        prompt_file = self.prompts_dir / f"{task_id}_initial.txt"
        metadata_file = self.prompts_dir / f"{task_id}_initial.json"
        
        # Save prompt content
        with open(prompt_file, 'w') as f:
            f.write(prompt)
            
        # Save metadata
        metadata_dict = metadata if metadata is not None else {}
        metadata_dict.update({
            "task_id": task_id,
            "version": "initial",
            "timestamp": datetime.now().isoformat(),
            "prompt_file": str(prompt_file.name)
        })
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
            
        return "initial"
        
    def save_optimized_prompt(self, task_id: str, prompt: str, 
                            metrics: Dict[str, float], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save an optimized version of a prompt."""
        # Get next version number
        existing_versions = sorted([
            int(f.stem.split('_v')[-1])
            for f in self.prompts_dir.glob(f"{task_id}_v*.txt")
            if f.stem.split('_v')[-1].isdigit()
        ])
        version_num = (existing_versions[-1] + 1) if existing_versions else 1
        version_id = f"v{version_num}"
        
        # Save prompt content
        prompt_file = self.prompts_dir / f"{task_id}_{version_id}.txt"
        metadata_file = self.prompts_dir / f"{task_id}_{version_id}.json"
        
        with open(prompt_file, 'w') as f:
            f.write(prompt)
            
        # Save metadata
        metadata_dict = metadata if metadata is not None else {}
        metadata_dict.update({
            "task_id": task_id,
            "version": version_id,
            "version_number": version_num,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "prompt_file": str(prompt_file.name)
        })
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
            
        return version_id
        
    def load_prompt(self, task_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Load a specific prompt version. If version is None, loads the latest version."""
        if version is None:
            # Find latest version
            versions = sorted([
                int(f.stem.split('_v')[-1])
                for f in self.prompts_dir.glob(f"{task_id}_v*.txt")
                if f.stem.split('_v')[-1].isdigit()
            ])
            version = f"v{versions[-1]}" if versions else "initial"
            
        # Load prompt content
        prompt_file = self.prompts_dir / f"{task_id}_{version}.txt"
        metadata_file = self.prompts_dir / f"{task_id}_{version}.json"
        
        if not prompt_file.exists() or not metadata_file.exists():
            raise FileNotFoundError(f"Prompt version {version} not found for task {task_id}")
            
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
            
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            
        return {
            "content": prompt_content,
            "metadata": metadata
        }
        
    def get_prompt_history(self, task_id: str) -> List[Dict[str, Any]]:
        """Get the complete history of prompt versions for a task."""
        history = []
        
        # Get initial version if exists
        initial_metadata = self.prompts_dir / f"{task_id}_initial.json"
        if initial_metadata.exists():
            with open(initial_metadata, 'r') as f:
                history.append(json.load(f))
        
        # Get all optimized versions
        for metadata_file in sorted(self.prompts_dir.glob(f"{task_id}_v*.json")):
            with open(metadata_file, 'r') as f:
                history.append(json.load(f))
                
        return history
        
    def get_improvement_metrics(self, task_id: str) -> Dict[str, Any]:
        """Calculate improvement metrics across prompt versions."""
        history = self.get_prompt_history(task_id)
        if not history:
            return {"error": f"No prompt history found for task {task_id}"}
            
        initial_metrics = history[0].get("metrics", {})
        latest_metrics = history[-1].get("metrics", {})
        
        improvements = {}
        for metric, final_value in latest_metrics.items():
            if metric in initial_metrics:
                initial_value = initial_metrics[metric]
                improvements[metric] = {
                    "initial": initial_value,
                    "final": final_value,
                    "absolute_improvement": final_value - initial_value,
                    "relative_improvement": ((final_value - initial_value) / initial_value * 100 
                                          if initial_value != 0 else 0)
                }
                
        return {
            "task_id": task_id,
            "versions_count": len(history),
            "improvements": improvements,
            "history": history
        } 