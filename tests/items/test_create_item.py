from http import HTTPStatus
from typing import Any

import allure
import pytest
from allure_commons.types import Severity

from clients.errors_schema import ObjectErrorResponseSchema
from clients.items.items_client import ItemsClient
from clients.items.items_schema import (
    CreateItemRequestSchema,
    CreateItemResponseSchema,
    GetItemResponseSchema,
    ItemSchema,
    StatisticsSchema,
)
from fixtures.items import try_cleanup_on_unexpected_success
from tools.allure.epics import AllureEpic
from tools.allure.features import AllureFeature
from tools.allure.stories import AllureStory
from tools.allure.tags import AllureTag
from tools.assertions.base import (
    assert_equal,
    assert_error_response,
    assert_is_true,
    assert_is_uuid,
    assert_status_code,
)
from tools.assertions.errors import APIErrorMessage
from tools.assertions.items import assert_create_item_response
from tools.assertions.schema import validate_json_schema
from tools.routes import APIRoutes


@pytest.mark.items
@pytest.mark.regression
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.CREATE_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestCreateItem:
    @pytest.mark.smoke
    @allure.tag(AllureTag.SMOKE)
    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Positive: Создание объявления с валидными данными")
    @allure.severity(Severity.BLOCKER)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_valid(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        request = CreateItemRequestSchema()

        with allure.step("Создать объявление"):
            response = items_client.create_item_api(request)
            assert_status_code(response.status_code, HTTPStatus.OK)
            data = CreateItemResponseSchema.model_validate_json(response.text)
            cleanup_items.append(data.id)
            assert_is_uuid(data.id)
            validate_json_schema(response.json(), data.model_json_schema(), strict=True)

        with allure.step("Проверить сохранение через GET /item/:id"):
            get_response = items_client.get_item_api(data.id)
            assert_status_code(get_response.status_code, HTTPStatus.OK)
            stored = GetItemResponseSchema.model_validate_json(get_response.text)
            assert_create_item_response(request, stored.root[0])

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Positive: Ответ на создание объявления содержит полный объект объявления")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-6: POST /item возвращает строку вместо полного объекта",
    )
    def test_create_item_response_schema(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        request = CreateItemRequestSchema()
        response = items_client.create_item_api(request)

        assert_status_code(response.status_code, HTTPStatus.OK)
        created = CreateItemResponseSchema.model_validate_json(response.text)
        cleanup_items.append(created.id)
        ItemSchema.model_validate_json(response.text)

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Positive: Создание объявления с нулевой статистикой")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-5: POST /item с нулевыми значениями статистики возвращает 400 вместо 200",
    )
    def test_create_item_zero_statistics(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        request = CreateItemRequestSchema(
            statistics=StatisticsSchema(likes=0, view_count=0, contacts=0),
        )

        with allure.step("Создать объявление"):
            response = items_client.create_item_api(request)
            assert_status_code(response.status_code, HTTPStatus.OK)
            data = CreateItemResponseSchema.model_validate_json(response.text)
            cleanup_items.append(data.id)
            assert_is_uuid(data.id)
            validate_json_schema(response.json(), data.model_json_schema(), strict=True)

        with allure.step("Проверить сохранение через GET /item/:id"):
            get_response = items_client.get_item_api(data.id)
            assert_status_code(get_response.status_code, HTTPStatus.OK)
            stored = GetItemResponseSchema.model_validate_json(get_response.text)
            assert_create_item_response(request, stored.root[0])

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Positive: Неидемпотентность POST - два запроса с одинаковым телом создают разные объявления")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_non_idempotent(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        request = CreateItemRequestSchema()

        response_1 = items_client.create_item_api(request)
        response_2 = items_client.create_item_api(request)

        assert_status_code(response_1.status_code, HTTPStatus.OK)
        assert_status_code(response_2.status_code, HTTPStatus.OK)

        data_1 = CreateItemResponseSchema.model_validate_json(response_1.text)
        data_2 = CreateItemResponseSchema.model_validate_json(response_2.text)
        cleanup_items.extend([data_1.id, data_2.id])
        assert_is_true(data_1.id != data_2.id, "ID объявлений должны быть разными")

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Positive: Создание объявления с минимальной ценой (price = 1)")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_min_price(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        request = CreateItemRequestSchema(price=1)

        with allure.step("Создать объявление"):
            response = items_client.create_item_api(request)
            assert_status_code(response.status_code, HTTPStatus.OK)
            data = CreateItemResponseSchema.model_validate_json(response.text)
            cleanup_items.append(data.id)
            assert_is_uuid(data.id)
            validate_json_schema(response.json(), data.model_json_schema(), strict=True)

        with allure.step("Проверить сохранение через GET /item/:id"):
            get_response = items_client.get_item_api(data.id)
            assert_status_code(get_response.status_code, HTTPStatus.OK)
            stored = GetItemResponseSchema.model_validate_json(get_response.text)
            assert_create_item_response(request, stored.root[0])

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Positive: Создание объявления с sellerID = INT_MAX (2^31-1)")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_large_seller_id(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        payload: dict[str, object] = CreateItemRequestSchema().model_dump(by_alias=True)
        payload["sellerID"] = 2**31 - 1

        with allure.step("Создать объявление"):
            response = items_client.post(APIRoutes.CREATE_ITEM, json=payload)
            assert_status_code(response.status_code, HTTPStatus.OK)
            data = CreateItemResponseSchema.model_validate_json(response.text)
            cleanup_items.append(data.id)
            assert_is_uuid(data.id)

        with allure.step("Проверить сохранение через GET /item/:id"):
            get_response = items_client.get_item_api(data.id)
            assert_status_code(get_response.status_code, HTTPStatus.OK)
            stored = GetItemResponseSchema.model_validate_json(get_response.text)
            assert_equal(stored.root[0].seller_id, 2**31 - 1, "sellerId")

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Positive: Создание объявления с минимальной ненулевой статистикой")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_min_statistics(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        request = CreateItemRequestSchema(
            statistics=StatisticsSchema(likes=1, view_count=1, contacts=1),
        )

        with allure.step("Создать объявление"):
            response = items_client.create_item_api(request)
            assert_status_code(response.status_code, HTTPStatus.OK)
            data = CreateItemResponseSchema.model_validate_json(response.text)
            cleanup_items.append(data.id)
            assert_is_uuid(data.id)
            validate_json_schema(response.json(), data.model_json_schema(), strict=True)

        with allure.step("Проверить сохранение через GET /item/:id"):
            get_response = items_client.get_item_api(data.id)
            assert_status_code(get_response.status_code, HTTPStatus.OK)
            stored = GetItemResponseSchema.model_validate_json(get_response.text)
            assert_create_item_response(request, stored.root[0])


