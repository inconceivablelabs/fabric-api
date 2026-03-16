import pytest


@pytest.fixture
def api_key():
    return "test-api-key-123"


@pytest.fixture
def base_url():
    return "https://api.fabric.so/v2"
