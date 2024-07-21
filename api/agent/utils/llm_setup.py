# File: llm_library.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain_core.language_models import BaseLLM
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

class LLMProvider(ABC):
    @abstractmethod
    def get_llm(self, **kwargs) -> BaseLLM:
        pass

class OpenAIProvider(LLMProvider):
    def get_llm(self, **kwargs) -> BaseLLM:
        return ChatOpenAI(**kwargs)

class ClaudeProvider(LLMProvider):
    def get_llm(self, **kwargs) -> BaseLLM:
        return ChatAnthropic(**kwargs)

class LLMFactory:
    @staticmethod
    def create_llm(provider: str, **kwargs) -> BaseLLM:
        providers = {
            "openai": OpenAIProvider(),
            "claude": ClaudeProvider(),
        }
        
        if provider not in providers:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        return providers[provider].get_llm(**kwargs)

def get_llm(provider: str, model_name: Optional[str] = None, **kwargs) -> BaseLLM:
    """
    Get an LLM instance based on the specified provider and model name.
    
    :param provider: The LLM provider ("openai" or "claude")
    :param model_name: The specific model name (optional)
    :param kwargs: Additional keyword arguments for LLM initialization
    :return: An instance of the specified LLM
    """
    if model_name:
        kwargs["model_name"] = model_name
    
    return LLMFactory.create_llm(provider, **kwargs)
