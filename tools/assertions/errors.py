from enum import StrEnum


class APIErrorMessage(StrEnum):
    GET_ITEM_NOT_FOUND = "item {id} not found"
    GET_ITEM_INVALID_ID = "ID айтема не UUID: {id}"

    DELETE_ITEM_INVALID_ID = "переданный id айтема некорректный"
    DELETE_ITEM_NOT_FOUND = "item {id} not found"

    GET_STATISTIC_NOT_FOUND = "statistic {id} not found"
    GET_STATISTIC_INVALID_ID = "передан некорректный идентификатор объявления"

    GET_SELLER_ITEMS_INVALID_SELLER_ID = "передан некорректный идентификатор продавца"

    POST_ITEM_MISSING_SELLER_ID = "поле sellerID обязательно"
    POST_ITEM_MISSING_NAME = "поле name обязательно"
    POST_ITEM_MISSING_PRICE = "поле price обязательно"
    POST_ITEM_MISSING_LIKES = "поле likes обязательно"
    POST_ITEM_MISSING_VIEW_COUNT = "поле viewCount обязательно"
    POST_ITEM_MISSING_CONTACTS = "поле contacts обязательно"
