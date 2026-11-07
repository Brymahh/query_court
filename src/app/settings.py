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
    azure_openai_deployment_name:
            Optional Azure OpenAI deployment name.
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
    azure_openai_deployment_name: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_DEPLOYMENT_NAME",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="QUERY_COURT_",
        extra="ignore",
    )
