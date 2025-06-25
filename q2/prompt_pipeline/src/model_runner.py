import subprocess
import json
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelRunner:
    def __init__(self, model_name: str = "hf.co/lmstudio-community/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q4_K_M"):
        self.model_name = model_name
        self._verify_ollama_installation()

    def _verify_ollama_installation(self):
        """Verify that Ollama is installed and the model is available."""
        try:
            subprocess.run(["ollama", "list"], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error verifying Ollama installation: {e}")
            raise RuntimeError("Ollama is not properly installed or accessible")
        except FileNotFoundError:
            raise RuntimeError("Ollama is not installed. Please install Ollama first.")

    def generate_response(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """Generate a response from the model using Ollama."""
        try:
            # Prepare the command
            cmd = [
                "ollama",
                "run",
                self.model_name,
                prompt,
                "--temperature",
                str(temperature),
                "--max-tokens",
                str(max_tokens)
            ]

            # Run the command and capture output
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
            else:
                logger.error(f"Error in model response: {result.stderr}")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Error running model: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def generate_multiple_responses(self, prompt: str, n: int = 3, **kwargs) -> list[str]:
        """Generate multiple responses for the same prompt."""
        responses = []
        for _ in range(n):
            response = self.generate_response(prompt, **kwargs)
            if response:
                responses.append(response)
        return responses

if __name__ == "__main__":
    # Example usage
    runner = ModelRunner()
    test_prompt = "What is 2+2? Explain step by step."
    
    try:
        # Test single response
        response = runner.generate_response(test_prompt)
        if response:
            print("Single response test:")
            print(response)
            print("\n" + "="*50 + "\n")

        # Test multiple responses
        responses = runner.generate_multiple_responses(test_prompt, n=2)
        print("Multiple responses test:")
        for i, resp in enumerate(responses, 1):
            print(f"\nResponse {i}:")
            print(resp)
    
    except Exception as e:
        print(f"Error during testing: {e}") 