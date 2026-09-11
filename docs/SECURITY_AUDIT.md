# Security and reliability audit baseline

## High-risk boundaries checked

- Private keys/seed phrases are excluded by repository policy and `.gitignore`.
- Runtime configuration requires HTTPS for network endpoints.
- Default trading mode is research.
- Guardian is independent from strategy generation.
- Guardian rejects emergency-stop states and hard drawdown/daily-loss breaches.
- Position sizing is capped by policy.
- High uncertainty can force HOLD/REJECT behavior.
- Execution safety rejects invalid side/notional/slippage inputs and prevents unsafe mode transitions.
- Jupiter adapter is a research/execution boundary and does not contain a wallet signer.
- Local API binds to `127.0.0.1` by default.
- CI runs linting, static type checking and tests on changes.

## Reliability hazards still requiring empirical validation

No software audit can prove that a trading system has zero defects or that a strategy will make money. The following must be continuously tested with real historical/replay data:

1. look-ahead leakage and timestamp misalignment;
2. stale or duplicated market data;
3. liquidity collapse and price-impact nonlinearities;
4. failed, delayed, reordered or partially executed swaps;
5. RPC/API outages and rate limits;
6. token metadata changes and malicious token behavior;
7. model drift and uncertainty miscalibration;
8. correlated strategy failures;
9. storage corruption and incomplete checkpoints;
10. resource exhaustion on the local laptop.

## Production gate

Do not promote a strategy or model merely because tests pass. A promotion record should contain dataset/version hashes, feature definitions, code/dependency versions, random seeds, validation windows, benchmark comparisons, confidence intervals where applicable, stress results, and rollback information.

## Explicit non-goals

- No secret extraction or wallet-key exposure.
- No automatic transfer/withdrawal authority for an LLM.
- No unrestricted code self-modification in the live process.
- No leverage in V1 live trading.
- No claim of guaranteed profitability or a guaranteed maximum failure rate.
