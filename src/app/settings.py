from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes
    ----------
    app_name:
            Name displayed by the FastAPI application.
    environment:
            Runtime environment name, such as ``development``.
    azure_openai_api_key:
            Optional Azure OpenAI API key, loaded from ``AZURE_OPENAI_API_KEY``.
    azure_openai_endpoint:
            Optional Azure OpenAI resource endpoint.
    azure_openai_generator_deployment_name:
            Optional Azure OpenAI deployment name for the generator.
    azure_openai_critic_deployment_name:
            Optional Azure OpenAI deployment name for the critic.
    """

    app_name: str = "Query-Court"
    environment: str = "development"

    azure_openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_API_KEY",
    )

    azure_openai_endpoint: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_ENDPOINT",
    )

    azure_openai_generator_deployment_name: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_GENERATOR_DEPLOYMENT_NAME",
    )

    azure_openai_critic_deployment_name: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_CRITIC_DEPLOYMENT_NAME",
    )

    model_provider: Literal["azure", "fake"] = Field(
        default="azure",
        validation_alias="MODEL_PROVIDER",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="QUERY_COURT_",
        extra="ignore",
    )