@pytest.mark.items
@pytest.mark.regression
@pytest.mark.negative
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.NEGATIVE, AllureTag.CREATE_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestCreateItemMissingFields:
    """Создание объявления с отсутствующими обязательными полями."""

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.parametrize(
        ("missing_field", "expected_message", "description"),
        [
            pytest.param(
                "sellerID", APIErrorMessage.POST_ITEM_MISSING_SELLER_ID, "без поля sellerID", id="missing_seller_id"
            ),
            pytest.param("name", APIErrorMessage.POST_ITEM_MISSING_NAME, "без поля name", id="missing_name"),
            pytest.param("price", APIErrorMessage.POST_ITEM_MISSING_PRICE, "без поля price", id="missing_price"),
        ],
    )
    def test_create_item_missing_root_field(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
        missing_field: str,
        expected_message: str,
        description: str,
    ) -> None:
        allure.dynamic.title(f"Negative: Создание объявления {description}")
        valid_item_payload.pop(missing_field)
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, expected_message)

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Negative: Создание объявления с пустым телом запроса")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_empty_body(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        response = items_client.post(APIRoutes.CREATE_ITEM, json={})

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, APIErrorMessage.POST_ITEM_MISSING_NAME)

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.parametrize(
        ("missing_stat", "expected_message", "description"),
        [
            pytest.param(
                "likes", APIErrorMessage.POST_ITEM_MISSING_LIKES, "без поля likes в statistics", id="missing_likes"
            ),
            pytest.param(
                "viewCount",
                APIErrorMessage.POST_ITEM_MISSING_VIEW_COUNT,
                "без поля viewCount в statistics",
                id="missing_view_count",
            ),
            pytest.param(
                "contacts",
                APIErrorMessage.POST_ITEM_MISSING_CONTACTS,
                "без поля contacts в statistics",
                id="missing_contacts",
            ),
        ],
    )
    def test_create_item_missing_statistics_field(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
        missing_stat: str,
        expected_message: str,
        description: str,
    ) -> None:
        allure.dynamic.title(f"Negative: Создание объявления {description}")
        valid_item_payload["statistics"].pop(missing_stat)
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, expected_message)

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Negative: Создание объявления с пустым объектом statistics")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_empty_statistics(
        self, items_client: ItemsClient, valid_item_payload: dict[str, Any], cleanup_items: list[str]
    ) -> None:
        valid_item_payload["statistics"] = {}
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, APIErrorMessage.POST_ITEM_MISSING_LIKES)

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Negative: Создание объявления без поля statistics")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_missing_statistics_object(
        self, items_client: ItemsClient, valid_item_payload: dict[str, Any], cleanup_items: list[str]
    ) -> None:
        valid_item_payload.pop("statistics")
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, APIErrorMessage.POST_ITEM_MISSING_LIKES)


