# Автотесты API микросервиса объявлений

🐞 [Задание 1](https://github.com/IgorMozzy/avt_qa_test_autotests/blob/main/_TASK_1/_TASK_1.md) |
📊 [Allure отчет](https://igormozzy.github.io/avt_qa_test_autotests) | 
📝 [Тест-кейсы](https://github.com/IgorMozzy/avt_qa_test_autotests/blob/main/TESTCASES.md) | 
💔 [Баг-репорты](https://github.com/IgorMozzy/avt_qa_test_autotests/blob/main/BUGS.md)





Автотесты для REST API микросервиса объявлений. Проект разработан в рамках отборочного стажерского задания QA (весна 2026).

## Стек

- Python 3.14
- pytest
- httpx
- pydantic
- allure-pytest
- faker
- jsonschema
- ruff (линтер/форматтер)
- ty (проверка типов)

## Установка

## Клонирование репозитория

```bash
git clone git@github.com:IgorMozzy/avt_qa_test_autotests.git
cd avt_qa_test_autotests
```


### 1. Установить uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Или через pip:

```bash
pip install uv
```

### 2. Установить зависимости

```bash
uv sync
```

### 3. Настроить окружение

При старте подхватываются оба файла (если есть): сначала `.env.example`, затем `.env` - локальные значения перекрывают пример. Для своих настроек можно скопировать пример:

```bash
cp .env.example .env
```

Содержимое `.env.example` / `.env`:

```
HTTP_CLIENT.URL="https://qa-internship.avito.com"
HTTP_CLIENT.TIMEOUT=30.0
HTTP_CLIENT.RESPONSE_TIME_SLA=2.0
```

## Запуск тестов

### Все тесты

```bash
uv run pytest
```

### По маркерам

```bash
uv run pytest -m items          # тесты объявлений
uv run pytest -m statistics     # тесты статистики
uv run pytest -m e2e            # сквозные тесты
uv run pytest -m negative       # негативные тесты
uv run pytest -m regression     # регрессионные тесты
uv run pytest -m smoke          # smoke-тесты
```

### Конкретный файл

```bash
uv run pytest tests/items/test_create_item.py
```

## Allure-отчеты

Серьезность в `BUGS.md` отражает скорее продуктовую оценку и обычно близка к `@allure.severity` у связанных тестов, но может расходиться (например, при верном HTTP и ошибке только в теле ответа).

### Установка Allure CLI

macOS (Homebrew):

```bash
brew install allure
```

Windows (Scoop):

```bash
scoop install allure
```

Или через npm:

```bash
npm install -g allure-commandline
```

### Запуск тестов с сохранением результатов

```bash
uv run pytest --alluredir=allure-results
```

### Генерация и открытие отчета

```bash
allure serve allure-results
```

Или для генерации статического отчета:

```bash
allure generate allure-results -o allure-reports --clean
allure open allure-reports
```

## Линтер и форматтер

### Проверка линтером

```bash
uv run ruff check .
```

### Автоисправление

```bash
uv run ruff check . --fix
```

### Проверка форматирования

```bash
uv run ruff format --check .
```

### Форматирование

```bash
uv run ruff format .
```

## Проверка типов

```bash
uv run ty check
```

## Спецификация API

Base URL: `https://qa-internship.avito.com`

### POST `/api/1/item` - Создать объявление

**Заголовки:** `Content-Type: application/json`, `Accept: application/json`

**Тело запроса:**

```json
{
  "sellerID": "<integer>",
  "name": "<string>",
  "price": "<integer>",
  "statistics": {
    "likes": "<integer>",
    "viewCount": "<integer>",
    "contacts": "<integer>"
  }
}
```

| Код | Описание | Тело ответа |
|-----|----------|-------------|
| 200 | Успех | `{id, sellerId, name, price, statistics: {likes, viewCount, contacts}, createdAt}` |
| 400 | Невалидный запрос | `{result: {messages: {}, message: ""}, status: ""}` |

---

### GET `/api/1/item/:id` - Получить объявление по ID

**Параметры пути:** `id` (string, обязательный) - идентификатор объявления

| Код | Описание | Тело ответа |
|-----|----------|-------------|
| 200 | Успех | `[{id, sellerId, name, price, statistics: {likes, viewCount, contacts}, createdAt}]` |
| 400 | Невалидный запрос | `{result: {messages: {}, message: ""}, status: ""}` |
| 404 | Не найдено | `{result: "", status: ""}` |
| 500 | Ошибка сервера | `{result: {messages: {}, message: ""}, status: ""}` |

---

### GET `/api/1/:sellerID/item` - Получить все объявления продавца

**Параметры пути:** `sellerID` (integer, обязательный) - идентификатор продавца

| Код | Описание | Тело ответа |
|-----|----------|-------------|
| 200 | Успех | `[{id, sellerId, name, price, statistics: {likes, viewCount, contacts}, createdAt}]` |
| 400 | Невалидный запрос | `{result: {messages: {}, message: ""}, status: ""}` |
| 500 | Ошибка сервера | `{result: {messages: {}, message: ""}, status: ""}` |

---

### GET `/api/1/statistic/:id` - Получить статистику (v1)

**Параметры пути:** `id` (string, обязательный) - идентификатор объявления

| Код | Описание | Тело ответа |
|-----|----------|-------------|
| 200 | Успех | `[{likes, viewCount, contacts}]` |
| 400 | Невалидный запрос | `{result: {messages: {}, message: ""}, status: ""}` |
| 404 | Не найдено | `{result: "", status: ""}` |
| 500 | Ошибка сервера | `{result: {messages: {}, message: ""}, status: ""}` |

---

### DELETE `/api/2/item/:id` - Удалить объявление

**Параметры пути:** `id` (string, обязательный) - идентификатор объявления

| Код | Описание | Тело ответа |
|-----|----------|-------------|
| 200 | Успех | пустое тело |
| 400 | Невалидный запрос | `{result: {messages: {}, message: ""}, status: ""}` |
| 404 | Не найдено | `{result: "", status: ""}` |
| 500 | Ошибка сервера | `{result: {messages: {}, message: ""}, status: ""}` |

---

### GET `/api/2/statistic/:id` - Получить статистику (v2)

**Параметры пути:** `id` (string, обязательный) - идентификатор объявления

| Код | Описание | Тело ответа |
|-----|----------|-------------|
| 200 | Успех | `[{likes, viewCount, contacts}]` |
| 404 | Не найдено | `{result: "", status: ""}` |
| 500 | Ошибка сервера | `{result: {messages: {}, message: ""}, status: ""}` |

---

## Структура проекта

```
.
├── clients/                  # HTTP-клиенты
│   ├── api_client.py         # Базовый API-клиент
│   ├── event_hooks.py        # Хуки логирования и cURL
│   ├── http_builder.py       # Фабрика HTTP-клиента
│   └── items/                # Клиент и схемы объявлений
│       ├── items_client.py
│       └── items_schema.py
├── fixtures/                 # pytest-фикстуры
│   ├── items.py              # Фикстуры объявлений
│   └── allure.py             # Фикстура Allure
├── tests/                    # Тесты
│   └── items/
│       ├── test_create_item.py
│       ├── test_get_item.py
│       ├── test_get_seller_items.py
│       ├── test_get_statistic.py
│       ├── test_delete_item.py
│       ├── test_http.py
│       └── test_e2e.py
├── tools/                    # Утилиты
│   ├── allure/               # Allure-метаданные
│   ├── assertions/           # Кастомные assert-функции
│   ├── http/                 # cURL-генератор
│   ├── fakers.py             # Генерация тестовых данных
│   ├── logger.py             # Логирование
│   └── routes.py             # Маршруты API
├── config.py                 # Конфигурация (pydantic-settings)
├── conftest.py               # Загрузка фикстур
├── pytest.ini                # Настройки pytest
├── pyproject.toml            # Зависимости и настройки ruff
├── TESTCASES.md              # Описание тест-кейсов
├── BUGS.md                   # Найденные дефекты
└── .env.example              # Шаблон переменных окружения
```

## TODO:
### Soft-assertion (`pytest-check`)

Текущие assert-функции прерывают тест на первом падении. Для комплексной валидации схем удобнее накапливать все ошибки и видеть их за один прогон. Можно рассмотреть библиотеку `pytest-check`.
