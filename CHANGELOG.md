# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[SemVer](https://semver.org/).

## [0.2.0] - 2025

### Added
- **Factor library** (`factors.py`): low-volatility and value (mean-reversion proxy)
  factors alongside momentum, plus cross-sectional z-scoring and a configurable
  composite scorer that blends factors with arbitrary weights.
- **Risk module** (`risk.py`): inverse-volatility (risk-parity) position sizing,
  annualized/portfolio volatility helpers, and volatility-target leverage with a
  configurable cap.
- **Metrics module** (`metrics.py`): CAGR, annualized volatility, Sharpe, Sortino,
  max drawdown, Calmar, win rate, and a bundled `PerformanceReport`.
- **Typed configuration** (`config.py`): pydantic `StrategyConfig` with
  `WeightingScheme` and `RebalanceSchedule` (daily/weekly/monthly) enums and
  full input validation.
- **Configurable engine**: `run_strategy()` drives the full pipeline (composite
  ranking -> sizing -> vol targeting -> scheduled rebalance) and records the
  rebalance count and config on the result; `BacktestResult.metrics()` returns
  the performance report.
- **Reporting** (`report.py`): a rich metrics table and ASCII equity-curve
  sparkline via `render_report()`.
- **Weighted rebalancing**: `Portfolio.rebalance_weighted()` supports arbitrary
  target weights (sub-1.0 sums leave cash for de-risking).
- **CLI subcommands**: `backtest` (fully parameterised) and `rank` (composite
  ranking), in addition to the existing `demo` and `version`.
- **Example**: `examples/factor_rotation.py` end-to-end multi-factor run.
- Test suite expanded from 6 to 87 tests across factors, risk, metrics, config,
  portfolio, engine, report, and CLI.

### Changed
- Bumped version to 0.2.0.
- `run_backtest()` retained for backward compatibility; now delegates to
  `run_strategy()` for named schedules.

## [0.1.0] - 2025

### Added
- Initial release of stock-trading-bot: AI stock trading bot: cross-sectional momentum ranking and portfolio rebalancing.
