from enum import StrEnum


class AllureTag(StrEnum):
    ITEMS = "items"
    STATISTICS = "statistics"
    REGRESSION = "regression"
    SMOKE = "smoke"
    NEGATIVE = "negative"
    E2E = "e2e"
    SECURITY = "security"

    CREATE_ENTITY = "create_entity"
    GET_ENTITY = "get_entity"
    DELETE_ENTITY = "delete_entity"
