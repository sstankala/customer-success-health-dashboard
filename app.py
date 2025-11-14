import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="Customer Success Health Dashboard",
    layout="wide",
)

# -----------------------------
# Helper functions
# -----------------------------
def compute_health_scores(df, weights):
    df = df.copy()

    # Defensive defaults
    df["ARR"] = pd.to_numeric(df["ARR"], errors="coerce").fillna(0)
    df["NPS"] = pd.to_numeric(df["NPS"], errors="coerce").fillna(0)
    df["Tickets_Last_90d"] = pd.to_numeric(df["Tickets_Last_90d"], errors="coerce").fillna(0)
    df["CSAT"] = pd.to_numeric(df["CSAT"], errors="coerce").fillna(0)
    df["Logins_Last_30d"] = pd.to_numeric(df["Logins_Last_30d"], errors="coerce").fillna(0)
    df["Active_Users"] = pd.to_numeric(df["Active_Users"], errors="coerce").fillna(0)
    df["Total_Seats"] = pd.to_numeric(df["Total_Seats"], errors="coerce").fillna(1)  # avoid div by 0

    # Usage % (0–1)
    df["Usage_Ratio"] = (df["Active_Users"] / df["Total_Seats"]).clip(0, 1)

    # Normalize features into 0–1 scores
    # Higher is better: NPS, CSAT, Usage, Logins
    df["score_nps"] = (df["NPS"].clip(-100, 100) + 100) / 200.0
    df["score_csat"] = df["CSAT"].clip(1, 5) / 5.0
    df["score_usage"] = df["Usage_Ratio"]
    df["score_logins"] = (df["Logins_Last_30d"] / df["Logins_Last_30d"].max()).fillna(0)

    # Lower is better: Tickets (we invert)
    df["score_tickets"] = 1 - (df["Tickets_Last_90d"] / df["Tickets_Last_90d"].max()).fillna(0)
    df["score_tickets"] = df["score_tickets"].clip(0, 1)

    # Weighted composite score (0–100)
    w = weights
    df["Health_Score"] = (
        df["score_nps"] * w["nps"]
        + df["score_csat"] * w["csat"]
        + df["score_usage"] * w["usage"]
        + df["score_logins"] * w["logins"]
        + df["score_tickets"] * w["tickets"]
    )

    df["Health_Score"] = (df["Health_Score"] / sum(w.values()) * 100).round(1)

    # Buckets
    df["Health_Band"] = pd.cut(
        df["Health_Score"],
        bins=[-1, 49.9, 74.9, 100],
        labels=["Red", "Yellow", "Green"]
    )

    # Renewal horizon (days)
    today = datetime.today().date()
    df["Renewal_Date"] = pd.to_datetime(df["Renewal_Date"], errors="coerce").dt.date
    df["Days_to_Renewal"] = (df["Renewal_Date"] - today).dt.days

    return df


def expansion_potential(row):
    if row["Health_Band"] == "Green" and row["Usage_Ratio"] > 0.7 and row["NPS"] >= 50:
        return "High"
    if row["Health_Band"] == "Yellow" and row["Usage_Ratio"] > 0.5 and row["NPS"] >= 20:
        return "Medium"
    return "Low"


def renewal_risk(row):
    if row["Health_Band"] == "Red":
        return "High"
    if row["Health_Band"] == "Yellow":
        return "Medium"
    return "Low"


def recommended_actions(row):
    actions = []

    # Health-based
    if row["Health_Band"] == "Red":
        actions.append("Schedule executive-sponsored escalation and detailed recovery plan.")
    elif row["Health_Band"] == "Yellow":
        actions.append("Run focused health check and align on 90-day success plan.")
    else:
        actions.append("Reinforce value with EBR/QBR and explore expansion paths.")

    # Usage
    if row["Usage_Ratio"] < 0.4:
        actions.append("Low adoption: run enablement sessions and map more use cases.")
    elif row["Usage_Ratio"] > 0.8:
        actions.append("High adoption: discuss seat expansion or advanced modules.")

    # Tickets
    if row["Tickets_Last_90d"] > row["Tickets_Last_90d"].median():
        actions.append("High support volume: review top ticket themes and propose fixes.")

    # NPS / CSAT
    if row["NPS"] < 0:
        actions.append("Negative NPS: hold stakeholder interviews and address pain points.")
    elif row["NPS"] >= 50:
        actions.append("Promoter: invite to reference program or case study.")

    if row["CSAT"] < 3.5:
        actions.append("Improve support quality: review SLAs and support playbook.")

    # Renewal
    if row["Days_to_Renewal"] is not None and row["Days_to_Renewal"] <= 120:
        actions.append("Renewal <120 days: lock in mutual success plan and early commit.")

    return " • ".join(actions)


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("⚙️ Configuration")

