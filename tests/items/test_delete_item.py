from http import HTTPStatus

import allure
import pytest
from allure_commons.types import Severity

from clients.errors_schema import ErrorResponseSchema, ObjectErrorResponseSchema
from clients.items.items_client import ItemsClient
from clients.items.items_schema import ItemSchema
from fixtures.items import ItemFixture
from tools.allure.epics import AllureEpic
from tools.allure.features import AllureFeature
from tools.allure.stories import AllureStory
from tools.allure.tags import AllureTag
from tools.assertions.base import assert_error_response, assert_is_true, assert_status_code
from tools.assertions.errors import APIErrorMessage
from tools.assertions.schema import validate_json_schema
from tools.fakers import fake


@pytest.mark.items
@pytest.mark.regression
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.DELETE_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestDeleteItem:
    @pytest.mark.smoke
    @allure.tag(AllureTag.SMOKE)
    @allure.story(AllureStory.DELETE_ITEM)
    @allure.title("Positive: Удаление существующего объявления")
    @allure.severity(Severity.BLOCKER)
    @allure.sub_suite(AllureStory.DELETE_ITEM)
    def test_delete_item(self, items_client: ItemsClient, function_item: ItemFixture) -> None:
        response = items_client.delete_item_api(function_item.item_id)

        assert_status_code(response.status_code, HTTPStatus.OK)

    @allure.story(AllureStory.DELETE_ITEM)
    @allure.title("Positive: После удаления GET возвращает 404")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.DELETE_ITEM)
    def test_get_after_delete_returns_404(self, items_client: ItemsClient, function_item: ItemFixture) -> None:
        items_client.delete_item_api(function_item.item_id)

        response = items_client.get_item_api(function_item.item_id)
        assert_status_code(response.status_code, HTTPStatus.NOT_FOUND)
        validate_json_schema(response.json(), ErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(
            response.json(), HTTPStatus.NOT_FOUND, APIErrorMessage.GET_ITEM_NOT_FOUND.format(id=function_item.item_id)
        )

    @allure.story(AllureStory.DELETE_ITEM)
    @allure.title("Positive: После удаления объявление отсутствует в списке продавца")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.DELETE_ITEM)
    def test_delete_item_not_in_seller_list(self, items_client: ItemsClient, function_item: ItemFixture) -> None:
        items_client.delete_item_api(function_item.item_id)

        response = items_client.get_seller_items_api(function_item.seller_id)
        assert_status_code(response.status_code, HTTPStatus.OK)
        item_ids = {ItemSchema.model_validate(item).id for item in response.json()}
        assert_is_true(
            function_item.item_id not in item_ids,
            "Удалённое объявление не должно быть в списке продавца",
        )


@pytest.mark.items
@pytest.mark.regression
@pytest.mark.negative
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.NEGATIVE, AllureTag.DELETE_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestDeleteItemNegative:
    @allure.story(AllureStory.DELETE_ITEM)
    @allure.title("Negative: Повторное удаление одного объявления возвращает 404")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.DELETE_ITEM)
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-4: DELETE /item/:id для несуществующего/удалённого ID возвращает body status '500' вместо '404'",
    )
    def test_delete_item_twice(self, items_client: ItemsClient, function_item: ItemFixture) -> None:
        items_client.delete_item_api(function_item.item_id)

        response = items_client.delete_item_api(function_item.item_id)
        assert_status_code(response.status_code, HTTPStatus.NOT_FOUND)

        validate_json_schema(response.json(), ErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(
            response.json(),
            HTTPStatus.NOT_FOUND,
            APIErrorMessage.DELETE_ITEM_NOT_FOUND.format(id=function_item.item_id),
        )

    @allure.story(AllureStory.DELETE_ITEM)
    @allure.title("Negative: Удаление с невалидным ID")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.DELETE_ITEM)
    def test_delete_item_invalid_id(self, items_client: ItemsClient) -> None:
        response = items_client.delete_item_api("invalid-id")

        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, APIErrorMessage.DELETE_ITEM_INVALID_ID)

    @allure.story(AllureStory.DELETE_ITEM)
    @allure.title("Negative: Удаление объявления по случайному несуществующему UUID")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.DELETE_ITEM)
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-4: DELETE /item/:id для несуществующего/удалённого ID возвращает body status '500' вместо '404'",
    )
    def test_delete_item_random_uuid(self, items_client: ItemsClient) -> None:
        random_id = fake.uuid4()
        response = items_client.delete_item_api(random_id)

        assert_status_code(response.status_code, HTTPStatus.NOT_FOUND)

        validate_json_schema(response.json(), ErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(
            response.json(), HTTPStatus.NOT_FOUND, APIErrorMessage.DELETE_ITEM_NOT_FOUND.format(id=random_id)
        )
