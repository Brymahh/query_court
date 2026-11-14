from unittest.mock import Mock, patch

import pytest
from pydantic import SecretStr

from app.providers import (
    AzureModelConfig,
    AzureModelProvider,
    FakeModelProvider,
    ModelProviderError,
)


def test_fake_provider_returns_configured_response() -> None:
    provider = FakeModelProvider(
        responses=["SELECT name FROM customers"],
    )

    result = provider.complete(
        system_prompt="Generate PostgreSQL SQL.",
        user_prompt="Find customer names.",
    )

    assert result == "SELECT name FROM customers"


def test_fake_provider_returns_responses_in_order() -> None:
    provider = FakeModelProvider(
        responses=["first response", "second response"],
    )

    first = provider.complete(
        system_prompt="system",
        user_prompt="first",
    )
    second = provider.complete(
        system_prompt="system",
        user_prompt="second",
    )

    assert first == "first response"
    assert second == "second response"


def test_fake_provider_fails_when_responses_are_exhausted() -> None:
    provider = FakeModelProvider(responses=[])

    with pytest.raises(ModelProviderError):
        provider.complete(
            system_prompt="system",
            user_prompt="user",
        )


@patch("app.providers.azure.OpenAI")
def test_azure_provider_uses_deployment_configuration(
    openai: Mock,
) -> None:
    config = AzureModelConfig(
        endpoint="https://example.openai.azure.com",
        api_key=SecretStr("test-key"),
        deployment_name="critic-model",
    )

    AzureModelProvider(config)

    openai.assert_called_once_with(
        base_url="https://example.openai.azure.com",
        api_key="test-key",
    )


@patch("app.providers.azure.OpenAI")
def test_azure_provider_sends_prompts(
    openai: Mock,
) -> None:
    response = Mock()
    response.output_text = "SELECT name FROM customers"

    client = openai.return_value
    client.responses.create.return_value = response

    provider = AzureModelProvider(
        AzureModelConfig(
            endpoint="https://example.openai.azure.com",
            api_key=SecretStr("test-key"),
            deployment_name="generator-model",
        )
    )

    result = provider.complete(
        system_prompt="Generate PostgreSQL SQL.",
        user_prompt="Find customer names.",
    )

    assert result == "SELECT name FROM customers"
    client.responses.create.assert_called_once_with(
        model="generator-model",
        input=[
            {"role": "system", "content": "Generate PostgreSQL SQL."},
            {"role": "user", "content": "Find customer names."},
        ],
    )