st.sidebar.markdown("### 1. Upload customer data")
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV (or leave empty to use sample_data.csv)",
    type=["csv"]
)

st.sidebar.markdown("### 2. Health score weights")
nps_w = st.sidebar.slider("NPS weight", 0.0, 5.0, 3.0, 0.5)
csat_w = st.sidebar.slider("CSAT weight", 0.0, 5.0, 2.0, 0.5)
usage_w = st.sidebar.slider("Usage weight", 0.0, 5.0, 3.0, 0.5)
logins_w = st.sidebar.slider("Logins weight", 0.0, 5.0, 1.0, 0.5)
tickets_w = st.sidebar.slider("Tickets weight (lower is better)", 0.0, 5.0, 2.0, 0.5)

weights = {
    "nps": nps_w,
    "csat": csat_w,
    "usage": usage_w,
    "logins": logins_w,
    "tickets": tickets_w,
}

st.sidebar.markdown("---")
st.sidebar.info(
    "Tip: start with default weights. In a real QBR, you can tune weights per segment "
    "or based on your leadership team's priorities."
)

# -----------------------------
# Main layout
# -----------------------------
st.title("📊 Customer Success Health Dashboard")
st.caption(
    "Prioritize accounts by health, renewal risk, and expansion potential. "
    "Built by Sai Tankala – Sr. Customer Success & Service Experience Leader."
)

# Load data
if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file)
else:
    df_raw = pd.read_csv("sample_data.csv")

required_cols = [
    "Customer",
    "Segment",
    "ARR",
    "Renewal_Date",
    "NPS",
    "Tickets_Last_90d",
    "CSAT",
    "Logins_Last_30d",
    "Active_Users",
    "Total_Seats",
]

missing = [c for c in required_cols if c not in df_raw.columns]
if missing:
    st.error(f"Missing required columns in CSV: {missing}")
    st.stop()

df = compute_health_scores(df_raw, weights)
df["Expansion_Potential"] = df.apply(expansion_potential, axis=1)
df["Renewal_Risk"] = df.apply(renewal_risk, axis=1)
df["Recommended_Actions"] = df.apply(recommended_actions, axis=1)

# -----------------------------
# KPI summary row
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

total_arr = df["ARR"].sum()
at_risk_arr = df.loc[df["Health_Band"].isin(["Red", "Yellow"]), "ARR"].sum()

near_term_mask = df["Days_to_Renewal"].between(0, 180, inclusive="both")
near_term_arr = df.loc[near_term_mask, "ARR"].sum()
red_customers = (df["Health_Band"] == "Red").sum()

with col1:
    st.metric("Total ARR", f"${total_arr:,.0f}")
with col2:
    st.metric("ARR (Yellow + Red)", f"${at_risk_arr:,.0f}")
with col3:
    st.metric("ARR Renewing in 180 Days", f"${near_term_arr:,.0f}")
with col4:
    st.metric("# Red Accounts", int(red_customers))

st.markdown("---")

# -----------------------------
- Charts
# -----------------------------
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Health Band Distribution")
    band_counts = df["Health_Band"].value_counts().reindex(["Green", "Yellow", "Red"]).fillna(0)
    st.bar_chart(band_counts)

with right_col:
    st.subheader("ARR by Health Band")
    arr_by_band = df.groupby("Health_Band")["ARR"].sum().reindex(["Green", "Yellow", "Red"]).fillna(0)
    st.bar_chart(arr_by_band)

st.markdown("---")

# -----------------------------
# Detailed table + filters
# -----------------------------
st.subheader("Account-level view")

seg_filter = st.multiselect(
    "Filter by Segment",
    options=sorted(df["Segment"].unique()),
    default=sorted(df["Segment"].unique())
)

band_filter = st.multiselect(
    "Filter by Health Band",
    options=["Green", "Yellow", "Red"],
    default=["Green", "Yellow", "Red"],
)

risk_filter = st.multiselect(
    "Filter by Renewal Risk",
    options=["Low", "Medium", "High"],
    default=["Low", "Medium", "High"],
)

filtered = df[
    df["Segment"].isin(seg_filter)
    & df["Health_Band"].isin(band_filter)
    & df["Renewal_Risk"].isin(risk_filter)
]

display_cols = [
    "Customer",
    "Segment",
    "ARR",
    "Renewal_Date",
    "Health_Score",
    "Health_Band",
    "Renewal_Risk",
    "Expansion_Potential",
    "NPS",
    "CSAT",
    "Usage_Ratio",
    "Tickets_Last_90d",
    "Days_to_Renewal",
    "Recommended_Actions",
]

st.dataframe(filtered[display_cols].sort_values("Health_Score", ascending=True))

st.markdown("---")
st.markdown("#### Data Preview")
with st.expander("Show raw input data"):
    st.dataframe(df_raw)
