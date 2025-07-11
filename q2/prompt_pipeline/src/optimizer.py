from typing import Dict, Any, List, Optional
import logging
import json
import datetime
from pathlib import Path
from .utils.logging_utils import PipelineLogger
from .utils.version_manager import VersionManager
from .model_runner import ModelRunner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptOptimizer:
    def __init__(self, model_runner: ModelRunner, prompts_dir: Optional[str] = None, max_iterations: int = 3, base_dir: str = "."):
        self.model_runner = model_runner
        self.max_iterations = max_iterations
        self.logger = PipelineLogger(base_dir=base_dir)
        self.version_manager = VersionManager(base_dir=base_dir)
        self.eval_dir = self.logger.eval_dir
        # Use prompts_dir from parameter if provided, otherwise use logger's
        self.prompts_dir = Path(prompts_dir) if prompts_dir else self.logger.prompts_dir
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def _evaluate_prompt_performance(self, results: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate the performance of a prompt based on results."""
        metrics = {
            "confidence": results.get('confidence', 0),
            "consistency": len(results.get('supporting_answers', [])) / results.get('total_paths', 1),
            "correctness": 0.0
        }
        
        # Calculate correctness if expected answer is available
        if task.get('expected_answer'):
            correctness_prompt = f"""Rate the correctness of this answer from 0 to 1:

Given Answer: {results.get('final_answer', '')}
Expected Answer: {task['expected_answer']}

Consider:
1. Numerical accuracy
2. Units and format
3. Semantic equivalence

Provide only the numerical score."""

            try:
                response = self.model_runner.generate_response(
                    correctness_prompt,
                    task_id=f"{task['task_id']}_correctness_eval"
                )
                if response:
                    metrics["correctness"] = float(response.strip())
            except (ValueError, AttributeError) as e:
                self.logger.log_error(
                    task['task_id'],
                    e,
                    {
                        "stage": "correctness_evaluation",
                        "prompt": correctness_prompt,
                        "response": response if 'response' in locals() else None
                    }
                )
                
        # Calculate overall score
        metrics["overall_score"] = (
            metrics["confidence"] * 0.3 +
            metrics["consistency"] * 0.3 +
            metrics["correctness"] * 0.4
        )
        
        return metrics

    def _create_improvement_prompt(self, original_prompt: str, results: Dict[str, Any], task: Dict[str, Any]) -> str:
        """Create a meta-prompt for improving the original prompt."""
        return f"""Analyze and improve the following prompt that produced suboptimal results:

Original Prompt:
{original_prompt}

Task Description:
{task['problem']}

Expected Answer:
{task.get('expected_answer', 'Not provided')}

Current Results:
- Confidence: {results.get('confidence', 'N/A')}
- Answer: {results.get('final_answer', 'N/A')}
- Supporting Answers: {results.get('supporting_answers', [])}

Issues to address:
1. {"Low confidence" if results.get('confidence', 0) < 0.7 else ""}
2. {"Inconsistent answers" if len(results.get('supporting_answers', [])) < 2 else ""}
3. {"Incorrect answer" if task.get('expected_answer') and task.get('expected_answer') != results.get('final_answer') else ""}

Provide an improved version of the prompt that:
1. Is more specific and clearer
2. Better guides the reasoning process
3. Reduces ambiguity
4. Encourages consistent outputs

Return only the improved prompt text."""

    def optimize_prompt(self, initial_prompt: str, task: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize a prompt through multiple iterations based on performance."""
        current_prompt = initial_prompt
        best_prompt = initial_prompt
        best_metrics = self._evaluate_prompt_performance(results, task)
        
        # Save initial version
        self.version_manager.save_prompt_version(
            task_id=task['task_id'],
            prompt=initial_prompt,
            metrics=best_metrics,
            is_initial=True
        )
        
        optimization_history = []
        
        for iteration in range(self.max_iterations):
            # Generate improved prompt
            improvement_prompt = self._create_improvement_prompt(current_prompt, results, task)
            improved_prompt = self.model_runner.generate_response(
                improvement_prompt,
                task_id=f"{task['task_id']}_optimization_iter_{iteration + 1}"
            )
            
            if not improved_prompt:
                self.logger.log_error(
                    task['task_id'],
                    Exception("Failed to generate improved prompt"),
                    {
                        "stage": "prompt_optimization",
                        "iteration": iteration + 1,
                        "improvement_prompt": improvement_prompt
                    }
                )
                break
                
            # Test the improved prompt
            test_response = self.model_runner.generate_response(
                improved_prompt,
                task_id=f"{task['task_id']}_test_iter_{iteration + 1}"
            )
            if not test_response:
                continue
                
            # Evaluate the new prompt's performance
            new_metrics = self._evaluate_prompt_performance({"final_answer": test_response}, task)
            
            # Save new version
            self.version_manager.save_prompt_version(
                task_id=task['task_id'],
                prompt=improved_prompt,
                metrics=new_metrics
            )
            
            optimization_history.append({
                "iteration": iteration + 1,
                "prompt": improved_prompt,
                "metrics": new_metrics,
                "improvement": new_metrics["overall_score"] - best_metrics["overall_score"]
            })
            
            # Update if better
            if new_metrics["overall_score"] > best_metrics["overall_score"]:
                best_prompt = improved_prompt
                best_metrics = new_metrics
                current_prompt = improved_prompt
            else:
                # If no improvement, stop early
                break
            
        # Get performance progression
        progression = self.version_manager.get_performance_progression(task['task_id'])
            
        return {
            "optimized_prompt": best_prompt,
            "original_prompt": initial_prompt,
            "metrics": best_metrics,
            "optimization_history": optimization_history,
            "performance_progression": progression
        }

if __name__ == "__main__":
    # Example usage with logging
    model_runner = ModelRunner()
    optimizer = PromptOptimizer(model_runner)
    
    try:
        test_task = {
            "task_id": "test_1",
            "problem": "If a train travels 120 kilometers in 2 hours, what is its average speed in kilometers per hour?",
            "expected_answer": "60 kilometers per hour"
        }
        
        initial_prompt = """Calculate the average speed of the train.
Given:
- Distance: 120 kilometers
- Time: 2 hours
Show your work."""
        
        test_results = {
            "final_answer": "The speed is approximately 60-65 km/h",
            "confidence": 0.6,
            "supporting_answers": ["60-65 km/h", "around 60 kilometers per hour"],
            "total_paths": 3
        }
        
        optimization_result = optimizer.optimize_prompt(initial_prompt, test_task, test_results)
        
        print("Optimization Result:")
        for key, value in optimization_result.items():
            if key != "optimization_history":
                print(f"\n{key}:")
                print(value)
            
    except Exception as e:
        print(f"Error during testing: {e}") 