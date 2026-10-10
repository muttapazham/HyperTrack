"""HyperTrack dashboard.  Run:  streamlit run app.py"""
from datetime import date

import pandas as pd
import streamlit as st

from hypertrack import analysis as A
from hypertrack import models as M
from hypertrack import plots, reports
from hypertrack.config import FEATURES, Thresholds
from hypertrack.storage import Database, StorageError
from hypertrack.validation import ValidationError, validate_entry

st.set_page_config(page_title="HyperTrack", layout="wide")


@st.cache_resource
def get_db() -> Database:
    return Database()


db = get_db()
st.title("HyperTrack")
st.caption("Personal sweat-severity log. Data stays on this computer. Not medical advice.")

# ------------------------------------------------------------------ sidebar
all_df = db.dataframe()
st.sidebar.header("Filters")
if all_df.empty:
    lo = hi = date.today()
else:
    lo, hi = all_df["entry_date"].min().date(), all_df["entry_date"].max().date()
sel = st.sidebar.date_input("Date range", (lo, hi), min_value=min(lo, date(2000, 1, 1)),
                            max_value=max(hi, date.today()))
# While the user is mid-selection Streamlit returns a 1-tuple; fall back to full range.
start, end = sel if isinstance(sel, (tuple, list)) and len(sel) == 2 else (lo, hi)
st.sidebar.header("Thresholds (not medically validated)")
th = Thresholds(
    st.sidebar.slider("Severe severity >=", 1, 10, 7),
    st.sidebar.slider("High stress >=", 0, 10, 7),
    st.sidebar.slider("High humidity >=", 0, 100, 70),
    st.sidebar.slider("Poor sleep < (hours)", 0.0, 12.0, 6.0, 0.5),
)
df = db.dataframe(start, end)
daily = A.daily_frame(df)

tab_over, tab_log, tab_stats, tab_corr, tab_anom, tab_ml, tab_export = st.tabs(
    ["Overview", "Add / edit", "Statistics", "Correlation & lag", "Anomalies", "Machine learning", "Export & privacy"])

# ----------------------------------------------------------------- overview
with tab_over:
    if daily.empty:
        st.info("No entries in this range. Use 'Add / edit' to log one, or import a CSV under 'Export & privacy'.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Days logged", len(daily))
        c2.metric("Average severity", f"{daily['severity'].mean():.2f}")
        w = A.worst_entry(df)
        c3.metric("Worst day", f"{w['severity']:.0f}/10", str(w["entry_date"].date()), delta_color="off")
        cmp = A.compare_recent_windows(daily)
        c4.metric("Last 7 vs previous 7 days",
                  "n/a" if pd.isna(cmp["change"]) else f"{cmp['mean_current']:.2f}",
                  None if pd.isna(cmp["change"]) else f"{cmp['change']:+.2f}", delta_color="inverse")
        if not cmp["reliable"]:
            st.caption(f"Comparison uses {cmp['n_current']} and {cmp['n_previous']} days: too few to be reliable.")
        cols = st.multiselect("Variables", ["severity", *FEATURES], default=["severity", "stress", "sleep_hours"])
        roll = st.slider("Rolling mean (days)", 0, 30, 7)
        show_anom = st.checkbox("Highlight anomalies", True)
        if cols:
            st.pyplot(plots.trend_plot(daily, cols, A.detect_anomalies(daily) if show_anom else None, roll))
        st.subheader("Weekly / monthly summary")
        freq = st.radio("Period", ["W", "M"], horizontal=True, format_func=lambda x: {"W": "Weekly", "M": "Monthly"}[x])
        st.dataframe(A.summarize(daily, freq).round(2))
        st.subheader("Daily log")
        st.dataframe(df.drop(columns=[]).sort_values("entry_date", ascending=False), use_container_width=True)

# ---------------------------------------------------------------- add / edit
with tab_log:
    st.subheader("New entry")
    with st.form("new"):
        d = st.date_input("Date", date.today(), max_value=date.today())
        a, b, c = st.columns(3)
        sev = a.number_input("Severity (1-10)", 1, 10, 5)
        temp = b.number_input("Temperature (°C)", -30.0, 60.0, 25.0, 0.5)
        hum = c.number_input("Humidity (%)", 0, 100, 60)
        stress = a.number_input("Stress (0-10)", 0, 10, 4)
        sleep = b.number_input("Sleep (hours)", 0.0, 24.0, 7.0, 0.5)
        act = c.number_input("Activity (0-10)", 0, 10, 5)
        if st.form_submit_button("Save"):
            try:
                entry = validate_entry(dict(entry_date=d, severity=sev, temperature=temp, humidity=hum,
                                            stress=stress, sleep_hours=sleep, activity=act))
                dup = not df[df["entry_date"].dt.date == d].empty
                db.add(entry)
                st.success("Saved." + (" Note: this date already had an entry; both are kept and averaged in analysis." if dup else ""))
            except (ValidationError, StorageError) as exc:
                st.error(str(exc))
    st.subheader("Edit or delete")
    if not all_df.empty:
        ids = all_df.sort_values("entry_date", ascending=False)["id"].tolist()
        eid = st.selectbox("Entry", ids, format_func=lambda i: f"#{i}  {all_df.set_index('id').loc[i, 'entry_date'].date()}")
        cur = db.get(int(eid))
        with st.form("edit"):
            nd = st.date_input("Date ", cur.entry_date, max_value=date.today())
            a, b, c = st.columns(3)
            e_sev = a.number_input("Severity", 1, 10, int(cur.severity))
            e_tmp = b.number_input("Temperature", -30.0, 60.0, float(cur.temperature), 0.5)
            e_hum = c.number_input("Humidity", 0, 100, int(cur.humidity))
            e_str = a.number_input("Stress", 0, 10, int(cur.stress))
            e_slp = b.number_input("Sleep", 0.0, 24.0, float(cur.sleep_hours), 0.5)
            e_act = c.number_input("Activity", 0, 10, int(cur.activity))
            col_s, col_d = st.columns(2)
            if col_s.form_submit_button("Update"):
                try:
                    db.update(int(eid), entry_date=nd, severity=e_sev, temperature=e_tmp, humidity=e_hum,
                              stress=e_str, sleep_hours=e_slp, activity=e_act)
                    st.success("Updated. Reload the page to refresh tables.")
                except (ValidationError, StorageError) as exc:
                    st.error(str(exc))
            if col_d.form_submit_button("Delete"):
                db.delete(int(eid))
                st.warning("Deleted. Reload the page to refresh tables.")

