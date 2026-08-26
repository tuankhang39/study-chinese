from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_database_url(v: str) -> str:
    """Render/Neon/Railway: postgres:// or postgresql:// → SQLAlchemy + psycopg2 + SSL."""
    if not isinstance(v, str):
        return v
    url = v.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        url = "postgresql+psycopg2://" + url[len("postgresql://") :]
    # Managed Postgres (Render) usually requires SSL
    host_local = "localhost" in url or "127.0.0.1" in url or "@db:" in url
    if not host_local and "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://hoctiengtrung:hoctiengtrung@localhost:5433/hoctiengtrung"
    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    daily_ai_message_limit: int = 40
    daily_ai_message_limit_pro: int = 200
    bootstrap_secret: str = ""
    super_admin_email: str = ""
    super_admin_password: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://127.0.0.1:8001/api/auth/google/callback"
    web_app_url: str = "http://localhost:3001"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        return _normalize_database_url(v)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def google_enabled(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)


settings = Settings()


def ai_limit_for_plan(plan: str) -> int | None:
    """None = unlimited."""
    p = (plan or "free").lower()
    if p == "unlimit":
        return None
    if p == "pro":
        return settings.daily_ai_message_limit_pro
    return settings.daily_ai_message_limit
