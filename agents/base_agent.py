from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from openai import OpenAI
import os

class BaseAgent(ABC):
    """
    Abstract base class for all agents with support for multiple LLM providers.
    """
    def __init__(self, name: str, client: Optional[Union[OpenAI, Any]] = None):
        self.name = name
        self.client = client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.client_type = self._detect_client_type()
        self.model = self._get_default_model()
    
    def _detect_client_type(self) -> str:
        """Detect the type of client being used"""
        client_class = self.client.__class__.__name__
        if isinstance(self.client, OpenAI):
            return "openai"
        elif "Anthropic" in client_class:
            return "anthropic"
        else:
            return "unknown"
    
    def _get_default_model(self) -> str:
        """Get the default model based on client type"""
        if self.client_type == "openai":
            return "gpt-4"  # Using standard GPT-4 instead of custom model
        elif self.client_type == "anthropic":
            return "claude-2"
        else:
            return "gpt-4"  # Default to OpenAI
    
    def _format_messages(self, prompt: str, system_prompt: Optional[str] = None) -> Union[List[Dict[str, str]], str]:
        """Format messages based on client type"""
        if self.client_type == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            return messages
        elif self.client_type == "anthropic":
            # Anthropic uses a single string with special tokens
            formatted_prompt = ""
            if system_prompt:
                formatted_prompt += f"\n\nSystem: {system_prompt}"
            formatted_prompt += f"\n\nHuman: {prompt}\n\nAssistant:"
            return formatted_prompt
        else:
            # Default to OpenAI format
            return [{"role": "user", "content": prompt}]
    
    def get_completion(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Get completion from the model.
        
        Args:
            prompt: The user prompt to send to the model
            system_prompt: Optional system prompt to set context
            
        Returns:
            The model's response as a string
        """
        try:
            if self.client_type == "openai":
                messages = self._format_messages(prompt, system_prompt)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            
            elif self.client_type == "anthropic":
                formatted_prompt = self._format_messages(prompt, system_prompt)
                response = self.client.completions.create(
                    model=self.model,
                    prompt=formatted_prompt,
                    max_tokens_to_sample=2000,
                    temperature=0.7
                )
                return response.completion
            
            else:
                raise ValueError(f"Unsupported client type: {self.client_type}")
                
        except Exception as e:
            print(f"{self.name} Error: {str(e)}")
            raise e
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        pass
