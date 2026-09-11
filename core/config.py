from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime settings.

    Safety-critical limits are intentionally conservative. Runtime code should
    treat these as policy inputs, never as suggestions from an AI agent.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    trading_mode: Literal["research", "paper", "shadow", "tiny_live"] = "research"

    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"
    jupiter_api_base: str = "https://api.jup.ag"
    trading_wallet_public_key: str | None = None

    max_position_fraction: Decimal = Field(default=Decimal("0.10"), gt=0, le=Decimal("1"))
    max_portfolio_drawdown: Decimal = Field(default=Decimal("0.15"), gt=0, le=Decimal("1"))
    max_daily_loss_fraction: Decimal = Field(default=Decimal("0.03"), gt=0, le=Decimal("1"))
    min_cash_reserve_fraction: Decimal = Field(default=Decimal("0.20"), ge=0, lt=Decimal("1"))

    @field_validator("jupiter_api_base", "solana_rpc_url")
    @classmethod
    def require_https(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("network endpoints must use HTTPS")
        return value.rstrip("/")

    @field_validator("min_cash_reserve_fraction")
    @classmethod
    def reserve_must_fit_position_limit(cls, value: Decimal, info):
        max_position = info.data.get("max_position_fraction")
        if max_position is not None and value + max_position > Decimal("1"):
            raise ValueError("cash reserve plus maximum position fraction cannot exceed 100%")
        return value


def load_settings() -> Settings:
    return Settings()
