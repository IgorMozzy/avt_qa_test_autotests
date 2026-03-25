from typing import Any

import allure
from httpx import URL, Client, QueryParams, Response


class APIClient:
    def __init__(self, client: Client) -> None:
        self.client = client

    @allure.step("Выполнить {method}-запрос к {url}")
    def request(self, method: str, url: URL | str, **kwargs: Any) -> Response:
        """Выполняет HTTP-запрос с произвольным методом."""
        return self.client.request(method, url, **kwargs)

    @allure.step("Выполнить GET-запрос к {url}")
    def get(self, url: URL | str, params: QueryParams | None = None) -> Response:
        """Выполняет GET-запрос."""
        return self.client.get(url, params=params)

    @allure.step("Выполнить POST-запрос к {url}")
    def post(self, url: URL | str, json: Any | None = None) -> Response:
        """Выполняет POST-запрос."""
        return self.client.post(url, json=json)

    @allure.step("Выполнить DELETE-запрос к {url}")
    def delete(self, url: URL | str) -> Response:
        """Выполняет DELETE-запрос."""
        return self.client.delete(url)
