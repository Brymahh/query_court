"""Azure OpenAI model provider."""

from dataclasses import dataclass

from openai import OpenAI
from pydantic import SecretStr

from app.providers.base import ModelProviderError


@dataclass(frozen=True)
class AzureModelConfig:
    """Configuration for one Azure-hosted model deployment."""

    endpoint: str
    api_key: SecretStr
    deployment_name: str


class AzureModelProvider:
    """Call one Azure-hosted model through an OpenAI-compatible endpoint."""

    def __init__(self, config: AzureModelConfig) -> None:
        """Create a model provider.

        Parameters
        ----------
        config:
            Endpoint, API key, and deployment configuration.
        """
        self._deployment_name = config.deployment_name
        self._client = OpenAI(
            base_url=config.endpoint,
            api_key=config.api_key.get_secret_value(),
        )

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Send a prompt to the configured model deployment.

        Parameters
        ----------
        system_prompt:
            System instruction for the model.
        user_prompt:
            User request for the model.

        Returns
        -------
        str
            Model response text.

        Raises
        ------
        ModelProviderError
            If the model request fails or returns no text.
        """
        try:
            response = self._client.responses.create(
                model=self._deployment_name,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
            )
        except Exception as error:
            raise ModelProviderError(
                "Azure model request failed.",
            ) from error

        if not response.output_text:
            raise ModelProviderError(
                "Azure model returned an empty response.",
            )

        return response.output_text
