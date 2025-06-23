import streamlit as st
import pandas as pd
import plotly.express as px

# App configuration
st.set_page_config(page_title="📊 SANC-I Health Dashboard", layout="wide")
st.title("📊 SANC-I: AI-Powered National Health Data Dashboard")

# Load and clean data
@st.cache_data
def load_data():
    df = pd.read_csv("sanci_health_data.csv", on_bad_lines="skip")
    # Clean column names: remove quotes and extra spaces
    df.columns = (
        df.columns.str.replace('"', '')
        .str.strip()
        .str.replace("Difference-", "Δ ")
        .str.replace("Total ", "")
    )
    return df

df = load_data()
df = df[df["Type"] == "TOTAL"]  # Filter only TOTAL values

# Sidebar filters
st.sidebar.header("🔍 Filter")
selected_indicator = st.sidebar.selectbox(
    "Select Indicator", sorted(df["Indicators"].unique())
)
filtered_df = df[df["Indicators"] == selected_indicator]

selected_param = st.sidebar.selectbox(
    "Select Parameter", sorted(filtered_df["Parameters"].unique())
)
final_df = filtered_df[filtered_df["Parameters"] == selected_param]

# KPI Cards
st.subheader(f"📌 KPI Summary: {selected_param}")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📅 2011–12", value=int(final_df["2011-2012"].values[0]))
with col2:
    st.metric("📅 2012–13", value=int(final_df["2012-2013"].values[0]))
with col3:
    delta = int(final_df["2012-2013"].values[0]) - int(final_df["2011-2012"].values[0])
    st.metric("📈 Yearly Difference", value=delta, delta=delta)

# Prepare monthly data
month_columns = [
    col
    for col in df.columns
    if any(
        month in col
        for month in [
            "April", "May", "June", "July", "August", "September",
            "October", "November", "December", "January", "February", "March"
        ]
    ) and "Δ" not in col
]

month_11_12 = [col for col in month_columns if "11-12" in col]
month_12_13 = [col for col in month_columns if "12-13" in col]

df_11 = final_df.melt(
    id_vars=["Indicators", "Parameters"],
    value_vars=month_11_12,
    var_name="Month",
    value_name="Value",
)
df_11["Year"] = "2011–12"

df_12 = final_df.melt(
    id_vars=["Indicators", "Parameters"],
    value_vars=month_12_13,
    var_name="Month",
    value_name="Value",
)
df_12["Year"] = "2012–13"

combined = pd.concat([df_11, df_12])

# Clean month labels
combined["Month"] = combined["Month"].str.extract(r"(\w+)", expand=False)
month_order = [
    "April", "May", "June", "July", "August", "September",
    "October", "November", "December", "January", "February", "March"
]
combined["Month"] = pd.Categorical(combined["Month"], categories=month_order, ordered=True)
combined = combined.sort_values("Month")

# Chart selection
chart_type = st.selectbox("📊 Choose Chart Type", ["Line", "Bar"])
st.subheader("📈 Monthly Trend Comparison")

if chart_type == "Line":
    fig = px.line(
        combined,
        x="Month",
        y="Value",
        color="Year",
        markers=True,
        title=f"{selected_param} – Monthly Comparison",
    )
else:
    fig = px.bar(
        combined,
        x="Month",
        y="Value",
        color="Year",
        barmode="group",
        title=f"{selected_param} – Monthly Comparison",
    )

fig.update_layout(xaxis_title="Month", yaxis_title="Value", legend_title="Year")
st.plotly_chart(fig, use_container_width=True)

# CSV Download
csv_download = final_df.T.reset_index()
csv_download.columns = ["Field", "Value"]
csv_download["Value"] = csv_download["Value"].astype(str)  # Fix ArrowTypeError

st.download_button(
    label="⬇️ Download Filtered Data",
    data=csv_download.to_csv(index=False).encode("utf-8"),
    file_name=f"{selected_param.replace(' ', '_')}_summary.csv",
    mime="text/csv",
)

# Show raw data
st.subheader("📋 Raw Data (Transposed)")
st.dataframe(csv_download, use_container_width=True)