@pytest.mark.items
@pytest.mark.regression
@pytest.mark.negative
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.NEGATIVE, AllureTag.CREATE_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestCreateItemInvalidValues:
    """Создание объявления с невалидными значениями (отрицательные, выход за границы)."""

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.parametrize(
        ("price", "description"),
        [
            pytest.param(
                -100,
                "с отрицательной ценой",
                id="negative_price",
                marks=pytest.mark.xfail(
                    strict=True,
                    reason="BUG-1: POST /item принимает отрицательную цену и возвращает 200 вместо 400",
                ),
            ),
            pytest.param(0, "с ценой = 0", id="zero_price"),
            pytest.param(
                2**53 + 1,
                "с ценой 2^53 + 1 (переполнение)",
                id="overflow_price",
                marks=pytest.mark.xfail(
                    strict=True,
                    reason="BUG-1: POST /item принимает цену с переполнением и возвращает 200 вместо 400",
                ),
            ),
        ],
    )
    def test_create_item_invalid_price(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
        price: int,
        description: str,
    ) -> None:
        allure.dynamic.title(f"Negative: Создание объявления {description}")
        valid_item_payload["price"] = price
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, APIErrorMessage.POST_ITEM_MISSING_PRICE)

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.parametrize(
        ("seller_id", "description"),
        [
            pytest.param(0, "с sellerID = 0", id="zero"),
            pytest.param(
                -111111,
                "с отрицательным sellerID",
                id="negative",
                marks=pytest.mark.xfail(
                    strict=True,
                    reason="BUG-16: POST /item принимает отрицательный sellerID и возвращает 200 вместо 400",
                ),
            ),
            pytest.param(
                2**53 + 1,
                "с sellerID = 2^53+1",
                id="overflow",
                marks=pytest.mark.xfail(
                    strict=True,
                    reason="BUG-16: POST /item принимает sellerID 2^53+1 и возвращает 200 вместо 400",
                ),
            ),
        ],
    )
    def test_create_item_invalid_seller_id(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
        seller_id: int,
        description: str,
    ) -> None:
        allure.dynamic.title(f"Negative: Создание объявления {description}")
        valid_item_payload["sellerID"] = seller_id
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, APIErrorMessage.POST_ITEM_MISSING_SELLER_ID)

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-2: POST /item принимает отрицательные значения статистики",
    )
    @pytest.mark.parametrize(
        ("field", "value", "description"),
        [
            pytest.param("likes", -1, "с отрицательным количеством лайков", id="negative_likes"),
            pytest.param("viewCount", -1, "с отрицательным количеством просмотров", id="negative_view_count"),
            pytest.param("contacts", -1, "с отрицательным количеством контактов", id="negative_contacts"),
        ],
    )
    def test_create_item_negative_statistics(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
        field: str,
        value: int,
        description: str,
    ) -> None:
        allure.dynamic.title(f"Negative: Создание объявления {description}")
        valid_item_payload["statistics"][field] = value
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.parametrize(
        ("name", "expected_message", "description"),
        [
            pytest.param("", APIErrorMessage.POST_ITEM_MISSING_NAME, "с пустым именем", id="empty_name"),
            pytest.param(
                "   ",
                APIErrorMessage.POST_ITEM_MISSING_NAME,
                "с именем из пробелов",
                id="whitespace_name",
                marks=pytest.mark.xfail(
                    strict=True,
                    reason="BUG-13: POST /item принимает имя из пробелов и возвращает 200 вместо 400",
                ),
            ),
            pytest.param(
                "a" * 10000,
                "",
                "с именем из 10000 символов",
                id="too_long_name",
                marks=pytest.mark.xfail(
                    strict=True,
                    reason="BUG-19: POST /item принимает слишком длинное имя и возвращает 200 вместо 400",
                ),
            ),
        ],
    )
    def test_create_item_invalid_name(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
        name: str,
        expected_message: str,
        description: str,
    ) -> None:
        allure.dynamic.title(f"Negative: Создание объявления {description}")
        valid_item_payload["name"] = name
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, expected_message)

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Negative: Создание объявления со статистикой 2^53+1")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-14: POST /item принимает значения статистики (2^53+1) и возвращает 200 вместо 400",
    )
    def test_create_item_overflow_statistics(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
    ) -> None:
        overflow = 2**53 + 1
        valid_item_payload["statistics"] = {"likes": overflow, "viewCount": overflow, "contacts": overflow}
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)


