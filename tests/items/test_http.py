from http import HTTPStatus

import allure
import pytest
from allure_commons.types import Severity

from clients.errors_schema import ObjectErrorResponseSchema
from clients.items.items_client import ItemsClient
from clients.items.items_schema import CreateItemRequestSchema
from config import settings
from fixtures.items import ItemFixture, try_cleanup_on_unexpected_success
from tools.allure.epics import AllureEpic
from tools.allure.features import AllureFeature
from tools.allure.stories import AllureStory
from tools.allure.tags import AllureTag
from tools.assertions.base import assert_content_type, assert_error_response, assert_response_time, assert_status_code
from tools.assertions.schema import validate_json_schema
from tools.fakers import fake
from tools.routes import APIRoutes


@pytest.mark.items
@pytest.mark.regression
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestResponseContract:
    """Проверка нефункциональных характеристик HTTP-ответов."""

    @allure.story(AllureStory.HTTP_CONTRACT)
    @allure.title("Positive: SLA и Content-Type для успешных ответов всех эндпоинтов")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.HTTP_CONTRACT)
    @pytest.mark.flaky(reruns=3, reruns_delay=2)
    def test_successful_response_contract(
        self,
        items_client: ItemsClient,
        function_item_with_cleanup: ItemFixture,
        cleanup_items: list[str],
    ) -> None:
        item_id = function_item_with_cleanup.item_id
        seller_id = function_item_with_cleanup.seller_id

        requests = [
            ("POST", APIRoutes.CREATE_ITEM, CreateItemRequestSchema().model_dump(by_alias=True)),
            ("GET", APIRoutes.GET_ITEM.format(item_id=item_id), None),
            ("GET", APIRoutes.GET_SELLER_ITEMS.format(seller_id=seller_id), None),
            ("GET", APIRoutes.GET_STATISTIC_V1.format(item_id=item_id), None),
            ("GET", APIRoutes.GET_STATISTIC_V2.format(item_id=item_id), None),
            ("DELETE", APIRoutes.DELETE_ITEM.format(item_id=item_id), None),
        ]

        for method, url, json_payload in requests:
            with allure.step(f"Проверка контракта для {method} {url}"):
                response = items_client.request(method, url, json=json_payload)

                if method == "POST":
                    try_cleanup_on_unexpected_success(response, cleanup_items)

                assert_response_time(response.elapsed, settings.http_client.response_time_sla)

                if method != "DELETE":
                    assert_content_type(response.headers.get("content-type"), "application/json")


@pytest.mark.items
@pytest.mark.regression
@pytest.mark.negative
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.NEGATIVE)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestMethodNotAllowed:
    """Проверка, что неподдерживаемые HTTP-методы отклоняются."""

    @allure.story(AllureStory.HTTP_CONTRACT)
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.HTTP_CONTRACT)
    @pytest.mark.parametrize(
        ("method", "url", "description"),
        [
            pytest.param("PUT", APIRoutes.CREATE_ITEM, "PUT /api/1/item", id="put_create"),
            pytest.param("PATCH", APIRoutes.CREATE_ITEM, "PATCH /api/1/item", id="patch_create"),
            pytest.param("PUT", APIRoutes.GET_ITEM.format(item_id="test-id"), "PUT /api/1/item/:id", id="put_get_item"),
            pytest.param(
                "PATCH", APIRoutes.GET_ITEM.format(item_id="test-id"), "PATCH /api/1/item/:id", id="patch_get_item"
            ),
            pytest.param(
                "PUT", APIRoutes.GET_SELLER_ITEMS.format(seller_id=111111), "PUT /api/1/:sellerID/item", id="put_seller"
            ),
            pytest.param(
                "PATCH",
                APIRoutes.GET_SELLER_ITEMS.format(seller_id=111111),
                "PATCH /api/1/:sellerID/item",
                id="patch_seller",
            ),
            pytest.param(
                "PUT",
                APIRoutes.GET_STATISTIC_V1.format(item_id="test-id"),
                "PUT /api/1/statistic/:id",
                id="put_stat_v1",
            ),
            pytest.param(
                "PATCH",
                APIRoutes.GET_STATISTIC_V1.format(item_id="test-id"),
                "PATCH /api/1/statistic/:id",
                id="patch_stat_v1",
            ),
            pytest.param(
                "PUT", APIRoutes.DELETE_ITEM.format(item_id="test-id"), "PUT /api/2/item/:id", id="put_delete"
            ),
            pytest.param(
                "PATCH", APIRoutes.DELETE_ITEM.format(item_id="test-id"), "PATCH /api/2/item/:id", id="patch_delete"
            ),
            pytest.param(
                "PUT",
                APIRoutes.GET_STATISTIC_V2.format(item_id="test-id"),
                "PUT /api/2/statistic/:id",
                id="put_stat_v2",
            ),
            pytest.param(
                "PATCH",
                APIRoutes.GET_STATISTIC_V2.format(item_id="test-id"),
                "PATCH /api/2/statistic/:id",
                id="patch_stat_v2",
            ),
        ],
    )
    def test_method_not_allowed(
        self,
        items_client: ItemsClient,
        method: str,
        url: str,
        description: str,
    ) -> None:
        allure.dynamic.title(f"Negative: {description} возвращает 405")
        response = items_client.request(method, url)

        assert_status_code(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)


