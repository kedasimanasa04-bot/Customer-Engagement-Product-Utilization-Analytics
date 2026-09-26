import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Customer Retention Analytics",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv("European_Bank.csv")
    median_balance = df["Balance"].median()

    def segment(row):
        if row["IsActiveMember"] == 0 and row["Balance"] >= median_balance:
            return "High-Value Disengaged"
        if row["IsActiveMember"] == 1 and row["NumOfProducts"] >= 2:
            return "Engaged & Deep Relationship"
        if row["IsActiveMember"] == 0 and row["NumOfProducts"] == 1:
            return "Disengaged & Shallow Relationship"
        if row["IsActiveMember"] == 1 and row["NumOfProducts"] == 1:
            return "Active but Low Product"
        return "Other"

    df["BehavioralSegment"] = df.apply(segment, axis=1)
    df["EngagementStatus"] = df["IsActiveMember"].map({0: "Inactive", 1: "Active"})
    df["CreditCardStatus"] = df["HasCrCard"].map({0: "No", 1: "Yes"})
    return df, median_balance

df, median_balance = load_data()

st.title("Customer Engagement & Product Utilization Analytics")
st.caption("Retention strategy analysis | Financial Analyst Internship Project")

# Sidebar filters
st.sidebar.header("Filters")
geographies = st.sidebar.multiselect(
    "Geography",
    sorted(df["Geography"].unique()),
    default=sorted(df["Geography"].unique())
)
engagement = st.sidebar.multiselect(
    "Engagement",
    ["Active", "Inactive"],
    default=["Active", "Inactive"]
)
product_min, product_max = int(df["NumOfProducts"].min()), int(df["NumOfProducts"].max())
product_range = st.sidebar.slider(
    "Number of Products",
    product_min, product_max,
    (product_min, product_max)
)
balance_min = float(df["Balance"].min())
balance_max = float(df["Balance"].max())
balance_threshold = st.sidebar.slider(
    "Minimum Balance",
    min_value=balance_min,
    max_value=balance_max,
    value=balance_min,
    step=1000.0
)

filtered = df[
    df["Geography"].isin(geographies)
    & df["EngagementStatus"].isin(engagement)
    & df["NumOfProducts"].between(product_range[0], product_range[1])
    & (df["Balance"] >= balance_threshold)
].copy()

def churn_rate(data):
    return data["Exited"].mean() if len(data) else 0

# KPIs
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Customers", f"{len(filtered):,}")
c2.metric("Churned", f"{int(filtered['Exited'].sum()):,}")
c3.metric("Churn Rate", f"{churn_rate(filtered):.2%}")
c4.metric("Avg Products", f"{filtered['NumOfProducts'].mean():.2f}" if len(filtered) else "0.00")
high_value_rate = (
    ((filtered["IsActiveMember"] == 0) & (filtered["Balance"] >= median_balance)).mean()
    if len(filtered) else 0
)
c5.metric("High-Value Disengagement", f"{high_value_rate:.2%}")

st.divider()

# High-value detector
st.subheader("High-Value Disengaged Customer Detector")
hv = filtered[
    (filtered["IsActiveMember"] == 0) &
    (filtered["Balance"] >= median_balance)
].copy()
st.write(
    f"Median balance threshold: **₹{median_balance:,.2f}**. "
    f"Customers matching the rule: **{len(hv):,}**. "
    f"Observed churn rate: **{churn_rate(hv):.2%}**."
)

if len(hv):
    display_cols = [
        "CustomerId", "Geography", "Age", "Balance",
        "NumOfProducts", "EstimatedSalary", "Exited"
    ]
    st.dataframe(
        hv[display_cols].sort_values("Balance", ascending=False).head(25),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No customers match the current filters and high-value disengagement rule.")

# Charts
left, right = st.columns(2)

with left:
    st.subheader("Engagement vs Churn")
    engagement_df = (
        filtered.groupby("EngagementStatus", as_index=False)["Exited"]
        .mean()
        .rename(columns={"Exited": "ChurnRate"})
    )
    engagement_df["ChurnRate"] *= 100
    fig = px.bar(
        engagement_df,
        x="EngagementStatus",
        y="ChurnRate",
        labels={"ChurnRate": "Churn Rate (%)", "EngagementStatus": "Customer Engagement"},
        title="Churn Rate by Customer Engagement"
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Product Utilization")
    product_df = (
        filtered.groupby("NumOfProducts", as_index=False)["Exited"]
        .mean()
        .rename(columns={"Exited": "ChurnRate"})
    )
    product_df["ChurnRate"] *= 100
    fig = px.bar(
        product_df,
        x="NumOfProducts",
        y="ChurnRate",
        labels={"NumOfProducts": "Number of Products", "ChurnRate": "Churn Rate (%)"},
        title="Churn Rate by Number of Products"
    )
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Behavioral Segment Analysis")
    seg_df = (
        filtered.groupby("BehavioralSegment", as_index=False)["Exited"]
        .mean()
        .rename(columns={"Exited": "ChurnRate"})
    )
    seg_df["ChurnRate"] *= 100
    fig = px.bar(
        seg_df,
        x="BehavioralSegment",
        y="ChurnRate",
        labels={"BehavioralSegment": "Behavioral Segment", "ChurnRate": "Churn Rate (%)"},
        title="Churn Rate by Behavioral Segment"
    )
    fig.update_xaxes(tickangle=-25)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Geography Analysis")
    geo_df = (
        filtered.groupby("Geography", as_index=False)["Exited"]
        .mean()
        .rename(columns={"Exited": "ChurnRate"})
    )
    geo_df["ChurnRate"] *= 100
    fig = px.bar(
        geo_df,
        x="Geography",
        y="ChurnRate",
        labels={"ChurnRate": "Churn Rate (%)", "Geography": "Geography"},
        title="Churn Rate by Geography"
    )
    st.plotly_chart(fig, use_container_width=True)

# Engagement + product
st.subheader("Engagement and Product Utilization")
combo = (
    filtered.groupby(["EngagementStatus", "NumOfProducts"], as_index=False)["Exited"]
    .mean()
    .rename(columns={"Exited": "ChurnRate"})
)
combo["ChurnRate"] *= 100
fig = px.bar(
    combo,
    x="NumOfProducts",
    y="ChurnRate",
    color="EngagementStatus",
    barmode="group",
    labels={"ChurnRate": "Churn Rate (%)", "NumOfProducts": "Number of Products"},
    title="Churn Rate by Engagement and Product Count"
)
st.plotly_chart(fig, use_container_width=True)

# Retention strength
st.subheader("Retention Strength Summary")
seg_summary = (
    filtered.groupby("BehavioralSegment")
    .agg(Customers=("CustomerId", "count"), ChurnRate=("Exited", "mean"))
    .reset_index()
)
seg_summary["ChurnRate"] *= 100
st.dataframe(seg_summary.sort_values("ChurnRate"), use_container_width=True, hide_index=True)

st.caption(
    "Note: This dashboard is an analytical project tool. Churn relationships shown here are descriptive "
    "and do not by themselves establish causation."
)
