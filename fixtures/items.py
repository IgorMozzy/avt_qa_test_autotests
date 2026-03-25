from collections.abc import Generator
from http import HTTPStatus
from typing import Any

import allure
import pytest
from httpx import Response
from pydantic import BaseModel

from clients.items.items_client import ItemsClient, get_items_client
from clients.items.items_schema import CreateItemRequestSchema, CreateItemResponseSchema
from tools.logger import get_logger

logger = get_logger("FIXTURES")


class ItemFixture(BaseModel):
    request: CreateItemRequestSchema
    item_id: str

    @property
    def seller_id(self) -> int:
        return self.request.seller_id


def try_cleanup_on_unexpected_success(response: Response, cleanup_items: list[str]) -> None:
    """Если API неожиданно вернул 200, извлекаем ID созданного объявления для очистки."""
    if response.status_code == HTTPStatus.OK:
        try:
            data = CreateItemResponseSchema.model_validate_json(response.text)
            cleanup_items.append(data.id)
        except Exception:
            logger.warning("Cleanup: не удалось извлечь ID из ответа 200 для очистки")


@allure.step("Cleanup: удалить объявление {item_id}")
def _safe_delete(items_client: ItemsClient, item_id: str) -> None:
    try:
        response = items_client.delete_item_api(item_id)
        if response.status_code != HTTPStatus.OK:
            logger.warning(
                "Cleanup: не удалось удалить объявление %s, status=%s",
                item_id,
                response.status_code,
            )
    except Exception:
        logger.exception("Cleanup: исключение при удалении объявления %s", item_id)


@pytest.fixture(scope="session")
def items_client() -> Generator[ItemsClient]:
    """Создает клиент для работы с объявлениями. Один на всю сессию."""
    client = get_items_client()
    try:
        yield client
    finally:
        client.client.close()


@pytest.fixture
def function_item(items_client: ItemsClient) -> ItemFixture:
    """Создает объявление для теста. Без автоматической очистки."""
    request = CreateItemRequestSchema()
    item_id = items_client.create_item(request)
    return ItemFixture(request=request, item_id=item_id)


@pytest.fixture
def function_item_with_cleanup(items_client: ItemsClient) -> Generator[ItemFixture]:
    """Создает объявление для теста с автоматическим удалением после завершения."""
    request = CreateItemRequestSchema()
    item_id = items_client.create_item(request)
    fixture = ItemFixture(request=request, item_id=item_id)
    yield fixture
    _safe_delete(items_client, item_id)


@pytest.fixture
def cleanup_items(items_client: ItemsClient) -> Generator[list[str]]:
    """Собирает ID объявлений для удаления после теста."""
    ids: list[str] = []
    yield ids
    if ids:
        with allure.step(f"Cleanup: удалить {len(ids)} объявлений"):
            for item_id in ids:
                _safe_delete(items_client, item_id)


@pytest.fixture
def valid_item_payload() -> dict[str, Any]:
    """Генерирует валидный пейлоад из Pydantic-модели."""
    return CreateItemRequestSchema().model_dump(by_alias=True)
