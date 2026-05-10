from eolchecker.helper import requests_session_with_retries


def test_requests_session_with_retries_mounts_http_and_https_adapters():
    session = requests_session_with_retries(timeout=7)

    assert "http://" in session.adapters
    assert "https://" in session.adapters
    assert callable(session.get)
