"""Load prompt templates from YAML."""

from functools import cache
from importlib.resources import files

import yaml
from pydantic import BaseModel


class PromptConfig(BaseModel):
    """Prompt templates used by the review agents."""

    generator: str
    critic: str


@cache
def load_prompts() -> PromptConfig:
    """Read and validate the prompt file once."""
    text = files("app").joinpath("prompts/prompts.yaml").read_text(encoding="utf-8")
    return PromptConfig.model_validate(yaml.safe_load(text))
