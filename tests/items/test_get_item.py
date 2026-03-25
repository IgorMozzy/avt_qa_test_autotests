from datetime import datetime
from http import HTTPStatus

import allure
import pytest
from allure_commons.types import Severity

from clients.errors_schema import ErrorResponseSchema, ObjectErrorResponseSchema
from clients.items.items_client import ItemsClient
from clients.items.items_schema import GetItemResponseSchema, ItemSchema
from fixtures.items import ItemFixture
from tools.allure.epics import AllureEpic
from tools.allure.features import AllureFeature
from tools.allure.stories import AllureStory
from tools.allure.tags import AllureTag
from tools.assertions.base import (
    assert_error_response,
    assert_is_true,
    assert_list_length,
    assert_status_code,
)
from tools.assertions.errors import APIErrorMessage
from tools.assertions.items import assert_create_item_response, assert_item
from tools.assertions.schema import validate_json_schema


@pytest.mark.items
@pytest.mark.regression
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.GET_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestGetItem:
    @pytest.mark.smoke
    @allure.tag(AllureTag.SMOKE)
    @allure.story(AllureStory.GET_ITEM)
    @allure.title("Positive: Получение объявления по ID")
    @allure.severity(Severity.BLOCKER)
    @allure.sub_suite(AllureStory.GET_ITEM)
    def test_get_item_by_id(
        self,
        items_client: ItemsClient,
        function_item_with_cleanup: ItemFixture,
    ) -> None:
        item = function_item_with_cleanup
        response = items_client.get_item_api(item.item_id)
        assert_status_code(response.status_code, HTTPStatus.OK)

        items = GetItemResponseSchema.model_validate_json(response.text)
        assert_list_length(items.root, 1, "get item response")
        assert_create_item_response(item.request, items.root[0])
        validate_json_schema(response.json()[0], ItemSchema.model_json_schema(), strict=True)

    @allure.story(AllureStory.GET_ITEM)
    @allure.title("Positive: Поле createdAt содержит валидную дату в формате ISO 8601")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.GET_ITEM)
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-9: createdAt содержит дублированный таймзон",
    )
    def test_created_at_is_valid_iso8601(
        self,
        items_client: ItemsClient,
        function_item_with_cleanup: ItemFixture,
    ) -> None:
        item = function_item_with_cleanup
        response = items_client.get_item_api(item.item_id)
        items = GetItemResponseSchema.model_validate_json(response.text)
        datetime.fromisoformat(items.root[0].created_at)

    @allure.story(AllureStory.GET_ITEM)
    @allure.title("Positive: GET /item/:id возвращает объект, а не массив")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.GET_ITEM)
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-7: GET /item/:id возвращает массив вместо единичного объекта",
    )
    def test_get_item_returns_object_not_array(
        self,
        items_client: ItemsClient,
        function_item_with_cleanup: ItemFixture,
    ) -> None:
        response = items_client.get_item_api(function_item_with_cleanup.item_id)
        assert_status_code(response.status_code, HTTPStatus.OK)
        assert_is_true(isinstance(response.json(), dict), "Ответ GET /item/:id должен быть объектом, а не массивом")

    @allure.story(AllureStory.GET_ITEM)
    @allure.title("Positive: Идемпотентность GET: два запроса возвращают одинаковый результат")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.GET_ITEM)
    def test_get_item_idempotency(
        self,
        items_client: ItemsClient,
        function_item_with_cleanup: ItemFixture,
    ) -> None:
        item = function_item_with_cleanup
        response_1 = items_client.get_item_api(item.item_id)
        response_2 = items_client.get_item_api(item.item_id)

        assert_status_code(response_1.status_code, HTTPStatus.OK)
        assert_status_code(response_2.status_code, HTTPStatus.OK)

        items_1 = GetItemResponseSchema.model_validate_json(response_1.text)
        items_2 = GetItemResponseSchema.model_validate_json(response_2.text)
        assert_list_length(items_1.root, 1, "get item response 1")
        assert_list_length(items_2.root, 1, "get item response 2")
        assert_item(items_1.root[0], items_2.root[0])


@pytest.mark.items
@pytest.mark.regression
@pytest.mark.negative
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.NEGATIVE, AllureTag.GET_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestGetItemNegative:
    @allure.story(AllureStory.GET_ITEM)
    @allure.title("Negative: Получение объявления с несуществующим ID")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.GET_ITEM)
    def test_get_item_not_found(self, items_client: ItemsClient, function_item_with_cleanup: ItemFixture) -> None:
        items_client.delete_item_api(function_item_with_cleanup.item_id)
        response = items_client.get_item_api(function_item_with_cleanup.item_id)

        assert_status_code(response.status_code, HTTPStatus.NOT_FOUND)

        validate_json_schema(response.json(), ErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(
            response.json(),
            HTTPStatus.NOT_FOUND,
            APIErrorMessage.GET_ITEM_NOT_FOUND.format(id=function_item_with_cleanup.item_id),
        )

    @allure.story(AllureStory.GET_ITEM)
    @allure.title("Negative: Получение объявления с невалидным форматом ID")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.GET_ITEM)
    def test_get_item_invalid_id(self, items_client: ItemsClient) -> None:
        response = items_client.get_item_api("invalid-id-format")

        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(
            response.json(), HTTPStatus.BAD_REQUEST, APIErrorMessage.GET_ITEM_INVALID_ID.format(id="invalid-id-format")
        )

    @pytest.mark.security
    @allure.story(AllureStory.GET_ITEM)
    @allure.title("Security: GET /item/:id с SQL-инъекцией в ID возвращает 400, не 500")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.GET_ITEM)
    def test_get_item_sql_injection_in_path(self, items_client: ItemsClient) -> None:
        response = items_client.get_item_api("'; DROP TABLE items; --")

        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)
