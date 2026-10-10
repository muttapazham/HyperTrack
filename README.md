# HyperTrack

Log daily **sweating severity** together with **temperature, humidity, stress, sleep and activity**, then explore trends and *possible* personal triggers with statistics, charts and (carefully caveated) machine learning.

> **Not a medical device.** Thresholds and findings are personal and not medically validated. Associations are not causes. If sweating worries you, see a clinician.

HyperTrack began as a C++ console app (kept in [`legacy/prj.cpp`](legacy/prj.cpp)) and was rebuilt in Python.

![Trend](docs/trend.png)

## Features

| Area | What it does |
|---|---|
| Storage | SQLite with schema `CHECK` constraints; add / list / edit / delete; date filtering; CSV import (legacy C++ format or headed); delete-all |
| Validation | Real calendar dates (no 31 Feb, no future dates), range checks, non-numeric/NaN/inf rejected, all errors reported at once |
| Reports | Weekly & monthly summaries with day counts; last-7 vs previous-7-day comparison |
| Statistics | mean / median / std / 95% CI; high- vs low-stress and low- vs adequate-sleep severity (Welch t-test); sample-size warnings |
| Correlation | Pearson/Spearman with p-values, heatmap, plain-language strength labels |
| Thresholds | Configurable severe/stress/humidity/sleep cut-offs compared with the original fixed rules |
| Anomalies | Rolling-baseline z-score (baseline excludes the day itself), highlighted on the trend graph |
| Lag analysis | Does stress/sleep *k* days earlier relate to today's severity? |
| ML | Baselines vs Linear Regression vs Random Forest (MAE/RMSE/R²), time-aware split, permutation importance, low/moderate/high classifier (confusion matrix, precision/recall/F1), moving-average vs exponential-smoothing forecast. Refuses to run with < 30 recorded days |
| Export | Filtered CSV (+ weekly summary), PDF report with graphs, stats, date range, sample size and methods |
| Privacy | Local SQLite file only, git-ignored; one-command wipe; nothing is uploaded |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# try it with synthetic data (no personal info)
python -m hypertrack --db data/demo.db import data/sample_data.csv
HYPERTRACK_DB=data/demo.db streamlit run app.py     # Windows PowerShell: $env:HYPERTRACK_DB="data/demo.db"; streamlit run app.py
```

Use your own data: `python -m hypertrack import path/to/Hypertrackv1.csv` (your old C++ file imports as-is), then `streamlit run app.py`.

### Command line

```bash
python -m hypertrack add                          # interactive, re-asks on bad input
python -m hypertrack list --start 2026-07-01
python -m hypertrack edit 3 --severity 6
python -m hypertrack delete 3
python -m hypertrack summary --period M
python -m hypertrack stats
python -m hypertrack anomalies --window 14 --z 2
python -m hypertrack plot --columns severity stress --out trend.png
python -m hypertrack export --out my_export.csv
python -m hypertrack pdf --out report.pdf --stress 8 --sleep 6.5
python -m hypertrack wipe                         # delete ALL records
```

## Tests

```bash
python -m unittest discover -s tests -t .
```
Covers validation boundaries, CRUD, malformed/duplicate CSV import, hand-computed statistics, threshold boundaries (`>=` vs `<`), anomaly and lag detection on known signals, train/test chronology, and report generation.

## Project layout

```
app.py                 Streamlit dashboard (UI only)
hypertrack/
  config.py            limits, default thresholds, DB path
  validation.py        all input checks
  storage.py           SQLite + CSV import
  analysis.py          statistics, correlation, anomalies, lag (pure functions)
  models.py            ML: regression, classification, forecasting
  plots.py             matplotlib figures
  reports.py           CSV / PDF export
  cli.py               command-line interface
tests/  data/sample_data.csv  docs/  legacy/prj.cpp  scripts/
```
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/DECISIONS.md](docs/DECISIONS.md).

## Privacy

Data lives in `data/hypertrack.db` on your machine (override with `HYPERTRACK_DB`). It is git-ignored. Only the synthetic `data/sample_data.csv` is meant to be committed. Never commit your real CSV/DB.

## Known limitations

- Single-person, self-reported data; short histories give unstable statistics and ML results.
- Stress and activity scales are assumed to be 0–10 (the original app never specified a range); change `FIELD_LIMITS` in `config.py` if yours differs.
- Forecasts are flat (no knowledge of future weather/stress); the uncertainty band is approximate.
- Multiple entries per day are averaged for analysis (fractional daily severities are possible).
- Dashboard widgets (`app.py`) are not covered by automated tests; check them manually after install.

## Future improvements
Seasonality-aware forecasting, mixed-effects models for repeated measures, per-factor interaction analysis, optional encrypted DB.
