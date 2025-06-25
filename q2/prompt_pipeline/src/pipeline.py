import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import datetime

from .model_runner import ModelRunner
from .task_loader import TaskLoader
from .tot_generator import ToTGenerator
from .aggregator import Aggregator
from .optimizer import PromptOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptPipeline:
    def __init__(self, 
                 model_name: str = "hf.co/lmstudio-community/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q4_K_M",
                 base_dir: str = ".."):
        self.base_dir = Path(base_dir)
        
        # Initialize components
        self.model_runner = ModelRunner(model_name)
        self.task_loader = TaskLoader(str(self.base_dir / "tasks"))
        self.tot_generator = ToTGenerator(self.model_runner)
        self.aggregator = Aggregator(self.model_runner)
        self.optimizer = PromptOptimizer(self.model_runner, str(self.base_dir / "prompts"))
        
        # Create logs directory
        self.logs_dir = self.base_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create evaluation directory
        self.eval_dir = self.base_dir / "evaluation"
        self.eval_dir.mkdir(parents=True, exist_ok=True)

    def _create_base_prompt(self, task: Dict[str, Any]) -> str:
        """Create the initial prompt for a task."""
        return f"""Solve the following problem step by step:

Problem: {task['problem_statement']}

Requirements:
1. Show your complete reasoning process
2. Break down the solution into clear steps
3. Validate your answer
4. State your final answer clearly

Your solution:"""

    def _log_run_results(self, task_id: str, run_data: Dict[str, Any]):
        """Log the results of a pipeline run."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"{task_id}_{timestamp}.json"
        
        with open(log_file, 'w') as f:
            json.dump(run_data, f, indent=2)

    def _save_evaluation(self, task_id: str, evaluation_data: Dict[str, Any]):
        """Save evaluation metrics."""
        eval_file = self.eval_dir / f"{task_id}_evaluation.json"
        
        with open(eval_file, 'w') as f:
            json.dump(evaluation_data, f, indent=2)

    def run_pipeline(self, task_id: str) -> Dict[str, Any]:
        """Run the complete prompt engineering pipeline for a task."""
        try:
            # Load task
            task = self.task_loader.load_task(f"{task_id}.json")
            logger.info(f"Loaded task: {task_id}")
            
            # Create initial prompt
            initial_prompt = self._create_base_prompt(task)
            current_prompt = initial_prompt
            
            # Generate reasoning paths
            logger.info("Generating reasoning paths...")
            reasoning_paths = self.tot_generator.generate_reasoning_paths(task)
            
            # Aggregate results
            logger.info("Aggregating results...")
            aggregation_result = self.aggregator.aggregate_responses(reasoning_paths)
            
            # Optimize prompt if needed
            if aggregation_result.get('confidence', 0) < 0.8:
                logger.info("Optimizing prompt...")
                optimization_result = self.optimizer.optimize_prompt(
                    initial_prompt=current_prompt,
                    task=task,
                    results=aggregation_result
                )
                current_prompt = optimization_result['optimized_prompt']
                
                # Re-run with optimized prompt
                logger.info("Re-running with optimized prompt...")
                reasoning_paths = self.tot_generator.generate_reasoning_paths(task)
                aggregation_result = self.aggregator.aggregate_responses(reasoning_paths)
            
            # Prepare run results
            run_results = {
                "task_id": task_id,
                "timestamp": str(datetime.datetime.now()),
                "initial_prompt": initial_prompt,
                "final_prompt": current_prompt,
                "reasoning_paths": reasoning_paths,
                "aggregation_result": aggregation_result,
                "metrics": {
                    "confidence": aggregation_result.get('confidence', 0),
                    "consistency": len(aggregation_result.get('supporting_answers', [])) / len(reasoning_paths),
                    "final_answer": aggregation_result.get('final_answer'),
                    "expected_answer": task.get('expected_answer')
                }
            }
            
            # Log results
            self._log_run_results(task_id, run_results)
            
            # Save evaluation
            evaluation = {
                "task_id": task_id,
                "timestamp": str(datetime.datetime.now()),
                "metrics": run_results["metrics"],
                "prompt_versions": {
                    "initial": initial_prompt,
                    "final": current_prompt
                }
            }
            self._save_evaluation(task_id, evaluation)
            
            return run_results
            
        except Exception as e:
            logger.error(f"Error running pipeline for task {task_id}: {e}")
            raise

if __name__ == "__main__":
    # Example usage
    try:
        pipeline = PromptPipeline()
        
        # Create a test task
        test_task = {
            "id": "test_1",
            "problem_statement": "If a train travels 120 kilometers in 2 hours, what is its average speed in kilometers per hour?",
            "expected_answer": "60 kilometers per hour"
        }
        
        # Save test task
        task_dir = Path("../tasks")
        task_dir.mkdir(parents=True, exist_ok=True)
        with open(task_dir / "test_1.json", 'w') as f:
            json.dump(test_task, f, indent=2)
        
        # Run pipeline
        results = pipeline.run_pipeline("test_1")
        
        print("\nPipeline Results:")
        print(f"Final Answer: {results['aggregation_result']['final_answer']}")
        print(f"Confidence: {results['metrics']['confidence']:.2f}")
        print(f"Consistency: {results['metrics']['consistency']:.2f}")
        
    except Exception as e:
        print(f"Error running example: {e}") 