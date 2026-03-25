from enum import StrEnum


class AllureStory(StrEnum):
    CREATE_ITEM = "Создание объявления"
    GET_ITEM = "Получение объявления"
    GET_SELLER_ITEMS = "Получение объявлений продавца"
    GET_STATISTIC = "Получение статистики"
    DELETE_ITEM = "Удаление объявления"
    E2E = "E2E"
    HTTP_CONTRACT = "HTTP-контракт"
