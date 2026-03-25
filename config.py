from pathlib import Path
from typing import Self

from pydantic import BaseModel, DirectoryPath, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parent
_ENV_FILES = tuple(str(p) for p in (_ROOT / ".env.example", _ROOT / ".env") if p.is_file()) or None


class HTTPClientConfig(BaseModel):
    url: HttpUrl
    timeout: float
    response_time_sla: float = 2.0

    @property
    def client_url(self) -> str:
        return str(self.url)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="allow",
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        env_nested_delimiter=".",
    )

    http_client: HTTPClientConfig
    allure_results_dir: DirectoryPath = Path("./allure-results")

    @classmethod
    def initialize(cls) -> Self:
        allure_results_dir = Path("./allure-results")
        allure_results_dir.mkdir(exist_ok=True)
        return cls(allure_results_dir=allure_results_dir)  # type: ignore[call-arg]


settings = Settings.initialize()
