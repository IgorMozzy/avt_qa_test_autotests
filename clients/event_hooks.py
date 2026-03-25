import json

import allure
from httpx import Request, Response

from tools.http.curl import make_curl_from_request
from tools.logger import get_logger

logger = get_logger("HTTP_CLIENT")


def curl_event_hook(request: Request) -> None:
    """Прикрепляет cURL команду к Allure отчету."""
    curl_command = make_curl_from_request(request)
    allure.attach(curl_command, "cURL command", allure.attachment_type.TEXT)


def log_request_event_hook(request: Request) -> None:
    """Логирует информацию об отправленном HTTP-запросе."""
    logger.info("Отправлен %s запрос к %s", request.method, request.url)


def log_response_event_hook(response: Response) -> None:
    """Логирует информацию о полученном HTTP-ответе."""
    logger.info("Получен ответ %s %s от %s", response.status_code, response.reason_phrase, response.url)


def allure_response_hook(response: Response) -> None:
    response.read()
    try:
        body = response.json()
        formatted_body = json.dumps(body, indent=2, ensure_ascii=False)
    except ValueError:
        formatted_body = response.text

    allure.attach(
        formatted_body,
        name=f"Response {response.status_code}",
        attachment_type=allure.attachment_type.JSON,
    )
