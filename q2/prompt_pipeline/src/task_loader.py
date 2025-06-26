import json
import yaml
from pathlib import Path
from typing import Dict, List, Any

class TaskLoader:
    def __init__(self, tasks_dir: str = "tasks"):
        self.tasks_dir = Path(tasks_dir)
        
    def load_task(self, task_file: str) -> Dict[str, Any]:
        """Load a single task from a file."""
        file_path = self.tasks_dir / task_file
        
        if not file_path.exists():
            raise FileNotFoundError(f"Task file not found: {file_path}")
            
        with open(file_path, 'r') as f:
            if file_path.suffix == '.json':
                return json.load(f)
            elif file_path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
                
    def load_all_tasks(self) -> List[Dict[str, Any]]:
        """Load all tasks from the tasks directory."""
        tasks = []
        for file_path in self.tasks_dir.glob('*.*'):
            if file_path.suffix in ['.json', '.yaml', '.yml']:
                try:
                    task = self.load_task(file_path.name)
                    tasks.append(task)
                except Exception as e:
                    print(f"Error loading task {file_path}: {e}")
        return tasks

if __name__ == "__main__":
    # Example usage
    loader = TaskLoader()
    try:
        tasks = loader.load_all_tasks()
        print(f"Loaded {len(tasks)} tasks successfully")
    except Exception as e:
        print(f"Error loading tasks: {e}") 