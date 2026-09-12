from decimal import Decimal

from core.config import Settings
from core.decision import Decision, DecisionAction, GuardianVerdict
from security.guardian import Guardian


def make_settings() -> Settings:
    return Settings(
        max_position_fraction=Decimal("0.10"),
        max_portfolio_drawdown=Decimal("0.15"),
        max_daily_loss_fraction=Decimal("0.03"),
        min_cash_reserve_fraction=Decimal("0.20"),
    )


def make_decision(**overrides) -> Decision:
    values = {
        "action": DecisionAction.BUY,
        "confidence": 0.8,
        "target_fraction": Decimal("0.05"),
        "rationale": "test",
        "model_version": "test-1",
        "uncertainty": 0.2,
    }
    values.update(overrides)
    return Decision(**values)


def test_caps_position_size() -> None:
    result = Guardian(make_settings()).evaluate(
        make_decision(target_fraction=Decimal("0.50"))
    )
    assert result.allowed_fraction == Decimal("0.10")
    assert result.verdict == GuardianVerdict.REDUCE


def test_rejects_drawdown_breach() -> None:
    result = Guardian(make_settings()).evaluate(
        make_decision(), current_drawdown=Decimal("0.15")
    )
    assert result.verdict == GuardianVerdict.REJECT
    assert result.allowed_fraction == 0


def test_holds_when_uncertainty_is_too_high() -> None:
    result = Guardian(make_settings()).evaluate(make_decision(uncertainty=0.9))
    assert result.verdict == GuardianVerdict.HOLD
    assert result.allowed_fraction == 0


def test_holds_when_confidence_is_too_low() -> None:
    result = Guardian(make_settings()).evaluate(make_decision(confidence=0.1))
    assert result.verdict == GuardianVerdict.HOLD
    assert result.allowed_fraction == 0


def test_holds_hold_and_no_trade_actions() -> None:
    for action in (DecisionAction.HOLD, DecisionAction.NO_TRADE):
        result = Guardian(make_settings()).evaluate(make_decision(action=action))
        assert result.verdict == GuardianVerdict.HOLD
        assert result.allowed_fraction == 0


def test_emergency_stop_blocks_all_decisions() -> None:
    guardian = Guardian(make_settings())
    guardian.emergency_stop()
    result = guardian.evaluate(make_decision())
    assert result.verdict == GuardianVerdict.EMERGENCY_STOP


def test_negative_telemetry_fails_closed() -> None:
    result = Guardian(make_settings()).evaluate(
        make_decision(), current_drawdown=Decimal("-0.01")
    )
    assert result.verdict == GuardianVerdict.REJECT
    assert "cannot be negative" in result.reasons[0]


def test_non_finite_telemetry_fails_closed() -> None:
    result = Guardian(make_settings()).evaluate(
        make_decision(), daily_loss=Decimal("NaN")
    )
    assert result.verdict == GuardianVerdict.REJECT
    assert "non-finite" in result.reasons[0]
