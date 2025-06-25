from typing import List, Dict, Any, Optional
import logging
from .model_runner import ModelRunner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToTGenerator:
    def __init__(self, model_runner: ModelRunner, num_paths: int = 3, max_depth: int = 3):
        self.model_runner = model_runner
        self.num_paths = num_paths
        self.max_depth = max_depth
        
    def _create_tot_prompt(self, task: Dict[str, Any], current_path: Optional[List[str]] = None) -> str:
        """Create a prompt that encourages tree-of-thought reasoning."""
        if current_path is None:
            current_path = []
            
        base_prompt = f"""Task: {task['problem_statement']}

You are solving this problem using Tree of Thoughts reasoning. Consider multiple possible approaches and explore them systematically.

Previous thoughts (if any):
{' -> '.join(current_path) if current_path else 'Starting fresh'}

Think step by step:
1. First, identify multiple possible approaches to solve this problem
2. For each approach, break down the reasoning into clear steps
3. Evaluate the potential of each path
4. Choose the most promising direction and explain why

Your reasoning:"""

        return base_prompt

    def _evaluate_path(self, response: str, task: Dict[str, Any]) -> float:
        """Evaluate the quality of a reasoning path."""
        # Create an evaluation prompt
        eval_prompt = f"""Evaluate the following reasoning path for solving this problem:

Problem: {task['problem_statement']}
Expected Answer: {task.get('expected_answer', 'Not provided')}

Reasoning Path:
{response}

Rate this reasoning path from 0 to 1 based on:
1. Logical coherence
2. Step-by-step clarity
3. Likelihood of reaching the correct solution

Provide only the numerical score."""

        try:
            score_response = self.model_runner.generate_response(eval_prompt)
            if score_response is None:
                logger.warning("Model returned None response, defaulting to 0.5")
                return 0.5
            score = float(score_response.strip())
            return min(max(score, 0), 1)  # Ensure score is between 0 and 1
        except (ValueError, AttributeError):
            logger.warning("Failed to get valid score, defaulting to 0.5")
            return 0.5

    def generate_reasoning_paths(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate multiple reasoning paths for a given task."""
        paths = []
        
        for _ in range(self.num_paths):
            current_path = []
            full_reasoning = []
            
            for depth in range(self.max_depth):
                # Generate next step in reasoning
                prompt = self._create_tot_prompt(task, current_path)
                response = self.model_runner.generate_response(prompt)
                
                if not response:
                    break
                    
                current_path.append(f"Step {depth + 1}")
                full_reasoning.append(response)
                
                # Check if we've reached a conclusion
                if "therefore" in response.lower() or "conclusion" in response.lower():
                    break
            
            # Evaluate the complete path
            full_response = "\n".join(full_reasoning)
            score = self._evaluate_path(full_response, task)
            
            paths.append({
                "reasoning": full_reasoning,
                "score": score,
                "final_response": full_response
            })
        
        # Sort paths by score
        paths.sort(key=lambda x: x["score"], reverse=True)
        return paths

if __name__ == "__main__":
    # Example usage
    from model_runner import ModelRunner
    
    try:
        model_runner = ModelRunner()
        tot_generator = ToTGenerator(model_runner)
        
        test_task = {
            "id": "test_1",
            "problem_statement": "If a train travels 120 kilometers in 2 hours, what is its average speed in kilometers per hour?",
            "expected_answer": "60 kilometers per hour"
        }
        
        paths = tot_generator.generate_reasoning_paths(test_task)
        
        print("Generated reasoning paths:")
        for i, path in enumerate(paths, 1):
            print(f"\nPath {i} (Score: {path['score']:.2f}):")
            print(path['final_response'])
            print("-" * 50)
            
    except Exception as e:
        print(f"Error during testing: {e}") 