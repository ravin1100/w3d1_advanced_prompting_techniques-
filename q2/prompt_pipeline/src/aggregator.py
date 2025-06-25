from typing import List, Dict, Any, Tuple
import re
import logging
from collections import Counter
from .model_runner import ModelRunner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Aggregator:
    def __init__(self, model_runner: ModelRunner, consistency_threshold: float = 0.7):
        self.model_runner = model_runner
        self.consistency_threshold = consistency_threshold

    def _extract_final_answer(self, reasoning: str) -> str:
        """Extract the final answer from a reasoning path."""
        # Look for common conclusion patterns
        patterns = [
            r"therefore,?\s*(the\s*)?(?:answer\s*is\s*)?([^\.]+)",
            r"conclusion:?\s*([^\.]+)",
            r"final\s*answer:?\s*([^\.]+)",
            r"thus,?\s*(the\s*)?(?:answer\s*is\s*)?([^\.]+)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, reasoning.lower())
            # Take the last match as it's likely to be the final conclusion
            last_match = None
            for match in matches:
                last_match = match
            
            if last_match:
                return last_match.group(1).strip()
        
        # If no pattern matches, return the last sentence
        sentences = reasoning.split('.')
        return sentences[-1].strip()

    def _calculate_answer_similarity(self, answer1: str, answer2: str) -> float:
        """Calculate similarity between two answers using the model."""
        similarity_prompt = f"""Rate the similarity between these two answers from 0 to 1:

Answer 1: {answer1}
Answer 2: {answer2}

Consider:
1. Numerical equivalence (if numbers are present)
2. Semantic meaning
3. Units and format

Provide only the numerical score."""

        try:
            response = self.model_runner.generate_response(similarity_prompt)
            if response is None:
                return 0.0
            score = float(response.strip())
            return min(max(score, 0), 1)  # Ensure score is between 0 and 1
        except (ValueError, AttributeError):
            logger.warning("Failed to calculate similarity, defaulting to 0")
            return 0.0

    def _cluster_answers(self, answers: List[Tuple[str, float]]) -> List[List[Tuple[str, float]]]:
        """Cluster similar answers together."""
        clusters: List[List[Tuple[str, float]]] = []
        
        for answer, score in answers:
            added_to_cluster = False
            
            # Try to add to existing cluster
            for cluster in clusters:
                # Check similarity with first answer in cluster
                similarity = self._calculate_answer_similarity(answer, cluster[0][0])
                if similarity >= self.consistency_threshold:
                    cluster.append((answer, score))
                    added_to_cluster = True
                    break
            
            # If not similar to any existing cluster, create new cluster
            if not added_to_cluster:
                clusters.append([(answer, score)])
        
        return clusters

    def aggregate_responses(self, reasoning_paths: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate multiple reasoning paths to produce a final answer."""
        if not reasoning_paths:
            return {"error": "No reasoning paths provided"}

        # Extract answers and their scores
        answers_with_scores = []
        for path in reasoning_paths:
            answer = self._extract_final_answer(path["final_response"])
            answers_with_scores.append((answer, path["score"]))

        # Cluster similar answers
        clusters = self._cluster_answers(answers_with_scores)
        
        # Find the best cluster based on size and average score
        best_cluster = max(clusters, key=lambda c: (len(c), sum(score for _, score in c) / len(c)))
        
        # Calculate confidence based on cluster size and scores
        confidence = (len(best_cluster) / len(reasoning_paths)) * sum(score for _, score in best_cluster) / len(best_cluster)
        
        # Select the answer with the highest score from the best cluster
        best_answer = max(best_cluster, key=lambda x: x[1])[0]
        
        return {
            "final_answer": best_answer,
            "confidence": confidence,
            "supporting_answers": [ans for ans, _ in best_cluster],
            "cluster_size": len(best_cluster),
            "total_paths": len(reasoning_paths)
        }

if __name__ == "__main__":
    # Example usage
    from model_runner import ModelRunner
    
    try:
        model_runner = ModelRunner()
        aggregator = Aggregator(model_runner)
        
        # Example reasoning paths
        test_paths = [
            {
                "final_response": "The train's speed is 60 kilometers per hour because 120 km ÷ 2 hours = 60 km/h",
                "score": 0.9
            },
            {
                "final_response": "Therefore, the average speed is 60 km/h (distance/time = 120/2)",
                "score": 0.85
            },
            {
                "final_response": "The speed must be 70 km/h based on the calculation",
                "score": 0.6
            }
        ]
        
        result = aggregator.aggregate_responses(test_paths)
        
        print("Aggregation Result:")
        for key, value in result.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"Error during testing: {e}") 