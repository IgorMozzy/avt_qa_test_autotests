from pydantic import BaseModel


class ErrorResultSchema(BaseModel):
    message: str = ""
    messages: dict[str, str] | None = None


class ErrorResponseSchema(BaseModel):
    result: ErrorResultSchema | str
    status: str


class ObjectErrorResponseSchema(BaseModel):
    """Схема ошибки 400/500 - result как объект ErrorResultSchema"""

    result: ErrorResultSchema
    status: str
