import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def requests_session_with_retries(
    retries: int = 5,
    backoff_factor: float = 0.5,
    status_forcelist: tuple = (429, 500, 502, 503, 504),
    timeout: int = 10,
) -> requests.Session:
    """
    Create a requests.Session with retry support.
    Retries on common transient errors (5xx, 429).
    """
    session = requests.Session()

    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["HEAD", "GET", "OPTIONS"],  # safe to retry
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Wrap session.get with timeout
    original_get = session.get

    def get_with_timeout(*args, **kwargs):
        kwargs.setdefault("timeout", timeout)
        return original_get(*args, **kwargs)

    session.get = get_with_timeout
    return session

