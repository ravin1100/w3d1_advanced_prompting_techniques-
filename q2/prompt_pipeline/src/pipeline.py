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
from .prompt_manager import PromptManager
from .utils.logging_utils import PipelineLogger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptPipeline:
    def __init__(self, 
                 model_name: str = "hf.co/lmstudio-community/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q4_K_M",
                 base_dir: str = "."):
        self.base_dir = Path(base_dir)
        
        # Initialize logger first
        self.logger = PipelineLogger(base_dir=str(self.base_dir))
        
        # Initialize components
        self.model_runner = ModelRunner(model_name, base_dir=str(self.base_dir))
        self.task_loader = TaskLoader(str(self.base_dir / "tasks"))
        self.tot_generator = ToTGenerator(self.model_runner)
        self.aggregator = Aggregator(self.model_runner)
        self.optimizer = PromptOptimizer(
            self.model_runner, 
            str(self.logger.prompts_dir), 
            base_dir=str(self.base_dir)
        )
        self.prompt_manager = PromptManager(str(self.logger.prompts_dir))
        
        # Use logger's directories
        self.logs_dir = self.logger.logs_dir
        self.eval_dir = self.logger.eval_dir

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
            logger.info("="*60)
            logger.info(f"Starting pipeline execution for task: {task_id}")
            logger.info("="*60)
            
            # Load task
            task = self.task_loader.load_task(f"{task_id}.json")
            logger.info(f"✓ Task {task_id} loaded successfully")
            
            # Create and save initial prompt
            logger.info(f"➤ Task {task_id}: Creating initial prompt...")
            initial_prompt = self._create_base_prompt(task)
            self.prompt_manager.save_initial_prompt(
                task_id=task_id,
                prompt=initial_prompt
            )
            current_prompt = initial_prompt
            logger.info(f"✓ Task {task_id}: Initial prompt created and saved")
            
            # Generate reasoning paths
            logger.info(f"\n➤ Task {task_id}: Generating reasoning paths...")
            reasoning_paths = self.tot_generator.generate_reasoning_paths(task)
            logger.info(f"✓ Task {task_id}: Generated {len(reasoning_paths)} reasoning paths")
            
            # Aggregate results
            logger.info(f"\n➤ Task {task_id}: Aggregating results...")
            aggregation_result = self.aggregator.aggregate_responses(reasoning_paths)
            logger.info(f"✓ Task {task_id}: Results aggregated successfully")
            
            # Calculate initial metrics
            logger.info(f"\n➤ Task {task_id}: Calculating initial metrics...")
            initial_metrics = {
                "confidence": aggregation_result.get('confidence', 0),
                "consistency": len(aggregation_result.get('supporting_answers', [])) / len(reasoning_paths),
                "correctness": self.optimizer._evaluate_prompt_performance(
                    {"final_answer": aggregation_result.get('final_answer')}, 
                    task
                ).get("correctness", 0)
            }
            logger.info(f"✓ Task {task_id}: Initial metrics:")
            logger.info(f"  • Confidence: {initial_metrics['confidence']:.2f}")
            logger.info(f"  • Consistency: {initial_metrics['consistency']:.2f}")
            
            # Optimize prompt if needed
            if initial_metrics["confidence"] < 0.8:
                logger.info(f"\n➤ Task {task_id}: Confidence below threshold (0.8), starting optimization...")
                optimization_result = self.optimizer.optimize_prompt(
                    initial_prompt=current_prompt,
                    task=task,
                    results=aggregation_result
                )
                current_prompt = optimization_result['optimized_prompt']
                logger.info(f"✓ Task {task_id}: Prompt optimization completed")
                
                # Save optimized prompt
                self.prompt_manager.save_optimized_prompt(
                    task_id=task_id,
                    prompt=current_prompt,
                    metrics=optimization_result['metrics']
                )
                
                # Re-run with optimized prompt
                logger.info(f"\n➤ Task {task_id}: Re-running with optimized prompt...")
                reasoning_paths = self.tot_generator.generate_reasoning_paths(task)
                aggregation_result = self.aggregator.aggregate_responses(reasoning_paths)
                logger.info(f"✓ Task {task_id}: Re-run completed")
            
            # Get final metrics and improvements
            logger.info(f"\n➤ Task {task_id}: Calculating final metrics...")
            improvement_metrics = self.prompt_manager.get_improvement_metrics(task_id)
            
            # Prepare run results
            run_results = {
                "task_id": task_id,
                "timestamp": str(datetime.datetime.now()),
                "initial_prompt": initial_prompt,
                "final_prompt": current_prompt,
                "reasoning_paths": reasoning_paths,
                "aggregation_result": aggregation_result,
                "metrics": improvement_metrics
            }
            
            # Log results and save evaluation
            self._log_run_results(task_id, run_results)
            self._save_evaluation(task_id, improvement_metrics)
            
            logger.info("\n" + "="*60)
            logger.info(f"✓ Task {task_id}: Pipeline completed successfully")
            logger.info("="*60)
            return run_results
            
        except Exception as e:
            logger.error("\n" + "="*60)
            logger.error(f"✗ Task {task_id}: Pipeline failed")
            logger.error(f"Error: {str(e)}")
            logger.error("="*60)
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
        print(f"Confidence: {results['metrics']['improvements']['confidence']['final']:.2f}")
        print(f"Consistency: {results['metrics']['improvements']['consistency']['final']:.2f}")
        
    except Exception as e:
        print(f"Error running example: {e}") 