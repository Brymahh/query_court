"""Application dependency composition."""

from app.providers.azure import AzureModelConfig, AzureModelProvider
from app.providers.fake import FakeModelProvider
from app.settings import Settings
from app.workflow.agents import SQLCriticAgent, SQLGeneratorAgent
from app.workflow.event_source import GraphEventSource


def build_event_source(settings: Settings) -> GraphEventSource:
    """Build the configured review event source.

    Parameters
    ----------
    settings:
        Application settings.

    Returns
    -------
    GraphEventSource
        Event source using fake or Azure model providers.

    Raises
    ------
    ValueError
        If an unsupported provider is configured.
    """
    if settings.model_provider == "fake":
        return build_development_event_source()

    if settings.model_provider == "azure":
        return build_azure_event_source(settings)

    raise ValueError(f"Unsupported model provider: {settings.model_provider}")


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


def _require_setting[SettingValue](
    value: SettingValue | None,
    name: str,
) -> SettingValue:
    """Return a required setting or raise a clear configuration error.

    Parameters
    ----------
    value:
        Optional configuration value.
    name:
        Environment variable name used in the error message.

    Returns
    -------
    SettingValue
        The validated configuration value.

    Raises
    ------
    ValueError
        If the configuration value is missing.
    """
    if value is None:
        raise ValueError(
            f"Missing required setting: {name}",
        )

    if isinstance(value, str) and not value.strip():
        raise ValueError(
            f"Setting cannot be empty: {name}",
        )

    return value


def build_azure_event_source(
    settings: Settings,
) -> GraphEventSource:
    """Build the workflow using separate Azure generator and critic models.

    Parameters
    ----------
    settings:
        Application settings containing Azure configuration.

    Returns
    -------
    GraphEventSource
        Workflow connected to Azure model deployments.

    Raises
    ------
    ValueError
        If required Azure settings are missing.
    """
    endpoint = _require_setting(
        settings.azure_openai_endpoint,
        "AZURE_OPENAI_ENDPOINT",
    )

    api_key = _require_setting(
        settings.azure_openai_api_key,
        "AZURE_OPENAI_API_KEY",
    )

    generator_deployment = _require_setting(
        settings.azure_openai_generator_deployment_name,
        "AZURE_OPENAI_GENERATOR_DEPLOYMENT_NAME",
    )

    critic_deployment = _require_setting(
        settings.azure_openai_critic_deployment_name,
        "AZURE_OPENAI_CRITIC_DEPLOYMENT_NAME",
    )

    generator_provider = AzureModelProvider(
        AzureModelConfig(
            endpoint=endpoint,
            api_key=api_key,
            deployment_name=generator_deployment,
        )
    )

    critic_provider = AzureModelProvider(
        AzureModelConfig(
            endpoint=endpoint,
            api_key=api_key,
            deployment_name=critic_deployment,
        )
    )

    return GraphEventSource(
        generator=SQLGeneratorAgent(generator_provider),
        critic=SQLCriticAgent(critic_provider),
    )
    # required_values = {
    #     "AZURE_OPENAI_API_KEY": settings.azure_openai_api_key,
    #     "AZURE_OPENAI_ENDPOINT": settings.azure_openai_endpoint,
    #     "AZURE_OPENAI_GENERATOR_DEPLOYMENT_NAME": (
    # settings.azure_openai_generator_deployment_name),
    #     "AZURE_OPENAI_CRITIC_DEPLOYMENT_NAME": (
    # settings.azure_openai_critic_deployment_name),}

    # missing_values = [name for name, value in required_values.items() if value is None]

    # if missing_values:
    #     raise ValueError("Missing Azure configuration: " + ", ".join(missing_values))

    # generator_provider = AzureModelProvider(
    #     AzureModelConfig(
    #         endpoint=settings.azure_openai_endpoint,
    #         api_key=settings.azure_openai_api_key,
    #         deployment_name=(settings.azure_openai_generator_deployment_name),
    #     )
    # )

    # critic_provider = AzureModelProvider(
    #     AzureModelConfig(
    #         endpoint=settings.azure_openai_endpoint,
    #         api_key=settings.azure_openai_api_key,
    #         deployment_name=settings.azure_openai_critic_deployment_name,
    #     )
    # )

    # return GraphEventSource(
    #     generator=SQLGeneratorAgent(generator_provider),
    #     critic=SQLCriticAgent(critic_provider),
    # )
