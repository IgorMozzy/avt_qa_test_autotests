import allure

from clients.items.items_schema import CreateItemRequestSchema, ItemSchema, StatisticsSchema
from tools.assertions.base import assert_equal, assert_is_uuid
from tools.logger import get_logger

logger = get_logger("ITEMS_ASSERTIONS")


@allure.step("Проверить ответ создания объявления")
def assert_create_item_response(request: CreateItemRequestSchema, response: ItemSchema) -> None:
    """Проверяет, что ответ на создание объявления соответствует запросу."""
    logger.info("Проверить ответ создания объявления")

    assert_is_uuid(response.id)
    assert_equal(response.seller_id, request.seller_id, "sellerId")
    assert_equal(response.name, request.name, "name")
    assert_equal(response.price, request.price, "price")
    assert_statistic(response.statistics, request.statistics)


@allure.step("Проверить соответствие объявления")
def assert_item(actual: ItemSchema, expected: ItemSchema) -> None:
    """Проверяет, что объявление соответствует ожидаемому."""
    logger.info("Проверить соответствие объявления")

    assert_equal(actual.id, expected.id, "id")
    assert_equal(actual.seller_id, expected.seller_id, "sellerId")
    assert_equal(actual.name, expected.name, "name")
    assert_equal(actual.price, expected.price, "price")
    assert_statistic(actual.statistics, expected.statistics)


@allure.step("Проверить соответствие статистики")
def assert_statistic(actual: StatisticsSchema, expected: StatisticsSchema) -> None:
    """Проверяет, что статистика соответствует ожидаемой."""
    logger.info("Проверить соответствие статистики")

    assert_equal(actual.likes, expected.likes, "likes")
    assert_equal(actual.view_count, expected.view_count, "viewCount")
    assert_equal(actual.contacts, expected.contacts, "contacts")