@pytest.mark.items
@pytest.mark.regression
@pytest.mark.negative
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.NEGATIVE, AllureTag.CREATE_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestCreateItemWrongTypes:
    """Создание объявления с полями неверного типа."""

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.parametrize(
        ("field", "value", "description"),
        [
            pytest.param("sellerID", "not_a_number", "sellerID строкой", id="seller_id_string"),
            pytest.param("sellerID", 111111.5, "sellerID дробным числом", id="seller_id_float"),
            pytest.param("name", 12345, "name числом", id="name_int"),
            pytest.param("price", "not_a_number", "price строкой", id="price_string"),
            pytest.param("price", 99.99, "price дробным числом", id="price_float"),
            pytest.param("statistics", "not_an_object", "statistics строкой", id="statistics_string"),
            pytest.param("sellerID", None, "sellerID как null", id="seller_id_null"),
            pytest.param("name", None, "name как null", id="name_null"),
            pytest.param("price", None, "price как null", id="price_null"),
            pytest.param("statistics", None, "statistics как null", id="statistics_null"),
            pytest.param("statistics", [], "statistics как массив", id="statistics_array"),
        ],
    )
    def test_create_item_wrong_root_type(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
        field: str,
        value: object,
        description: str,
    ) -> None:
        allure.dynamic.title(f"Negative: Создание объявления с {description}")
        valid_item_payload[field] = value
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.parametrize(
        ("field", "value", "description"),
        [
            pytest.param("likes", "abc", "likes строкой в statistics", id="likes_string"),
            pytest.param("viewCount", "abc", "viewCount строкой в statistics", id="view_count_string"),
            pytest.param("contacts", "abc", "contacts строкой в statistics", id="contacts_string"),
            pytest.param("likes", 1.5, "likes дробным числом в statistics", id="likes_float"),
            pytest.param("viewCount", 1.5, "viewCount дробным числом в statistics", id="view_count_float"),
            pytest.param("contacts", 1.5, "contacts дробным числом в statistics", id="contacts_float"),
        ],
    )
    def test_create_item_wrong_statistics_type(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
        field: str,
        value: object,
        description: str,
    ) -> None:
        allure.dynamic.title(f"Negative: Создание объявления с {description}")
        valid_item_payload["statistics"][field] = value
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.parametrize(
        ("field", "expected_message", "description"),
        [
            pytest.param(
                "likes", APIErrorMessage.POST_ITEM_MISSING_LIKES, "likes как null в statistics", id="likes_null"
            ),
            pytest.param(
                "viewCount",
                APIErrorMessage.POST_ITEM_MISSING_VIEW_COUNT,
                "viewCount как null в statistics",
                id="view_count_null",
            ),
            pytest.param(
                "contacts",
                APIErrorMessage.POST_ITEM_MISSING_CONTACTS,
                "contacts как null в statistics",
                id="contacts_null",
            ),
        ],
    )
    def test_create_item_null_statistics_field(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
        field: str,
        expected_message: str,
        description: str,
    ) -> None:
        allure.dynamic.title(f"Negative: Создание объявления с {description}")
        valid_item_payload["statistics"][field] = None
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, expected_message)

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Negative: Создание объявления с телом запроса в виде массива")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_body_as_array(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        response = items_client.post(APIRoutes.CREATE_ITEM, json=[])

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)


