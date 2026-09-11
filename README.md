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

## Initial boundaries

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

## Repository roadmap

- `core/` — domain contracts and validated configuration
- `security/` — Guardian, policy, credential isolation, emergency controls
- `data/` — acquisition, normalization, quality, provenance, feature store
- `intelligence/` — model laboratory, uncertainty, regime inference
- `agents/` — specialized research/coding/critique agents
- `simulation/` — adversarial digital twin and walk-forward evaluation
- `execution/` — route/timing/size/slippage optimization and venue adapters
- `dashboard/` — command center and forensic decision graph
- `tests/` — unit, integration, property, regression, and safety tests
- `docs/` — architecture, protocols, experiment standards, runbooks

## Development status

The `foundation` branch currently contains the first safety and project contracts. The next stages are data provenance/quality, experiment lineage, simulation primitives, and execution interfaces. Live credentials and private keys are intentionally absent.
