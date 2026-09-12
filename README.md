# Advanced AI Trader

Autonomous research and execution platform for spot crypto trading, designed around scientific reproducibility, adaptive intelligence, and independent capital protection.

> **Current status: research-only foundation. Live trading is not enabled.**

## Design principles

- **Intelligence proposes; the Guardian disposes.** No model, agent, or LLM can directly authorize an order.
- **Research before capital.** New models and strategies must survive reproducible evaluation before promotion.
- **No forced trades.** Uncertainty can result in waiting or no-trade.
- **Spot-only V1.** Leverage is outside the live execution boundary.
- **Venue-aware, venue-portable.** Solana/Jupiter is the first execution environment while core intelligence remains portable.
- **Evidence over narratives.** Every promoted artifact needs lineage, validation, and rollback metadata.
- **Small-capital aware.** Fees, slippage, liquidity, and minimum executable size matter from the first simulation.
- **Stable accounting.** USDC is the default portfolio accounting unit; SOL/WSOL remains a supported trading base asset.

## Architecture

```text
Market / on-chain / external data
              |
              v
       Data Quality Layer
              |
              v
     Research + Model Lab
              |
              v
     Strategy / Portfolio AI
              |
              v
       Decision Proposal
              |
              v
     +-------------------+
     | Independent       |
     | Guardian / Policy |
     +-------------------+
              |
        approved only
              v
       Execution Engine
              |
              v
       Solana / Jupiter
```

The Guardian is deliberately independent of strategy generation. It enforces hard loss, drawdown, sizing, uncertainty, and emergency-stop boundaries. Those boundaries are not optimization targets and are not negotiable by an AI agent.

## Repository layout

- `core/` — domain contracts and validated configuration
- `security/` — Guardian, policy, emergency controls
- `data/` — acquisition, normalization, quality, provenance, feature store
- `intelligence/` — model laboratory, uncertainty, regime inference
- `research/` — experiment lineage and reproducibility
- `execution/` — route/timing/size/slippage optimization and venue adapters
- `simulation/` — portfolio simulation and future adversarial digital twin
- `app/` — local FastAPI control plane and CLI
- `tests/` — unit and safety regression tests
- `docs/` — architecture and local runbook

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
ruff check .
mypy core data execution intelligence research security simulation
pytest -q
advanced-ai-trader
```

Then open `http://127.0.0.1:8000/docs`.

### Environment configuration

The example environment configures the Jupiter Developer Platform key, a public wallet address for telemetry, and the canonical Solana base mints:

```dotenv
JUPITER_API_KEY="your_jup_developer_portal_key"
TRADING_WALLET_PUBLIC_KEY="your_solana_public_address"
BASE_ACCOUNTING_MINT="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" # USDC
BASE_STABLE_MINT="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" # USDC
SOL_MINT="So11111111111111111111111111111111111111112" # WSOL
```

USDC is the default accounting currency because it provides a stable unit for portfolio value, PnL, drawdown, and risk limits. SOL can still be used as a trading base asset without making SOL/USD price movement appear as trading performance. Replace placeholder credentials locally; never commit real API keys or private signing material.

See [`docs/RUNBOOK.md`](docs/RUNBOOK.md) for the complete laptop/Ollama setup and the required research-to-live deployment ladder.

## Safety boundary

The default mode is `research`. No private key is stored in this repository and the general AI/LLM process is not allowed to sign transactions. The intended deployment ladder is:

`research → backtest → walk-forward → stress → paper → shadow → tiny_live → validated scaling`

A live wallet must be isolated and protected by independent policy enforcement. Real-money activation remains a deliberate deployment step, not an automatic consequence of successful training.

## Jupiter integration

The execution layer is intentionally abstracted from a particular Jupiter API version. Current production integration should use the current Jupiter Developer Platform rather than legacy endpoints. Quote data is treated as an observation: the system records expected output, route, timestamp, execution result, realized fees/slippage and failures so execution quality can be learned empirically.

## Development status

The `foundation` branch contains the safety contracts, provenance/quality primitives, token universe checks, execution safety, Jupiter adapter boundary, deterministic portfolio simulation, experiment lineage, local API, CI, and the laptop runbook. Larger research components are designed as replaceable modules so they can be validated independently before they receive capital.
