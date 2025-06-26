import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from .logging_utils import PipelineLogger

class VersionManager:
    def __init__(self, base_dir: str = ".."):
        self.base_dir = Path(base_dir)
        self.prompts_dir = self.base_dir / "prompts"
        self.logger = PipelineLogger()
        
        # Ensure directories exist
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_version_number(self, filename: str) -> Tuple[str, int]:
        """Extract version info from filename."""
        parts = filename.replace('.txt', '').split('_')
        task_id = '_'.join(parts[:-1])  # Handle task IDs with underscores
        
        if parts[-1] == 'initial':
            return task_id, 0
        else:
            version_num = int(parts[-1].replace('v', ''))
            return task_id, version_num
            
    def save_prompt_version(self, task_id: str, prompt: str, metrics: Dict[str, Any],
                          is_initial: bool = False) -> str:
        """Save a new prompt version and return the version identifier."""
        # Determine version number
        existing_versions = self.get_prompt_versions(task_id)
        if is_initial:
            version_id = "initial"
        else:
            max_version = max([v['version_number'] for v in existing_versions], default=0)
            version_id = f"v{max_version + 1}"
        
        # Save prompt file
        filename = f"{task_id}_{version_id}.txt"
        prompt_path = self.prompts_dir / filename
        
        with open(prompt_path, 'w') as f:
            f.write(prompt)
            
        # Save metadata
        metadata_path = prompt_path.with_suffix('.json')
        metadata = {
            "task_id": task_id,
            "version": version_id,
            "version_number": 0 if is_initial else max_version + 1,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "prompt_file": filename
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Log the version creation
        self.logger.log_model_output(
            task_id=task_id,
            stage="prompt_version_created",
            output=metadata,
            metadata={"prompt_file": str(prompt_path)}
        )
        
        return version_id
        
    def get_prompt_versions(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a prompt for a task, sorted by version number."""
        versions = []
        
        # Get all prompt files for this task
        for metadata_file in self.prompts_dir.glob(f"{task_id}_*.json"):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                versions.append(metadata)
                
        # Sort by version number
        versions.sort(key=lambda x: x['version_number'])
        return versions
        
    def load_prompt_version(self, task_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Load a specific prompt version. If version is None, loads the latest version."""
        versions = self.get_prompt_versions(task_id)
        
        if not versions:
            raise FileNotFoundError(f"No prompts found for task {task_id}")
            
        # Select version
        if version is None:
            # Get latest version
            target_version = versions[-1]
        else:
            # Find specific version
            target_version = next(
                (v for v in versions if v['version'] == version),
                None
            )
            if not target_version:
                raise ValueError(f"Version {version} not found for task {task_id}")
                
        # Load prompt content
        prompt_path = self.prompts_dir / target_version['prompt_file']
        with open(prompt_path, 'r') as f:
            prompt_content = f.read()
            
        return {
            "content": prompt_content,
            "metadata": target_version
        }
        
    def get_performance_progression(self, task_id: str) -> Dict[str, Any]:
        """Analyze performance progression across versions."""
        versions = self.get_prompt_versions(task_id)
        
        if not versions:
            return {"error": f"No versions found for task {task_id}"}
            
        # Extract metrics progression
        progression = {
            "task_id": task_id,
            "versions": len(versions),
            "metrics_history": [],
            "improvements": {}
        }
        
        for i, version in enumerate(versions):
            metrics = version['metrics']
            progression["metrics_history"].append({
                "version": version['version'],
                "metrics": metrics
            })
            
            # Calculate improvements from initial version
            if i > 0:
                initial_metrics = versions[0]['metrics']
                improvements = {}
                for metric, value in metrics.items():
                    if metric in initial_metrics:
                        delta = value - initial_metrics[metric]
                        improvements[metric] = {
                            "delta": delta,
                            "percentage": (delta / initial_metrics[metric] * 100) if initial_metrics[metric] != 0 else 0
                        }
                progression["improvements"][version['version']] = improvements
                
        # Calculate overall improvement
        if len(versions) > 1:
            first_metrics = versions[0]['metrics']
            last_metrics = versions[-1]['metrics']
            overall_improvement = {}
            
            for metric in first_metrics:
                if metric in last_metrics:
                    delta = last_metrics[metric] - first_metrics[metric]
                    overall_improvement[metric] = {
                        "initial": first_metrics[metric],
                        "final": last_metrics[metric],
                        "total_delta": delta,
                        "percentage": (delta / first_metrics[metric] * 100) if first_metrics[metric] != 0 else 0
                    }
                    
            progression["overall_improvement"] = overall_improvement
            
        return progression

if __name__ == "__main__":
    # Example usage
    version_manager = VersionManager()
    
    try:
        # Save initial version
        initial_metrics = {
            "confidence": 0.75,
            "consistency": 0.8,
            "correctness": 0.9
        }
        
        version_manager.save_prompt_version(
            task_id="test_task",
            prompt="Initial prompt content",
            metrics=initial_metrics,
            is_initial=True
        )
        
        # Save improved version
        improved_metrics = {
            "confidence": 0.85,
            "consistency": 0.9,
            "correctness": 0.95
        }
        
        version_manager.save_prompt_version(
            task_id="test_task",
            prompt="Improved prompt content",
            metrics=improved_metrics
        )
        
        # Load latest version
        latest = version_manager.load_prompt_version("test_task")
        print("\nLatest version:")
        print(json.dumps(latest, indent=2))
        
        # Get performance progression
        progression = version_manager.get_performance_progression("test_task")
        print("\nPerformance progression:")
        print(json.dumps(progression, indent=2))
        
    except Exception as e:
        print(f"Error during testing: {e}") 