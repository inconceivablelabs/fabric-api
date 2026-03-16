import httpx
import pytest
import respx

from fabric_client.exceptions import (
    AuthenticationError,
    FabricAPIError,
    NotFoundError,
    RateLimitError,
)
from fabric_client.http import FabricHTTP


@pytest.fixture
def http(api_key, base_url):
    return FabricHTTP(api_key=api_key, base_url=base_url)


@respx.mock
async def test_get_sends_api_key_header(http, base_url, api_key):
    route = respx.get(f"{base_url}/resource-roots").mock(
        return_value=httpx.Response(200, json=[])
    )
    await http.get("/resource-roots")
    assert route.called
    request = route.calls[0].request
    assert request.headers["X-Api-Key"] == api_key


@respx.mock
async def test_post_sends_json_body(http, base_url):
    route = respx.post(f"{base_url}/search").mock(
        return_value=httpx.Response(200, json={"hits": []})
    )
    body = {"text": "hello", "mode": "hybrid"}
    await http.post("/search", json=body)
    assert route.called
    import json

    assert json.loads(route.calls[0].request.content) == body


@respx.mock
async def test_workspace_id_header(api_key, base_url):
    http = FabricHTTP(api_key=api_key, base_url=base_url, workspace_id="ws-123")
    route = respx.get(f"{base_url}/users/me").mock(
        return_value=httpx.Response(200, json={})
    )
    await http.get("/users/me")
    request = route.calls[0].request
    assert request.headers["X-Fabric-Workspace-Id"] == "ws-123"


@respx.mock
async def test_404_raises_not_found(http, base_url):
    respx.get(f"{base_url}/resources/bad-id").mock(
        return_value=httpx.Response(
            404, json={"title": "Not Found", "detail": "resource_not_found"}
        )
    )
    with pytest.raises(NotFoundError) as exc_info:
        await http.get("/resources/bad-id")
    assert exc_info.value.detail == "resource_not_found"


@respx.mock
async def test_429_raises_rate_limit_with_retry_after(http, base_url):
    respx.get(f"{base_url}/search").mock(
        return_value=httpx.Response(
            429,
            json={"title": "Too Many Requests", "detail": "rate_limited"},
            headers={"Retry-After": "60"},
        )
    )
    with pytest.raises(RateLimitError) as exc_info:
        await http.get("/search")
    assert exc_info.value.retry_after == 60.0


@respx.mock
async def test_401_raises_authentication_error(http, base_url):
    respx.get(f"{base_url}/users/me").mock(
        return_value=httpx.Response(
            401, json={"title": "Unauthorized", "detail": "invalid_key"}
        )
    )
    with pytest.raises(AuthenticationError):
        await http.get("/users/me")


@respx.mock
async def test_5xx_retries_then_raises(http, base_url):
    route = respx.get(f"{base_url}/tags").mock(
        return_value=httpx.Response(
            502, json={"title": "Bad Gateway", "detail": "bad_gateway"}
        )
    )
    with pytest.raises(FabricAPIError) as exc_info:
        await http.get("/tags")
    assert exc_info.value.status_code == 502
    # Should have retried (1 initial + 2 retries = 3 attempts with max_retries=3)
    assert route.call_count == 3


@respx.mock
async def test_get_text_returns_raw_string(http, base_url):
    respx.get(f"{base_url}/notepads/abc/content").mock(
        return_value=httpx.Response(
            200,
            text="# My Note\nSome content here",
            headers={"Content-Type": "text/plain"},
        )
    )
    result = await http.get_text("/notepads/abc/content")
    assert result == "# My Note\nSome content here"
