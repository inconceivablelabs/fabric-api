from fabric_client.exceptions import (
    AuthenticationError,
    FabricAPIError,
    FabricError,
    NotFoundError,
    RateLimitError,
)


def test_fabric_error_is_base():
    err = FabricError("something broke")
    assert isinstance(err, Exception)
    assert str(err) == "something broke"


def test_api_error_has_status_and_detail():
    err = FabricAPIError(status_code=500, detail="internal_error")
    assert err.status_code == 500
    assert err.detail == "internal_error"
    assert isinstance(err, FabricError)


def test_not_found_error():
    err = NotFoundError(detail="resource_not_found")
    assert err.status_code == 404
    assert isinstance(err, FabricAPIError)


def test_rate_limit_error_with_retry_after():
    err = RateLimitError(detail="rate_limited", retry_after=30.0)
    assert err.status_code == 429
    assert err.retry_after == 30.0


def test_rate_limit_error_without_retry_after():
    err = RateLimitError(detail="rate_limited")
    assert err.retry_after is None


def test_authentication_error():
    err = AuthenticationError(detail="invalid_key")
    assert err.status_code == 401
    assert isinstance(err, FabricAPIError)
