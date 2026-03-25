from pydantic import BaseModel, ConfigDict, Field, RootModel

from tools.fakers import fake


class StatisticsSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    likes: int = Field(default_factory=fake.likes, ge=0)
    view_count: int = Field(alias="viewCount", default_factory=fake.view_count, ge=0)
    contacts: int = Field(default_factory=fake.contacts, ge=0)


class CreateItemRequestSchema(BaseModel):
    """Схема запроса на создание объявления. Поле sellerID с заглавной ID - особенность API."""

    model_config = ConfigDict(populate_by_name=True)

    seller_id: int = Field(alias="sellerID", default_factory=fake.seller_id, ge=111111, le=999999)
    name: str = Field(default_factory=fake.item_name, min_length=1)
    price: int = Field(default_factory=fake.price, ge=1)
    statistics: StatisticsSchema = Field(default_factory=StatisticsSchema)


class ItemSchema(BaseModel):
    """Схема объявления в ответах API."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    seller_id: int = Field(alias="sellerId")
    name: str
    price: int
    statistics: StatisticsSchema
    created_at: str = Field(alias="createdAt")


class GetItemResponseSchema(RootModel):
    """Схема ответа GET /api/1/item/:id. API возвращает массив с одним объектом."""

    root: list[ItemSchema]


class GetStatisticResponseSchema(RootModel):
    """Схема ответа GET /api/{1,2}/statistic/:id. API возвращает массив с одним объектом."""

    root: list[StatisticsSchema]


class CreateItemResponseSchema(BaseModel):
    # TODO: баг - API возвращает только {"status": "Сохранили объявление - <uuid>"}.
    # После исправления бага заменить этот класс на ItemSchema - ответ должен соответствовать:
    # {"id": str, "sellerId": int, "name": str, "price": int, "statistics": {...}, "createdAt": str}
    status: str

    @property
    def id(self) -> str:
        parts = self.status.rsplit(" - ", maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"Неожиданный формат статуса создания объявления: {self.status!r}")
        return parts[1]
