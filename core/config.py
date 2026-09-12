from decimal import Decimal
from typing import Literal

from pydantic import Field, SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SOL_MINT = "So11111111111111111111111111111111111111112"


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
    jupiter_api_base: str = "https://api.jup.ag/swap/v2"
    jupiter_api_key: SecretStr | None = None
    trading_wallet_public_key: str | None = None

    # USDC is the canonical portfolio accounting unit. SOL remains a supported
    # base asset for routing and trading without making SOL price changes look
    # like portfolio performance.
    base_accounting_mint: str = USDC_MINT
    base_stable_mint: str = USDC_MINT
    sol_mint: str = SOL_MINT

    max_position_fraction: Decimal = Field(default=Decimal("0.10"), gt=0, le=Decimal(1))
    max_portfolio_drawdown: Decimal = Field(default=Decimal("0.15"), gt=0, le=Decimal(1))
    max_daily_loss_fraction: Decimal = Field(default=Decimal("0.03"), gt=0, le=Decimal(1))
    min_cash_reserve_fraction: Decimal = Field(default=Decimal("0.20"), ge=0, lt=Decimal(1))

    @field_validator("jupiter_api_base", "solana_rpc_url")
    @classmethod
    def require_https(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("network endpoints must use HTTPS")
        return value.rstrip("/")

    @field_validator("base_accounting_mint", "base_stable_mint", "sol_mint", "trading_wallet_public_key")
    @classmethod
    def require_non_empty_addresses(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Solana addresses must not be empty")
        return value.strip() if value is not None else None

    @field_validator("min_cash_reserve_fraction")
    @classmethod
    def reserve_must_fit_position_limit(
        cls, value: Decimal, info: ValidationInfo
    ) -> Decimal:
        max_position = info.data.get("max_position_fraction") if info.data else None
        if max_position is not None and value + max_position > Decimal(1):
            raise ValueError("cash reserve plus maximum position fraction cannot exceed 100%")
        return value


def load_settings() -> Settings:
    return Settings()
