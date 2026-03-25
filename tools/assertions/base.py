import uuid as _uuid
from datetime import timedelta
from typing import Any

import allure

from clients.errors_schema import ErrorResponseSchema, ErrorResultSchema
from tools.logger import get_logger

logger = get_logger("BASE_ASSERTIONS")


@allure.step("Проверить, что статус-код ответа равен {expected}")
def assert_status_code(actual: int, expected: int) -> None:
    """Проверяет, что статус-код ответа соответствует ожидаемому."""
    logger.info("Проверить, что статус-код ответа равен %s", expected)
    assert actual == expected, f"Некорректный статус-код ответа. Ожидался: {expected}. Получен: {actual}"


@allure.step("Проверить, что {name} равно {expected}")
def assert_equal(actual: Any, expected: Any, name: str) -> None:
    """Проверяет, что фактическое значение равно ожидаемому."""
    logger.info("Проверить, что '%s' равно %s", name, expected)
    assert actual == expected, f'Некорректное значение: "{name}". Ожидалось: {expected}. Получено: {actual}'


@allure.step("Проверить, что {name} истинно")
def assert_is_true(actual: Any, name: str) -> None:
    """Проверяет, что значение является истинным."""
    logger.info("Проверить, что '%s' истинно", name)
    assert actual, f"Ожидалось истинное значение, но получено: {actual}"


@allure.step("Проверить, что {name} является валидным UUID")
def assert_is_uuid(value: str, name: str = "id") -> None:
    """Проверяет, что строка является валидным UUID."""
    logger.info("Проверить, что '%s' является валидным UUID", name)
    try:
        _uuid.UUID(value)
    except ValueError:
        raise AssertionError(f'Ожидался валидный UUID для "{name}", получено: {value!r}') from None


@allure.step("Проверить, что время ответа меньше {max_seconds} сек")
def assert_response_time(elapsed: timedelta, max_seconds: float) -> None:
    """Проверяет, что время ответа не превышает допустимый порог."""
    actual = elapsed.total_seconds()
    logger.info("Проверить, что время ответа (%.3f сек) меньше %s сек", actual, max_seconds)
    assert actual < max_seconds, (
        f"Время ответа превышает порог. Максимум: {max_seconds} сек. Фактически: {actual:.3f} сек"
    )


@allure.step("Проверить, что Content-Type равен {expected}")
def assert_content_type(actual: str | None, expected: str) -> None:
    """Проверяет, что заголовок Content-Type соответствует ожидаемому."""
    logger.info("Проверить, что Content-Type равен %s", expected)
    assert actual is not None, "Заголовок Content-Type отсутствует в ответе"
    mime_type = actual.split(";")[0].strip()
    assert mime_type == expected, f"Некорректный Content-Type. Ожидался: {expected}. Получен: {actual}"


@allure.step("Проверить тело ошибки: message={expected_message}")
def assert_error_response(body: dict[str, Any], expected_status: int, expected_message: str) -> None:
    """Проверяет структуру и содержимое ошибочного ответа API."""
    logger.info("Проверить тело ошибки: status=%s, message=%s", expected_status, expected_message)
    error = ErrorResponseSchema.model_validate(body)
    assert error.status == str(expected_status), (
        f'Некорректный status в теле ошибки. Ожидался: "{expected_status}". Получен: "{error.status}"'
    )
    assert isinstance(error.result, ErrorResultSchema), (
        f"Поле result должно быть объектом, получено: {type(error.result).__name__}"
    )
    assert error.result.message == expected_message, (
        f'Некорректный message в теле ошибки. Ожидался: "{expected_message}". Получен: "{error.result.message}"'
    )


@allure.step("Проверить, что длина списка {name} равна {expected}")
def assert_list_length(data: list[Any], expected: int, name: str) -> None:
    """Проверяет, что список содержит ровно expected элементов."""
    logger.info("Проверить, что длина списка '%s' равна %s", name, expected)
    assert isinstance(data, list), f'Ожидался список для "{name}", получен: {type(data).__name__}'
    assert len(data) == expected, f'Некорректная длина списка "{name}". Ожидалась: {expected}. Получена: {len(data)}'
