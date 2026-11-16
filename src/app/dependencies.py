"""Application dependency composition."""

from app.providers.fake import FakeModelProvider
from app.workflow.agents import SQLCriticAgent, SQLGeneratorAgent
from app.workflow.event_source import GraphEventSource


def build_development_event_source() -> GraphEventSource:
    """Build a deterministic local workflow without Azure calls."""
    generator_provider = FakeModelProvider(
        responses=["SELECT name FROM customers"],
    )

    critic_provider = FakeModelProvider(
        responses=["The SQL is valid and read-only."],
    )

    generator = SQLGeneratorAgent(generator_provider)
    critic = SQLCriticAgent(critic_provider)

    return GraphEventSource(
        generator=generator,
        critic=critic,
    )
