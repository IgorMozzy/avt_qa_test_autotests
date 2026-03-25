from enum import StrEnum


class APIRoutes(StrEnum):
    CREATE_ITEM = "/api/1/item"
    GET_ITEM = "/api/1/item/{item_id}"
    GET_SELLER_ITEMS = "/api/1/{seller_id}/item"
    GET_STATISTIC_V1 = "/api/1/statistic/{item_id}"
    GET_STATISTIC_V2 = "/api/2/statistic/{item_id}"
    DELETE_ITEM = "/api/2/item/{item_id}"