@pytest.mark.items
@pytest.mark.regression
@pytest.mark.security
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.CREATE_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestCreateItemSecurity:
    """Проверка устойчивости к инъекционным атакам в строковых полях."""

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    @pytest.mark.parametrize(
        ("name", "description"),
        [
            pytest.param("'; DROP TABLE items; --", "с SQL-инъекцией в name", id="sql_injection"),
            pytest.param("<script>alert(1)</script>", "с XSS в name", id="xss"),
        ],
    )
    def test_create_item_injection_in_name(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
        name: str,
        description: str,
    ) -> None:
        allure.dynamic.title(f"Security: Создание объявления {description}")
        valid_item_payload["name"] = name

        with allure.step("Создать объявление"):
            response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)
            assert_status_code(response.status_code, HTTPStatus.OK)
            data = CreateItemResponseSchema.model_validate_json(response.text)
            cleanup_items.append(data.id)

        with allure.step("Проверить сохранение через GET /item/:id"):
            get_response = items_client.get_item_api(data.id)
            assert_status_code(get_response.status_code, HTTPStatus.OK)
            stored = GetItemResponseSchema.model_validate_json(get_response.text)
            assert_equal(stored.root[0].name, name, "name хранится без изменений")

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Security: Создание объявления с составным эмодзи в name")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_unicode_emoji(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
    ) -> None:
        valid_item_payload["name"] = "\U0001f1f7\U0001f1fa"
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        assert_status_code(response.status_code, HTTPStatus.OK)
        data = CreateItemResponseSchema.model_validate_json(response.text)
        cleanup_items.append(data.id)
        assert_is_uuid(data.id)
        validate_json_schema(response.json(), data.model_json_schema(), strict=True)

    @pytest.mark.negative
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-17: POST /item с null-байтом в name возвращает 500 вместо 400",
    )
    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Security: Создание объявления с null-байтом в name возвращает 400")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_null_byte_in_name(
        self,
        items_client: ItemsClient,
        valid_item_payload: dict[str, Any],
        cleanup_items: list[str],
    ) -> None:
        valid_item_payload["name"] = "test\x00test"
        response = items_client.post(APIRoutes.CREATE_ITEM, json=valid_item_payload)

        try_cleanup_on_unexpected_success(response, cleanup_items)
        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)


@pytest.mark.items
@pytest.mark.regression
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.CREATE_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestCreateItemExtraFields:
    """Проверка поведения API при наличии неизвестных полей в теле запроса."""

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Contract: Создание объявления с лишним полем в корне тела - API игнорирует")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_extra_root_field(
        self,
        items_client: ItemsClient,
        cleanup_items: list[str],
    ) -> None:
        request = CreateItemRequestSchema()
        payload = request.model_dump(by_alias=True)
        payload["unknownField"] = "value"

        with allure.step("Создать объявление"):
            response = items_client.post(APIRoutes.CREATE_ITEM, json=payload)
            assert_status_code(response.status_code, HTTPStatus.OK)
            data = CreateItemResponseSchema.model_validate_json(response.text)
            cleanup_items.append(data.id)

        with allure.step("Проверить сохранение через GET /item/:id"):
            get_response = items_client.get_item_api(data.id)
            assert_status_code(get_response.status_code, HTTPStatus.OK)
            items = GetItemResponseSchema.model_validate_json(get_response.text)
            assert_create_item_response(request, items.root[0])

    @allure.story(AllureStory.CREATE_ITEM)
    @allure.title("Contract: Создание объявления с лишним полем в statistics - API игнорирует")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.CREATE_ITEM)
    def test_create_item_extra_statistics_field(
        self,
        items_client: ItemsClient,
        cleanup_items: list[str],
    ) -> None:
        request = CreateItemRequestSchema()
        payload = request.model_dump(by_alias=True)
        payload["statistics"]["unknownField"] = "value"

        with allure.step("Создать объявление"):
            response = items_client.post(APIRoutes.CREATE_ITEM, json=payload)
            assert_status_code(response.status_code, HTTPStatus.OK)
            data = CreateItemResponseSchema.model_validate_json(response.text)
            cleanup_items.append(data.id)

        with allure.step("Проверить сохранение через GET /item/:id"):
            get_response = items_client.get_item_api(data.id)
            assert_status_code(get_response.status_code, HTTPStatus.OK)
            items = GetItemResponseSchema.model_validate_json(get_response.text)
            assert_create_item_response(request, items.root[0])
