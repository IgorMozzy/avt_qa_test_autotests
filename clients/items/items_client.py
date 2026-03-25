import allure
from httpx import Response

from clients.api_client import APIClient
from clients.http_builder import get_http_client
from clients.items.items_schema import CreateItemRequestSchema, CreateItemResponseSchema
from tools.routes import APIRoutes


class ItemsClient(APIClient):
    """Клиент для работы с эндпоинтами объявлений."""

    @allure.step("Создать объявление")
    def create_item_api(self, request: CreateItemRequestSchema) -> Response:
        """Создает объявление."""
        return self.post(APIRoutes.CREATE_ITEM, json=request.model_dump(by_alias=True))

    def create_item(self, request: CreateItemRequestSchema) -> str:
        """Создает объявление и возвращает ID из ответа API."""
        response = self.create_item_api(request)
        return CreateItemResponseSchema.model_validate_json(response.text).id

    @allure.step("Получить объявление {item_id}")
    def get_item_api(self, item_id: str) -> Response:
        """Получает объявление по ID."""
        return self.get(APIRoutes.GET_ITEM.format(item_id=item_id))

    @allure.step("Получить объявления продавца {seller_id}")
    def get_seller_items_api(self, seller_id: int) -> Response:
        """Получает все объявления продавца."""
        return self.get(APIRoutes.GET_SELLER_ITEMS.format(seller_id=seller_id))

    @allure.step("Получить статистику v1 {item_id}")
    def get_statistic_v1_api(self, item_id: str) -> Response:
        """Получает статистику по объявлению (v1)."""
        return self.get(APIRoutes.GET_STATISTIC_V1.format(item_id=item_id))

    @allure.step("Получить статистику v2 {item_id}")
    def get_statistic_v2_api(self, item_id: str) -> Response:
        """Получает статистику по объявлению (v2)."""
        return self.get(APIRoutes.GET_STATISTIC_V2.format(item_id=item_id))

    @allure.step("Удалить объявление {item_id}")
    def delete_item_api(self, item_id: str) -> Response:
        """Удаляет объявление по ID."""
        return self.delete(APIRoutes.DELETE_ITEM.format(item_id=item_id))


def get_items_client() -> ItemsClient:
    """Создает экземпляр ItemsClient с настроенным HTTP-клиентом."""
    return ItemsClient(client=get_http_client())
