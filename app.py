from pathlib import Path

# Streamlit UI framework
import streamlit as st

# Data handling
import pandas as pd

# Plotting
import plotly.express as px

# Page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="MT5 EA Analytics Dashboard",
    layout="wide"
)

st.title("MT5 Expert Advisor — Performance Analytics")

st.markdown("""
This dashboard provides a structured analysis of **executed trades** from an MT5 Expert Advisor.
It focuses on:
- Realized profitability
- Trade frequency
- Per-instrument performance
- Equity evolution over time
""")

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "processed" / "exits_processed.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["Time"])
    return df

exits_df = load_data()

if exits_df.empty:
    st.error("No data loaded. Please check the CSV path.")
    st.stop()

REQUIRED_COLUMNS = {
    "Time", "Symbol", "Type", "Profit", "Volume", "Equity", "Date"
}

missing = REQUIRED_COLUMNS - set(exits_df.columns)
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

st.subheader("Data Snapshot")
st.dataframe(exits_df.head())

# Computing KPIs
total_profit = exits_df["Profit"].sum()
total_trades = len(exits_df)
win_rate = (exits_df["Profit"] > 0).mean() * 100
avg_trade = exits_df["Profit"].mean()

# Displaying with Streamlit Metrics
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Profit", f"{total_profit:,.2f}")
col2.metric("Trades", total_trades)
col3.metric("Win Rate", f"{win_rate:.1f}%")
col4.metric("Avg Trade", f"{avg_trade:.2f}")

# Build Portfolio Equity
portfolio_equity = (
    exits_df
    .sort_values("Time")
    .assign(PortfolioEquity=lambda df: df["Profit"].cumsum())
)

# Plot with Plotly
fig = px.line(
    portfolio_equity,
    x="Time",
    y="PortfolioEquity",
    title="Portfolio Equity Curve"
)

st.plotly_chart(fig, use_container_width=True)

# Compute profit by Symbol
symbol_profit = (
    exits_df
    .groupby("Symbol")["Profit"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

fig = px.bar(
    symbol_profit,
    x="Symbol",
    y="Profit",
    title="Profit by Instrument"
)

st.plotly_chart(fig, use_container_width=True)

########### Risk Metrics #########
# Max Drawdown
equity = portfolio_equity["PortfolioEquity"]
running_max = equity.cummax()
drawdown = equity - running_max
max_dd = drawdown.min()

st.metric("Max Drawdown", f"{max_dd:,.2f}")

########### Strategy Constraint Validation #########
# Daily profit target check (Per instrument)
daily_symbol_profit = (
    exits_df
    .groupby(["Date", "Symbol"])["Profit"]
    .sum()
    .reset_index()
)

fig = px.box(
    daily_symbol_profit,
    x="Symbol",
    y="Profit",
    title="Daily Profit Distribution per Instrument"
)

st.plotly_chart(fig, use_container_width=True)


