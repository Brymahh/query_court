from unittest.mock import Mock, patch

from pydantic import SecretStr

from app.providers.azure import (
    AzureModelConfig,
    AzureModelProvider,
)


@patch("app.providers.azure.OpenAI")
def test_azure_provider_returns_model_text(
    openai_mock: Mock,
) -> None:
    response = Mock()
    response.output_text = "SELECT name FROM customers"

    openai_mock.return_value.responses.create.return_value = response

    provider = AzureModelProvider(
        AzureModelConfig(
            endpoint="https://example.openai.azure.com/openai/v1/",
            api_key=SecretStr("test-key"),
            deployment_name="generator-model",
        )
    )

    result = provider.complete(
        system_prompt="Generate SQL.",
        user_prompt="Find customer names.",
    )

    assert result == "SELECT name FROM customers"
