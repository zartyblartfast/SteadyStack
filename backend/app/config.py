from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # --- Application ---
    app_env: str = "development"
    app_secret_key: str = ""
    app_debug: bool = True

    # --- Database ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "steadystack"
    postgres_user: str = "steadystack"
    postgres_password: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- External APIs ---
    coingecko_api_url: str = "https://api.coingecko.com/api/v3"
    binance_api_url: str = "https://api.binance.com/api/v3"
    mempool_api_url: str = "https://mempool.space/api"
    bitcoin_card_base_url: str = "http://127.0.0.1:8787"

    # --- Cache TTLs (seconds) ---
    cache_ttl_fees: int = 90
    cache_ttl_price: int = 60
    cache_ttl_onchain: int = 300

    # --- Signal fetch ---
    http_timeout: float = 10.0
    max_data_staleness_minutes: int = 30


settings = Settings()
