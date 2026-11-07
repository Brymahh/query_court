from app.settings import Settings


def test_settings_load_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("QUERY_COURT_APP_NAME", "Test API")
    monkeypatch.setenv("QUERY_COURT_ENVIRONMENT", "test")

    settings = Settings()

    assert settings.app_name == "Test API"
    assert settings.environment == "test"


def test_settings_load_azure_openai_environment(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "test-deployment")

    settings = Settings()

    assert settings.azure_openai_api_key is not None
    assert settings.azure_openai_api_key.get_secret_value() == "test-key"
    assert settings.azure_openai_endpoint == "https://example.openai.azure.com"
    assert settings.azure_openai_deployment_name == "test-deployment"