# --------------------------------------------------------------- statistics
with tab_stats:
    if daily.empty:
        st.info("No data.")
    else:
        st.write(A.small_sample_note(len(daily)) or "")
        rows = {c: A.describe(daily[c]) for c in ["severity", *FEATURES]}
        st.dataframe(pd.DataFrame(rows).T.round(2))
        for col, thr, above in [("stress", th.high_stress, True), ("sleep_hours", th.low_sleep, False)]:
            r = A.compare_by_threshold(daily, col, thr, above)
            st.markdown(f"**{r['rule']}**: flagged days mean **{r['flagged']['mean']:.2f}** "
                        f"(n={r['flagged']['n']}, 95% CI {r['flagged']['ci_low']:.2f}–{r['flagged']['ci_high']:.2f}) "
                        f"vs other days **{r['other']['mean']:.2f}** (n={r['other']['n']}); p = {r['p_value']:.3f}")
            if r["note"]:
                st.caption(r["note"])
        st.subheader("Fixed rules vs your thresholds (entries)")
        st.dataframe(A.compare_thresholds(df, th))
        st.caption(A.THRESHOLD_DISCLAIMER)

# -------------------------------------------------------------- correlation
with tab_corr:
    if len(daily) < 3:
        st.info("Need at least 3 days.")
    else:
        method = st.radio("Method", ["pearson", "spearman"], horizontal=True)
        st.dataframe(A.correlations(daily, method).round(3))
        st.pyplot(plots.correlation_heatmap(A.correlation_matrix(daily)))
        st.info(A.CORRELATION_EXPLANATION)
        var = st.selectbox("Lag analysis: factor", FEATURES, index=FEATURES.index("stress"))
        max_lag = st.slider("Max lag (days)", 1, 14, 7)
        lag = A.lag_analysis(daily, var, max_lag)
        st.pyplot(plots.lag_plot(lag, var))
        st.dataframe(lag.round(3))
        st.caption(A.LAG_NOTE)

# ---------------------------------------------------------------- anomalies
with tab_anom:
    if daily.empty:
        st.info("No data.")
    else:
        w_ = st.slider("Baseline window (recorded days)", 5, 30, 14)
        z_ = st.slider("z-score threshold", 1.0, 4.0, 2.0, 0.5)
        res = A.detect_anomalies(daily, w_, z_)
        st.dataframe(res[res["is_anomaly"]].round(2))
        st.caption(A.ANOMALY_NOTE)

# ---------------------------------------------------------------------- ML
with tab_ml:
    st.warning(M.LIMITATIONS)
    try:
        reg = M.train_regressors(daily)
        st.subheader("Prediction (later days held out)")
        st.dataframe(reg.metrics.round(3))
        for n in reg.notes[1:]:
            st.caption(n)
        imp = M.importance_table(reg, daily)
        st.dataframe(imp.round(3))
        st.caption(M.IMPORTANCE_NOTE)
        st.subheader("Classification (low / moderate / high)")
        cl = M.classify_severity(daily)
        st.dataframe(cl["confusion_matrix"])
        st.dataframe(cl["report"].round(2))
        st.caption(cl["note"])
        st.subheader("Forecast")
        fc = M.forecast_severity(daily)
        st.dataframe(fc["metrics"].round(3))
        st.pyplot(plots.forecast_plot(fc))
        st.caption(fc["note"])
    except M.InsufficientDataError as exc:
        st.info(f"{exc} Log more days (or load sample data) to unlock this tab.")

# ------------------------------------------------------------------- export
with tab_export:
    if not df.empty:
        st.download_button("Download filtered CSV", df.drop(columns=["id"]).to_csv(index=False), "hypertrack_export.csv")
        if st.button("Build PDF report"):
            reports.build_pdf(df, "report.pdf", th)
            with open("report.pdf", "rb") as f:
                st.download_button("Download PDF", f.read(), "hypertrack_report.pdf")
    up = st.file_uploader("Import CSV (legacy C++ format or headed)", type="csv")
    if up is not None and st.button("Import"):
        tmp = "_upload.csv"
        with open(tmp, "wb") as f:
            f.write(up.getvalue())
        rep = db.import_csv(tmp)
        st.success(f"Imported {rep.imported}, skipped {rep.skipped_duplicates} duplicates, rejected {len(rep.rejected)}.")
        for line, why in rep.rejected:
            st.caption(f"line {line}: {why}")
    st.subheader("Privacy")
    st.write(f"Everything is stored in a local SQLite file: `{db.path}`. Nothing is uploaded anywhere.")
    if st.checkbox("I understand this permanently deletes ALL records"):
        if st.button("Delete all records"):
            st.warning(f"Deleted {db.delete_all()} entries.")
