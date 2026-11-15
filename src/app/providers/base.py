"""Interfaces for model providers."""

from typing import Protocol


class ModelProviderError(RuntimeError):
    """Raised when a model provider cannot return a response."""


class ModelProvider(Protocol):
    """Interface shared by hosted and local model providers."""

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Return a model response for the supplied prompts."""
        ...
