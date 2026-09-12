# Advanced AI Trader — local runbook

## 1. Supported baseline

Ubuntu Linux, Python 3.11+, Git, and enough free disk for datasets/checkpoints. The application is designed to run locally and defaults to research mode.

## 2. Clone and create the environment

```bash
git clone <your-repository-url>
cd advenced-ai-trader
git checkout foundation
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
cp .env.example .env
```

Never put a seed phrase, private key, wallet JSON, or exchange secret in `.env` or the repository.

## 3. First verification

```bash
ruff check .
mypy core data execution intelligence research security simulation
pytest -q
```

Then start the local control plane:

```bash
advanced-ai-trader
```

Open `http://127.0.0.1:8000/docs` for the API documentation and use `/health` to verify the service.

## 4. Ollama

Install Ollama using the official Linux installer, then verify:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama --version
```

Recommended local roles for this laptop are intentionally small and sequential rather than running many large models concurrently:

- Coding/repository agent: `qwen3-coder` or `gpt-oss:20b`.
- General research/reasoning: a current compact reasoning model available locally in Ollama.
- Fast critic/classifier: a smaller model such as a Flash-class model available locally.
- Embeddings: choose a current local embedding model from the Ollama model catalog.

Model choice is a replaceable configuration, not part of the quantitative trading core. The trading engine must remain deterministic and authoritative over LLM suggestions.

On a CPU-only 32 GB machine, prefer quantized models and one heavy inference job at a time. Do not attempt to keep multiple 20B+ models resident unless memory measurements show it is safe.

## 5. Architecture rule for LLMs

LLMs may propose:

- hypotheses
- features
- experiments
- code changes
- strategy ideas
- research summaries
- adversarial tests

LLMs may not directly bypass the Guardian, sign transactions, expose private keys, change immutable risk limits, or promote unvalidated code/models into live execution.

## 6. Trading modes

`research` → `paper` → `shadow` → `tiny_live`.

The repository currently defaults to `research`. Do not jump directly to live trading. A live wallet must be isolated from the general AI process and protected by an independent policy layer.

## 7. Jupiter

Use the current Jupiter Developer Platform/API rather than old deprecated endpoints. Keep API keys outside Git. Start with the free tier and local caching/rate control.

The execution adapter should treat quotes as observations, not guaranteed fills. Record quote time, route, expected output, execution time, actual fill, fees, slippage, latency and failures for later attribution.

## 8. Data

Keep raw observations immutable. Store normalized/derived datasets separately. Every observation should retain source, timestamps, quality state and provenance. Never train on future information relative to a simulated decision timestamp.

## 9. Before any real-money deployment

Run all of:

1. historical backtests across multiple regimes;
2. walk-forward validation;
3. leakage tests;
4. transaction-cost/slippage tests;
5. liquidity and failed-execution stress tests;
6. adversarial simulations;
7. paper trading;
8. shadow execution;
9. tiny-live validation with hard capital limits;
10. rollback/emergency-stop verification.

A high backtest win rate is not a deployment criterion. Evaluate expectancy, drawdown, tail loss, Sharpe/Sortino/Calmar, turnover, realized slippage, uncertainty calibration and robustness.

## 10. Recovery

If the system detects corrupted data, model degradation, infrastructure instability, abnormal execution, or policy violations, it must reduce risk or enter safe mode. Preserve experiment lineage and incident evidence before recovery.
