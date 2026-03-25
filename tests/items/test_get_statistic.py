from http import HTTPStatus

import allure
import pytest
from allure_commons.types import Severity

from clients.errors_schema import ErrorResponseSchema, ObjectErrorResponseSchema
from clients.items.items_client import ItemsClient
from clients.items.items_schema import GetStatisticResponseSchema, StatisticsSchema
from fixtures.items import ItemFixture
from tools.allure.epics import AllureEpic
from tools.allure.features import AllureFeature
from tools.allure.stories import AllureStory
from tools.allure.tags import AllureTag
from tools.assertions.base import (
    assert_equal,
    assert_error_response,
    assert_is_true,
    assert_list_length,
    assert_status_code,
)
from tools.assertions.errors import APIErrorMessage
from tools.assertions.items import assert_statistic
from tools.assertions.schema import validate_json_schema
from tools.fakers import fake


@pytest.mark.statistics
@pytest.mark.regression
@allure.tag(AllureTag.STATISTICS, AllureTag.REGRESSION, AllureTag.GET_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.STATISTICS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.STATISTICS)
class TestGetStatistic:
    @pytest.mark.smoke
    @allure.tag(AllureTag.SMOKE)
    @allure.story(AllureStory.GET_STATISTIC)
    @allure.title("Positive: Получение статистики по объявлению (v1)")
    @allure.severity(Severity.BLOCKER)
    @allure.sub_suite(AllureStory.GET_STATISTIC)
    def test_get_statistic_v1(
        self,
        items_client: ItemsClient,
        function_item_with_cleanup: ItemFixture,
    ) -> None:
        item = function_item_with_cleanup
        response = items_client.get_statistic_v1_api(item.item_id)
        assert_status_code(response.status_code, HTTPStatus.OK)

        stat_list = GetStatisticResponseSchema.model_validate_json(response.text)
        assert_list_length(stat_list.root, 1, "statistic response")
        assert_statistic(stat_list.root[0], item.request.statistics)
        validate_json_schema(response.json(), GetStatisticResponseSchema.model_json_schema(), strict=True)

    @allure.story(AllureStory.GET_STATISTIC)
    @allure.title("Positive: Получение статистики по объявлению (v2)")
    @allure.severity(Severity.BLOCKER)
    @allure.sub_suite(AllureStory.GET_STATISTIC)
    def test_get_statistic_v2(
        self,
        items_client: ItemsClient,
        function_item_with_cleanup: ItemFixture,
    ) -> None:
        item = function_item_with_cleanup
        response = items_client.get_statistic_v2_api(item.item_id)
        assert_status_code(response.status_code, HTTPStatus.OK)

        stat_list = GetStatisticResponseSchema.model_validate_json(response.text)
        assert_list_length(stat_list.root, 1, "statistic response")
        assert_statistic(stat_list.root[0], item.request.statistics)
        validate_json_schema(response.json(), GetStatisticResponseSchema.model_json_schema(), strict=True)

    @allure.story(AllureStory.GET_STATISTIC)
    @allure.title("Positive: GET /statistic/:id возвращает объект, а не массив")
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.GET_STATISTIC)
    @pytest.mark.xfail(
        strict=True,
        reason="BUG-8: GET /statistic/:id возвращает массив вместо единичного объекта",
    )
    def test_get_statistic_returns_object_not_array(
        self,
        items_client: ItemsClient,
        function_item_with_cleanup: ItemFixture,
    ) -> None:
        response = items_client.get_statistic_v1_api(function_item_with_cleanup.item_id)
        assert_status_code(response.status_code, HTTPStatus.OK)
        assert_is_true(
            isinstance(response.json(), dict),
            "Ответ GET /statistic/:id должен быть объектом, а не массивом",
        )
        validate_json_schema(response.json(), StatisticsSchema.model_json_schema(), strict=True)

    @allure.story(AllureStory.GET_STATISTIC)
    @allure.title("Positive: GET статистики не изменяет счетчик просмотров")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.GET_STATISTIC)
    def test_get_statistic_does_not_increment_views(
        self,
        items_client: ItemsClient,
        function_item_with_cleanup: ItemFixture,
    ) -> None:
        item = function_item_with_cleanup
        response_1 = items_client.get_statistic_v1_api(item.item_id)
        assert_status_code(response_1.status_code, HTTPStatus.OK)
        stat_list_1 = GetStatisticResponseSchema.model_validate_json(response_1.text)
        assert_list_length(stat_list_1.root, 1, "statistic response 1")

        response_2 = items_client.get_statistic_v1_api(item.item_id)
        assert_status_code(response_2.status_code, HTTPStatus.OK)
        stat_list_2 = GetStatisticResponseSchema.model_validate_json(response_2.text)
        assert_list_length(stat_list_2.root, 1, "statistic response 2")

        assert_statistic(stat_list_2.root[0], stat_list_1.root[0])
        validate_json_schema(response_2.json(), GetStatisticResponseSchema.model_json_schema(), strict=True)

    @allure.story(AllureStory.GET_STATISTIC)
    @allure.title("Positive: GET /item/:id не изменяет счетчик просмотров")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.GET_STATISTIC)
    def test_view_count_unchanged_after_get_item(
        self,
        items_client: ItemsClient,
        function_item_with_cleanup: ItemFixture,
    ) -> None:
        item = function_item_with_cleanup
        stat_before = GetStatisticResponseSchema.model_validate_json(
            items_client.get_statistic_v1_api(item.item_id).text
        )
        view_count_before = stat_before.root[0].view_count

        items_client.get_item_api(item.item_id)

        stat_after = GetStatisticResponseSchema.model_validate_json(
            items_client.get_statistic_v1_api(item.item_id).text
        )
        assert_equal(stat_after.root[0].view_count, view_count_before, "viewCount не изменился после GET /item/:id")

    @allure.story(AllureStory.GET_STATISTIC)
    @allure.title("Positive: Статистика v1 и v2 возвращают одинаковые данные")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.GET_STATISTIC)
    def test_statistic_v1_equals_v2(
        self,
        items_client: ItemsClient,
        function_item_with_cleanup: ItemFixture,
    ) -> None:
        item = function_item_with_cleanup
        response_v1 = items_client.get_statistic_v1_api(item.item_id)
        response_v2 = items_client.get_statistic_v2_api(item.item_id)

        assert_status_code(response_v1.status_code, HTTPStatus.OK)
        assert_status_code(response_v2.status_code, HTTPStatus.OK)
        assert_equal(response_v1.json(), response_v2.json(), "v1 vs v2 statistic")
        validate_json_schema(response_v1.json(), GetStatisticResponseSchema.model_json_schema(), strict=True)


