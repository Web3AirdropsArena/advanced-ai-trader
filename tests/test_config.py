from decimal import Decimal

import pytest
from pydantic import ValidationError

from core.config import SOL_MINT, USDC_MINT, Settings


def test_default_accounting_currency_is_usdc() -> None:
    settings = Settings()

    assert settings.base_accounting_mint == USDC_MINT
    assert settings.base_stable_mint == USDC_MINT
    assert settings.sol_mint == SOL_MINT


def test_base_mints_can_be_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASE_ACCOUNTING_MINT", SOL_MINT)
    monkeypatch.setenv("BASE_STABLE_MINT", USDC_MINT)
    monkeypatch.setenv("SOL_MINT", SOL_MINT)

    settings = Settings()

    assert settings.base_accounting_mint == SOL_MINT
    assert settings.base_stable_mint == USDC_MINT
    assert settings.sol_mint == SOL_MINT


def test_wallet_public_key_is_trimmed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRADING_WALLET_PUBLIC_KEY", "  wallet-public-address  ")

    settings = Settings()

    assert settings.trading_wallet_public_key == "wallet-public-address"


def test_empty_wallet_public_key_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRADING_WALLET_PUBLIC_KEY", "   ")

    with pytest.raises(ValidationError):
        Settings()


def test_existing_risk_defaults_remain_unchanged() -> None:
    settings = Settings()

    assert settings.max_position_fraction == Decimal("0.10")
    assert settings.max_portfolio_drawdown == Decimal("0.15")
    assert settings.max_daily_loss_fraction == Decimal("0.03")
    assert settings.min_cash_reserve_fraction == Decimal("0.20")
