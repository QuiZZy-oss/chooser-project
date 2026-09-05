# Data Specification

Chooser Option Pricing Project. This document lists every data field the project collects, where it comes from, how often, over what window, and what role it plays. It covers raw collected data only. Features derived from these fields (returns, rolling volatilities, correlations) are produced in the Week 3 preprocessing step and documented separately.

## 1. Scope

Four categories of raw data:

- **Financial**: the underlying's price, its dividends, and the market volatility index.
- **Macroeconomic**: the risk-free interest rate.
- **Sentiment**: a news-derived sentiment score for the underlying.
- **Market target**: actual traded option prices, used as the ground truth for baseline evaluation and as Track B labels.

## 2. Fixed contract parameters

These are chosen, not collected. They live in `config.yaml`, listed here for reference.

| Parameter | Symbol | Value |
|---|---|---|
| Underlying | — | JPM |
| Strike | K | 150 |
| Time to final expiry | T | 1 year |
| Time to choice date | t1 | (set in config) |

## 3. Field table

Date range is 2018-01-01 to 2024-12-31 for every field. Role tags: **Formula input** means the field enters the BSM chooser pricer directly (with its symbol); **Feature** means it feeds the ML models; **Target** means it is the value models are scored against. A field can carry more than one role.

| # | Category | Field | Source | Frequency | Date range | Role |
|---|---|---|---|---|---|---|
| 1 | Financial | JPM close price | Yahoo Finance (`JPM`) | daily | 18–24 | Formula input (S); feature base |
| 2 | Financial | JPM dividends | Alpha Vantage / Yahoo Finance | as declared | 18–24 | Formula input (q) |
| 3 | Financial | VIX close | Yahoo Finance (`^VIX`) | daily | 18–24 | Feature |
| 4 | Macroeconomic | 1-year Treasury rate | FRED (`DGS1`) | daily | 18–24 | Formula input (r) |
| 5 | Macroeconomic | 3-month Treasury rate | FRED (`DGS3MO`) | daily | 18–24 | Feature (rate momentum) |
| 6 | Sentiment | News sentiment score | Reuters News API | daily | 18–24 | Feature |
| 7 | Market target | JPM option transaction prices | CME Group Historical Data | per trade | 18–24 | Target |

## 4. Field notes

**1. JPM close price.** Decide between adjusted and raw close and hold to it across the project; mixing the two is a silent source of error. Adjusted close accounts for splits and dividends and is the usual choice for return series. Record the choice in the pull script.

**2. JPM dividends.** Supplies the continuous dividend yield q used in the cost of carry `b = r - q`. Dividends arrive on declaration dates rather than daily, so they are forward-filled onto the daily calendar during preprocessing.

**3. VIX close.** The market's forward read on 30-day volatility. It never enters the BSM formula; it is the primary feature meant to explain the volatility BSM holds constant.

**4. 1-year Treasury rate.** The risk-free rate r. The 1-year tenor is chosen to match the contract's 1-year expiry T. Convert from the quoted percentage to a decimal before use.

**5. 3-month Treasury rate.** Collected so the rate-momentum feature (the spread and change between short and one-year rates) can be built. Not a formula input.

**6. News sentiment score.** A score in the range 0 to 1 summarizing news tone for JPM. Days with no news are filled during preprocessing; record the fill rule.

**7. JPM option transaction prices.** The actual prices the pricer is judged against. These are the targets for baseline MAE/RMSE and the labels for Track B. Align each traded price to its trade date so a prediction and an actual sit on the same row.

## 5. Collection conventions

- **Storage**: raw pulls saved to `data/raw/` as Parquet, one file per source, keyed on date. Raw files are git-ignored; the pull scripts are versioned.
- **API keys**: kept in a git-ignored `.env` file, loaded at runtime. No key appears in the repo.
- **Calendar**: all series are aligned onto the trading-day calendar in preprocessing, so each output row is one trading day with every field present.
- **Window rationale**: the 2018–2024 span contains the 2020 COVID volatility spike and the 2022 rate-hike cycle, so the later failure-mode and stress analysis has real high-volatility regimes to test against.
