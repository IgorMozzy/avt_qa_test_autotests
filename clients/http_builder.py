from httpx import Client

from clients.event_hooks import allure_response_hook, curl_event_hook, log_request_event_hook, log_response_event_hook
from config import settings


def get_http_client() -> Client:
    """Создает экземпляр httpx.Client с базовыми настройками."""
    return Client(
        timeout=settings.http_client.timeout,
        base_url=settings.http_client.client_url,
        event_hooks={
            "request": [curl_event_hook, log_request_event_hook],
            "response": [log_response_event_hook, allure_response_hook],
        },
    )
