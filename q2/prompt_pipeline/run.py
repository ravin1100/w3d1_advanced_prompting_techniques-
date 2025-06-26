from src.pipeline import PromptPipeline
import json
from pathlib import Path
import logging
import os
from datetime import datetime

# Configure logging with custom formatter
class CustomFormatter(logging.Formatter):
    """Custom formatter with colors and better formatting"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.FORMATS = {
            logging.DEBUG: self.grey,
            logging.INFO: self.blue,
            logging.WARNING: self.yellow,
            logging.ERROR: self.red,
            logging.CRITICAL: self.bold_red
        }

    def format(self, record):
        color = self.FORMATS.get(record.levelno, self.grey)
        record.levelname = f"{color}{record.levelname:8}{self.reset}"
        return super().format(record)

def setup_logging():
    """Set up logging configuration with custom formatting"""
    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CustomFormatter())
    
    # Configure root logger
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(console_handler)

def print_header(task_id: str):
    """Print a visually appealing header for the task"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "="*60)
    print(f"Pipeline Execution - Task: {task_id}")
    print(f"Started at: {timestamp}")
    print("="*60 + "\n")

def print_results(results: dict):
    """Print results in a formatted way"""
    print("\n" + "-"*60)
    print("Pipeline Results Summary")
    print("-"*60)
    print(f"Final Answer: {results['aggregation_result']['final_answer']}")
    print(f"Confidence: {results['metrics']['improvements']['confidence']['final']:.2f}")
    print(f"Consistency: {results['metrics']['improvements']['consistency']['final']:.2f}")
    print("-"*60 + "\n")

def main():
    try:
        # Set up logging with custom formatter
        setup_logging()
        
        # Get the directory where run.py is located
        base_dir = Path(__file__).parent
        
        # Initialize pipeline with correct base directory
        pipeline = PromptPipeline(base_dir=str(base_dir))
        
        # Load example tasks
        with open('tasks/example_tasks.json', 'r') as f:
            tasks = json.load(f)
        
        # Run pipeline for each task
        for task in tasks:
            task_id = task['task_id']
            
            # Convert task format to pipeline format
            pipeline_task = {
                "id": task_id,
                "problem_statement": task["problem"],
                "expected_answer": task["expected_answer"]
            }
            
            # Save individual task file
            task_file = Path('tasks') / f"{task_id}.json"
            with open(task_file, 'w') as f:
                json.dump(pipeline_task, f, indent=2)
            
            # Run pipeline
            print_header(task_id)
            
            try:
                results = pipeline.run_pipeline(task_id)
                
                # Print results summary
                print_results(results)
            except Exception as e:
                logging.error(f"Error processing task {task_id}: {e}")
                continue

    except Exception as e:
        logging.error(f"Error running pipeline: {e}", exc_info=True)

if __name__ == "__main__":
    main() 