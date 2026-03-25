from http import HTTPStatus

import allure
import pytest
from allure_commons.types import Severity

from clients.errors_schema import ObjectErrorResponseSchema
from clients.items.items_client import ItemsClient
from clients.items.items_schema import CreateItemRequestSchema, GetItemResponseSchema, ItemSchema
from tools.allure.epics import AllureEpic
from tools.allure.features import AllureFeature
from tools.allure.stories import AllureStory
from tools.allure.tags import AllureTag
from tools.assertions.base import assert_error_response, assert_is_true, assert_list_length, assert_status_code
from tools.assertions.errors import APIErrorMessage
from tools.assertions.schema import validate_json_schema
from tools.fakers import fake
from tools.routes import APIRoutes


@pytest.mark.items
@pytest.mark.regression
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.GET_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestGetSellerItems:
    @pytest.mark.smoke
    @allure.tag(AllureTag.SMOKE)
    @allure.story(AllureStory.GET_SELLER_ITEMS)
    @allure.title("Positive: Получение всех объявлений продавца")
    @allure.severity(Severity.BLOCKER)
    @allure.sub_suite(AllureStory.GET_SELLER_ITEMS)
    def test_get_seller_items(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        seller_id = fake.seller_id()
        request_1 = CreateItemRequestSchema(seller_id=seller_id)
        request_2 = CreateItemRequestSchema(seller_id=seller_id)
        created_id_1 = items_client.create_item(request_1)
        created_id_2 = items_client.create_item(request_2)
        cleanup_items.extend([created_id_1, created_id_2])

        response = items_client.get_seller_items_api(seller_id)
        assert_status_code(response.status_code, HTTPStatus.OK)

        items = [ItemSchema.model_validate(item) for item in response.json()]
        created_ids = {created_id_1, created_id_2}
        found_ids = {item.id for item in items}

        assert_is_true(created_ids.issubset(found_ids), "Созданные объявления должны быть в списке продавца")
        validate_json_schema(response.json(), GetItemResponseSchema.model_json_schema(), strict=True)

    @allure.story(AllureStory.GET_SELLER_ITEMS)
    @allure.title("Positive: Получение объявлений продавца без объявлений")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.GET_SELLER_ITEMS)
    def test_get_seller_items_empty(self, items_client: ItemsClient) -> None:
        seller_id = fake.seller_id()
        response = items_client.get_seller_items_api(seller_id)

        assert_status_code(response.status_code, HTTPStatus.OK)
        assert_is_true(response.json() == [], "Список объявлений должен быть пустым")
        validate_json_schema(response.json(), GetItemResponseSchema.model_json_schema(), strict=True)

    @pytest.mark.regression
    @allure.story(AllureStory.GET_SELLER_ITEMS)
    @allure.title("Positive: Получение 50 объявлений продавца без пагинации")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.GET_SELLER_ITEMS)
    def test_get_seller_items_no_pagination(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        seller_id = fake.seller_id()
        count = 50

        for _ in range(count):
            request = CreateItemRequestSchema(seller_id=seller_id)
            cleanup_items.append(items_client.create_item(request))

        response = items_client.get_seller_items_api(seller_id)
        assert_status_code(response.status_code, HTTPStatus.OK)
        assert_list_length(response.json(), count, "seller items")


@pytest.mark.items
@pytest.mark.regression
@pytest.mark.negative
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.NEGATIVE, AllureTag.GET_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestGetSellerItemsNegative:
    @allure.story(AllureStory.GET_SELLER_ITEMS)
    @allure.title("Negative: Получение объявлений с невалидным sellerID (строка)")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.GET_SELLER_ITEMS)
    def test_get_seller_items_invalid_seller_id(self, items_client: ItemsClient) -> None:
        response = items_client.get(APIRoutes.GET_SELLER_ITEMS.format(seller_id="not_a_number"))

        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(
            response.json(), HTTPStatus.BAD_REQUEST, APIErrorMessage.GET_SELLER_ITEMS_INVALID_SELLER_ID
        )

    @allure.story(AllureStory.GET_SELLER_ITEMS)
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.GET_SELLER_ITEMS)
    @pytest.mark.parametrize(
        ("seller_id_str", "description"),
        [
            pytest.param("111111.5", "дробным числом", id="fractional"),
            pytest.param(
                str(2**53 + 1),
                "числом 2^53+1",
                id="too_large",
                marks=pytest.mark.xfail(
                    strict=True,
                    reason="BUG-20: GET /:sellerID/item принимает sellerID = 2^53+1 и возвращает 200 вместо 400",
                ),
            ),
        ],
    )
    def test_get_seller_items_invalid_seller_id_boundary(
        self,
        items_client: ItemsClient,
        seller_id_str: str,
        description: str,
    ) -> None:
        allure.dynamic.title(f"Negative: Получение объявлений с sellerID {description}")
        response = items_client.get(APIRoutes.GET_SELLER_ITEMS.format(seller_id=seller_id_str))

        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)
        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(
            response.json(), HTTPStatus.BAD_REQUEST, APIErrorMessage.GET_SELLER_ITEMS_INVALID_SELLER_ID
        )

    @allure.story(AllureStory.GET_SELLER_ITEMS)
    @allure.title("Negative: Получение объявлений с отрицательным sellerID")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.GET_SELLER_ITEMS)
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-3: GET /:sellerID/item с отрицательным sellerID возвращает 200 вместо 400",
    )
    def test_get_seller_items_negative_seller_id(self, items_client: ItemsClient) -> None:
        response = items_client.get_seller_items_api(-111111)

        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(
            response.json(), HTTPStatus.BAD_REQUEST, APIErrorMessage.GET_SELLER_ITEMS_INVALID_SELLER_ID
        )
