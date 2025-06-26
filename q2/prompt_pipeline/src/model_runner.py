import subprocess
import json
from typing import Optional, Dict, Any
import logging
from .utils.logging_utils import PipelineLogger
import os

class ModelRunner:
    def __init__(self, model_name: str = "hf.co/lmstudio-community/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q4_K_M", base_dir: str = "."):
        self.model_name = model_name
        self.logger = PipelineLogger(base_dir=base_dir)
        self._verify_ollama_installation()

    def _verify_ollama_installation(self):
        """Verify that Ollama is installed and the model is available."""
        try:
            subprocess.run(["ollama", "list"], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            self.logger.log_error("system", e, {"stage": "installation_verification"})
            raise RuntimeError("Ollama is not properly installed or accessible")
        except FileNotFoundError:
            self.logger.log_error("system", FileNotFoundError("Ollama not found"), 
                                {"stage": "installation_verification"})
            raise RuntimeError("Ollama is not installed. Please install Ollama first.")

    def generate_response(self, prompt: str, task_id: str = "unknown", 
                        max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """Generate a response from the model using Ollama."""
        try:
            # Log the input prompt
            self.logger.log_model_output(
                task_id=task_id,
                stage="prompt",
                output=prompt,
                metadata={
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "model": self.model_name
                }
            )

            # Prepare the command - removed unsupported parameters
            cmd = [
                "ollama",
                "run",
                self.model_name,
                prompt
            ]

            # Set up environment for proper encoding
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            # Run the command and capture output with UTF-8 encoding
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                env=env,
                check=True
            )
            
            if result.returncode == 0 and result.stdout:
                response = result.stdout.strip()
                
                # Log the successful response
                self.logger.log_model_output(
                    task_id=task_id,
                    stage="response",
                    output=response,
                    metadata={
                        "success": True,
                        "return_code": result.returncode
                    }
                )
                
                return response
            else:
                # Log the error response
                self.logger.log_model_output(
                    task_id=task_id,
                    stage="response",
                    output=result.stderr,
                    metadata={
                        "success": False,
                        "return_code": result.returncode
                    }
                )
                return None

        except subprocess.CalledProcessError as e:
            self.logger.log_error(
                task_id,
                e,
                {
                    "stage": "model_execution",
                    "command": " ".join(cmd),
                    "stderr": e.stderr
                }
            )
            return None
        except Exception as e:
            self.logger.log_error(
                task_id,
                e,
                {
                    "stage": "model_execution",
                    "prompt": prompt
                }
            )
            return None

    def generate_multiple_responses(self, prompt: str, task_id: str, n: int = 3, **kwargs) -> list[str]:
        """Generate multiple responses for the same prompt."""
        responses = []
        for i in range(n):
            response = self.generate_response(
                prompt, 
                task_id=f"{task_id}_attempt_{i+1}", 
                **kwargs
            )
            if response:
                responses.append(response)
        
        # Log the collection of responses
        self.logger.log_model_output(
            task_id=task_id,
            stage="multiple_responses",
            output={
                "total_attempts": n,
                "successful_responses": len(responses),
                "responses": responses
            },
            metadata=kwargs
        )
        
        return responses

if __name__ == "__main__":
    # Example usage with logging
    runner = ModelRunner()
    test_prompt = "What is 2+2? Explain step by step."
    
    try:
        # Test single response
        response = runner.generate_response(
            test_prompt,
            task_id="test_math_1"
        )
        if response:
            print("Single response test:")
            print(response)
            print("\n" + "="*50 + "\n")

        # Test multiple responses
        responses = runner.generate_multiple_responses(
            test_prompt,
            task_id="test_math_1",
            n=2
        )
        print("Multiple responses test:")
        for i, resp in enumerate(responses, 1):
            print(f"\nResponse {i}:")
            print(resp)
    
    except Exception as e:
        print(f"Error during testing: {e}") 