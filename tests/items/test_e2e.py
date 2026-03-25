from http import HTTPStatus

import allure
import pytest
from allure_commons.types import Severity

from clients.items.items_client import ItemsClient
from clients.items.items_schema import (
    CreateItemRequestSchema,
    CreateItemResponseSchema,
    GetItemResponseSchema,
    GetStatisticResponseSchema,
    ItemSchema,
)
from tools.allure.epics import AllureEpic
from tools.allure.features import AllureFeature
from tools.allure.stories import AllureStory
from tools.allure.tags import AllureTag
from tools.assertions.base import assert_is_true, assert_list_length, assert_status_code
from tools.assertions.items import assert_create_item_response, assert_statistic
from tools.fakers import fake


@pytest.mark.e2e
@pytest.mark.regression
@allure.tag(AllureTag.E2E, AllureTag.REGRESSION)
@allure.epic(AllureEpic.ADS_SERVICE)
@allure.feature(AllureFeature.ITEMS)
@allure.parent_suite(AllureEpic.ADS_SERVICE)
@allure.suite(AllureStory.E2E)
class TestE2E:
    @allure.story(AllureStory.E2E)
    @allure.title("Positive: Полный жизненный цикл объявления: создание -> получение -> статистика -> удаление")
    @allure.severity(Severity.BLOCKER)
    @allure.sub_suite(AllureStory.E2E)
    def test_full_item_lifecycle(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        request = CreateItemRequestSchema()
        create_response = items_client.create_item_api(request)
        created = CreateItemResponseSchema.model_validate_json(create_response.text)
        cleanup_items.append(created.id)
        assert_status_code(create_response.status_code, HTTPStatus.OK)

        get_response = items_client.get_item_api(created.id)
        assert_status_code(get_response.status_code, HTTPStatus.OK)
        items = GetItemResponseSchema.model_validate_json(get_response.text)
        assert_list_length(items.root, 1, "get item response")
        assert_create_item_response(request, items.root[0])

        stat_response = items_client.get_statistic_v1_api(created.id)
        assert_status_code(stat_response.status_code, HTTPStatus.OK)
        stat_list = GetStatisticResponseSchema.model_validate_json(stat_response.text)
        assert_list_length(stat_list.root, 1, "statistic response")
        assert_statistic(stat_list.root[0], request.statistics)

        delete_response = items_client.delete_item_api(created.id)
        assert_status_code(delete_response.status_code, HTTPStatus.OK)

        gone_response = items_client.get_item_api(created.id)
        assert_status_code(gone_response.status_code, HTTPStatus.NOT_FOUND)

    @allure.story(AllureStory.E2E)
    @allure.title("Positive: Кросс-версия: создание v1, статистика v2, удаление v2")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.E2E)
    def test_cross_version(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        request = CreateItemRequestSchema()
        create_response = items_client.create_item_api(request)
        created = CreateItemResponseSchema.model_validate_json(create_response.text)
        cleanup_items.append(created.id)
        assert_status_code(create_response.status_code, HTTPStatus.OK)

        get_response = items_client.get_item_api(created.id)
        assert_status_code(get_response.status_code, HTTPStatus.OK)
        items = GetItemResponseSchema.model_validate_json(get_response.text)
        assert_list_length(items.root, 1, "get item response")
        assert_create_item_response(request, items.root[0])

        stat_response = items_client.get_statistic_v2_api(created.id)
        assert_status_code(stat_response.status_code, HTTPStatus.OK)
        stat_list = GetStatisticResponseSchema.model_validate_json(stat_response.text)
        assert_list_length(stat_list.root, 1, "statistic response")
        assert_statistic(stat_list.root[0], request.statistics)

        delete_response = items_client.delete_item_api(created.id)
        assert_status_code(delete_response.status_code, HTTPStatus.OK)

    @allure.story(AllureStory.E2E)
    @allure.title("Positive: Создание нескольких объявлений продавца -> получение списка -> удаление всех")
    @allure.severity(Severity.CRITICAL)
    @allure.sub_suite(AllureStory.E2E)
    def test_seller_items_lifecycle(self, items_client: ItemsClient, cleanup_items: list[str]) -> None:
        seller_id = fake.seller_id()
        created_ids: list[str] = []

        for _ in range(3):
            request = CreateItemRequestSchema(seller_id=seller_id)
            created_id = items_client.create_item(request)
            created_ids.append(created_id)
            cleanup_items.append(created_id)

        response = items_client.get_seller_items_api(seller_id)
        assert_status_code(response.status_code, HTTPStatus.OK)
        items = [ItemSchema.model_validate(item) for item in response.json()]
        found_ids = {item.id for item in items}
        assert_is_true(set(created_ids).issubset(found_ids), "Все созданные объявления должны быть в списке")

        for item_id in created_ids:
            delete_response = items_client.delete_item_api(item_id)
            assert_status_code(delete_response.status_code, HTTPStatus.OK)

        cleanup_items.clear()

        after_delete_response = items_client.get_seller_items_api(seller_id)
        assert_status_code(after_delete_response.status_code, HTTPStatus.OK)
        remaining_ids = {ItemSchema.model_validate(item).id for item in after_delete_response.json()}
        assert_is_true(
            set(created_ids).isdisjoint(remaining_ids),
            "Удалённые объявления не должны присутствовать в списке продавца",
        )
