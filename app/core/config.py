from functools import lru_cache

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_name: str = "MM Motors API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    jwt_secret_key: str = Field(..., validation_alias="JWT_SECRET_KEY")
    algorithm: str = Field(..., validation_alias="ALGORITHM")
    access_token_expire_minutes: int = Field(..., validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "https://admin-mm-motors.vercel.app",
            "https://mm-motors.vercel.app",
        ],
        validation_alias="CORS_ORIGINS"
    )

    @validator("database_url", "jwt_secret_key", "supabase_url", "supabase_service_role_key", pre=True)
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            import json
            if isinstance(v, str):
                return json.loads(v)
            return v
        return ["*"]
    supabase_url: str = Field(..., validation_alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., validation_alias="SUPABASE_KEY")
    supabase_storage_bucket: str = Field(default="mm-motors", validation_alias="SUPABASE_STORAGE_BUCKET")
    supabase_storage_public_base_url: str = Field(default="", validation_alias="SUPABASE_STORAGE_PUBLIC_BASE_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