@pytest.mark.items
@pytest.mark.regression
@pytest.mark.negative
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.NEGATIVE, AllureTag.CREATE_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestUnsupportedContentType:
    """Проверка отклонения запросов с неподдерживаемым Content-Type."""

    @allure.story(AllureStory.HTTP_CONTRACT)
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.HTTP_CONTRACT)
    @pytest.mark.parametrize(
        "content_type",
        [
            pytest.param(
                "text/xml",
                id="xml",
                marks=pytest.mark.xfail(
                    strict=True,
                    reason="BUG-21: POST /api/1/item с некорректным Content-Type возвращает нестандартную схему ошибки",
                ),
            ),
            pytest.param(
                "text/plain",
                id="plain",
                marks=pytest.mark.xfail(
                    strict=True,
                    reason="BUG-21: POST /api/1/item с некорректным Content-Type возвращает нестандартную схему ошибки",
                ),
            ),
        ],
    )
    def test_unsupported_content_type(
        self,
        items_client: ItemsClient,
        content_type: str,
    ) -> None:
        allure.dynamic.title(f"Negative: POST /api/1/item с Content-Type {content_type}")
        payload = CreateItemRequestSchema().model_dump_json(by_alias=True)
        response = items_client.request(
            "POST",
            APIRoutes.CREATE_ITEM,
            content=payload,
            headers={"Content-Type": content_type},
        )

        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)
        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)


@pytest.mark.items
@pytest.mark.regression
@pytest.mark.negative
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.NEGATIVE)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestErrorResponseSchema:
    """Проверка, что ошибочные ответы соответствуют ожидаемой JSON-схеме."""

    @allure.story(AllureStory.HTTP_CONTRACT)
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.HTTP_CONTRACT)
    @pytest.mark.parametrize(
        ("method", "url", "expected_status"),
        [
            pytest.param(
                "GET", APIRoutes.GET_ITEM.format(item_id="invalid-id"), HTTPStatus.BAD_REQUEST, id="get_item_400"
            ),
            pytest.param(
                "GET", APIRoutes.GET_ITEM.format(item_id=fake.uuid4()), HTTPStatus.NOT_FOUND, id="get_item_404"
            ),
            pytest.param(
                "DELETE", APIRoutes.DELETE_ITEM.format(item_id="invalid-id"), HTTPStatus.BAD_REQUEST, id="delete_400"
            ),
            pytest.param(
                "DELETE", APIRoutes.DELETE_ITEM.format(item_id=fake.uuid4()), HTTPStatus.NOT_FOUND, id="delete_404"
            ),
            pytest.param(
                "GET", APIRoutes.GET_STATISTIC_V1.format(item_id="invalid-id"), HTTPStatus.BAD_REQUEST, id="stat_v1_400"
            ),
            pytest.param(
                "GET", APIRoutes.GET_STATISTIC_V1.format(item_id=fake.uuid4()), HTTPStatus.NOT_FOUND, id="stat_v1_404"
            ),
            pytest.param(
                "GET",
                APIRoutes.GET_STATISTIC_V2.format(item_id="invalid-id"),
                HTTPStatus.BAD_REQUEST,
                id="stat_v2_400",
                marks=pytest.mark.xfail(
                    strict=True,
                    reason="BUG-12: GET /api/2/statistic/:id возвращает 404 вместо 400 для невалидного ID",
                ),
            ),
            pytest.param(
                "GET", APIRoutes.GET_STATISTIC_V2.format(item_id=fake.uuid4()), HTTPStatus.NOT_FOUND, id="stat_v2_404"
            ),
            pytest.param(
                "GET",
                APIRoutes.GET_SELLER_ITEMS.format(seller_id="not_a_number"),
                HTTPStatus.BAD_REQUEST,
                id="seller_400",
            ),
        ],
    )
    def test_error_response_schema(
        self,
        items_client: ItemsClient,
        method: str,
        url: str,
        expected_status: int,
    ) -> None:
        allure.dynamic.title(f"Контракт: схема ошибки {method} {url}")
        response = items_client.request(method, url)
        assert_status_code(response.status_code, expected_status)
        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)


@pytest.mark.items
@pytest.mark.regression
@pytest.mark.negative
@allure.tag(AllureTag.ITEMS, AllureTag.REGRESSION, AllureTag.NEGATIVE, AllureTag.CREATE_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.ITEMS)
class TestMalformedBody:
    """Проверка отклонения запросов с некорректным телом."""

    @allure.story(AllureStory.HTTP_CONTRACT)
    @allure.title("Negative: POST /api/1/item с пустым телом")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.HTTP_CONTRACT)
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-23: POST /item с пустым телом возвращает status='не передан объект - объявление' вместо '400'",
    )
    def test_empty_body(self, items_client: ItemsClient) -> None:
        response = items_client.request(
            "POST",
            APIRoutes.CREATE_ITEM,
            content=b"",
            headers={"Content-Type": "application/json"},
        )

        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)
        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, "")

    @allure.story(AllureStory.HTTP_CONTRACT)
    @allure.title("Negative: POST /api/1/item с невалидным JSON")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.HTTP_CONTRACT)
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-23: POST /item с невалидным JSON возвращает status='не передан объект - объявление' вместо '400'",
    )
    def test_broken_json(self, items_client: ItemsClient) -> None:
        response = items_client.request(
            "POST",
            APIRoutes.CREATE_ITEM,
            content=b'{"invalid json',
            headers={"Content-Type": "application/json"},
        )

        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)
        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, "")