@pytest.mark.statistics
@pytest.mark.regression
@pytest.mark.negative
@allure.tag(AllureTag.STATISTICS, AllureTag.REGRESSION, AllureTag.NEGATIVE, AllureTag.GET_ENTITY)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.STATISTICS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureFeature.STATISTICS)
class TestGetStatisticNegative:
    @allure.story(AllureStory.GET_STATISTIC)
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.GET_STATISTIC)
    @pytest.mark.parametrize(
        "version",
        [
            pytest.param(
                "v1",
                id="v1",
                marks=[
                    pytest.mark.flaky(reruns=2, reruns_delay=3),
                    pytest.mark.xfail(
                        strict=True,
                        reason="BUG-15: GET /statistic/:id возвращает 200 после удаления объявления вместо 404",
                    ),
                ],
            ),
            pytest.param(
                "v2",
                id="v2",
                marks=[
                    pytest.mark.flaky(reruns=2, reruns_delay=3),
                    pytest.mark.xfail(
                        strict=True,
                        reason="BUG-15: GET /statistic/:id возвращает 200 после удаления объявления вместо 404",
                    ),
                ],
            ),
        ],
    )
    def test_statistic_not_found_after_deletion(
        self, items_client: ItemsClient, function_item: ItemFixture, version: str
    ) -> None:
        allure.dynamic.title(f"Negative: Получение статистики по удалённому объявлению возвращает 404 ({version})")
        get_stat = items_client.get_statistic_v1_api if version == "v1" else items_client.get_statistic_v2_api
        items_client.delete_item_api(function_item.item_id)
        response = get_stat(function_item.item_id)

        assert_status_code(response.status_code, HTTPStatus.NOT_FOUND)

        validate_json_schema(response.json(), ErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(
            response.json(),
            HTTPStatus.NOT_FOUND,
            APIErrorMessage.GET_STATISTIC_NOT_FOUND.format(id=function_item.item_id),
        )

    @allure.story(AllureStory.GET_STATISTIC)
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.GET_STATISTIC)
    @pytest.mark.parametrize("version", [pytest.param("v1", id="v1"), pytest.param("v2", id="v2")])
    def test_statistic_not_found_random_id(self, items_client: ItemsClient, version: str) -> None:
        allure.dynamic.title(
            f"Negative: Получение статистики по случайному несуществующему ID возвращает 404 ({version})"
        )
        get_stat = items_client.get_statistic_v1_api if version == "v1" else items_client.get_statistic_v2_api
        random_id = fake.uuid4()
        response = get_stat(random_id)

        assert_status_code(response.status_code, HTTPStatus.NOT_FOUND)

        validate_json_schema(response.json(), ErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(
            response.json(), HTTPStatus.NOT_FOUND, APIErrorMessage.GET_STATISTIC_NOT_FOUND.format(id=random_id)
        )

    @allure.story(AllureStory.GET_STATISTIC)
    @allure.severity(Severity.NORMAL)
    @allure.sub_suite(AllureStory.GET_STATISTIC)
    @pytest.mark.parametrize(
        "version",
        [
            pytest.param("v1", id="v1"),
            pytest.param(
                "v2",
                id="v2",
                marks=pytest.mark.xfail(
                    strict=True,
                    reason="BUG-12: GET /api/2/statistic/:id возвращает 404 вместо 400 для невалидного ID",
                ),
            ),
        ],
    )
    def test_get_statistic_invalid_id(self, items_client: ItemsClient, version: str) -> None:
        allure.dynamic.title(f"Negative: Получение статистики с невалидным форматом ID ({version})")
        get_stat = items_client.get_statistic_v1_api if version == "v1" else items_client.get_statistic_v2_api
        response = get_stat("invalid-id")

        assert_status_code(response.status_code, HTTPStatus.BAD_REQUEST)

        validate_json_schema(response.json(), ObjectErrorResponseSchema.model_json_schema(), strict=True)
        assert_error_response(response.json(), HTTPStatus.BAD_REQUEST, APIErrorMessage.GET_STATISTIC_INVALID_ID)
