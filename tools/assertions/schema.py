import copy
from typing import Any

import allure
from jsonschema import validate
from jsonschema.validators import Draft202012Validator

from tools.logger import get_logger

logger = get_logger("SCHEMA_ASSERTIONS")


def _enforce_no_additional_properties(schema: dict[str, Any]) -> dict[str, Any]:
    """Возвращает копию schema с additionalProperties: false на всех object-схемах."""
    schema = copy.deepcopy(schema)
    if schema.get("type") == "object" and "properties" in schema:
        schema["additionalProperties"] = False
    for definition in schema.get("$defs", {}).values():
        if definition.get("type") == "object" and "properties" in definition:
            definition["additionalProperties"] = False
    return schema


@allure.step("Валидировать JSON-схему")
def validate_json_schema(instance: Any, schema: dict[str, Any], *, strict: bool = False) -> None:
    """Проверяет, соответствует ли JSON-объект заданной JSON-схеме."""
    logger.info("Валидация JSON-схемы")
    if strict:
        schema = _enforce_no_additional_properties(schema)
    validate(
        schema=schema,
        instance=instance,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
