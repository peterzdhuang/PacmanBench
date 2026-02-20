"""LLM provider abstraction layer for multi-provider benchmark support."""

import re
import time
from abc import ABC, abstractmethod
from typing import Optional

from src.constants import Direction


def parse_direction(text: str) -> Direction:
    """Parse an LLM response string into a Direction enum.
    
    Looks for UP/DOWN/LEFT/RIGHT in the response text (case-insensitive).
    Returns Direction.NONE if no valid direction is found.
    """
    text_upper = text.strip().upper()

    # Try exact match first
    for d in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
        if text_upper == d.name:
            return d

    # Try to find direction word in response (last occurrence wins, 
    # in case the LLM explains before answering)
    last_match = None
    last_pos = -1
    for d in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
        # Use word boundary to avoid matching substrings
        matches = list(re.finditer(r'\b' + d.name + r'\b', text_upper))
        if matches:
            pos = matches[-1].start()
            if pos > last_pos:
                last_pos = pos
                last_match = d

    return last_match if last_match else Direction.NONE


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model: str, temperature: float = 0.0, max_tokens: int = 50, timeout: float = 30.0):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    @abstractmethod
    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        """Make the actual API call and return the raw text response."""
        raise NotImplementedError

    def get_move(self, system_prompt: str, user_prompt: str) -> tuple:
        """Get a move direction from the LLM.
        
        Returns:
            (Direction, raw_response: str, latency: float, error: Optional[str])
        """
        start = time.time()
        try:
            raw = self._call_api(system_prompt, user_prompt)
            latency = time.time() - start
            direction = parse_direction(raw)
            return direction, raw, latency, None
        except Exception as e:
            latency = time.time() - start
            return Direction.NONE, "", latency, str(e)


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT-4o, GPT-4, etc.)."""

    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None, **kwargs):
        super().__init__(model, **kwargs)
        import openai
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = openai.OpenAI()  # Uses OPENAI_API_KEY env var

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
        )
        return response.choices[0].message.content or ""


class AnthropicProvider(LLMProvider):
    """Anthropic API provider (Claude models)."""

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: Optional[str] = None, **kwargs):
        super().__init__(model, **kwargs)
        import anthropic
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.content[0].text if response.content else ""


class OllamaProvider(LLMProvider):
    """Ollama local model provider (via HTTP API)."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(model, **kwargs)
        self.base_url = base_url.rstrip("/")

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        import requests
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")


def create_provider(provider_name: str, model: str, **kwargs) -> LLMProvider:
    """Factory function to create an LLM provider by name.
    
    Args:
        provider_name: One of 'openai', 'anthropic', 'ollama'
        model: Model name/identifier
        **kwargs: Additional provider-specific arguments
    """
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
    }
    if provider_name not in providers:
        raise ValueError(f"Unknown provider '{provider_name}'. Choose from: {list(providers.keys())}")
    return providers[provider_name](model=model, **kwargs)
