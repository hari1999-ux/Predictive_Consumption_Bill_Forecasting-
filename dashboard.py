import streamlit as st
import pandas as pd
import sqlite3
import requests
import calendar

# ==================================================
# 1. PAGE CONFIGURATION & POP-UP DIALOG
# ==================================================
st.set_page_config(page_title="Live Utility AI Dashboard", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# The Pop-up Dialog for Customer Details
@st.dialog("👤 Customer Profile & Consumption", width="large")
def show_customer_popup(customer_id, db_df, ai_df=None):
    # Fetch historical data
    cust_db = db_df[db_df["Customer id"] == customer_id]
    if cust_db.empty:
        st.error("Customer record not found.")
        return

    info = cust_db.iloc[0]
    st.markdown(f"## {info['Customer name']}")
    
    # Customer Metadata Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Customer ID", customer_id)
    c2.metric("Account Number", info['customer acct'])
    c3.metric("Site ID", info['sit id'])
    c4.metric("Meter Type", "Gas (GA)" if info['meter type'] == 'GA' else "Electric (EL)")

    st.divider()
    
    # Historical Consumption Visualization
    st.subheader("📊 12-Month Historical Consumption")
    chart_data = cust_db[['Month', 'Usage value']].set_index('Month')
    st.bar_chart(chart_data, color="#F5A623")

    # If AI Forecast data is available, show the next month prediction
    if ai_df is not None and not ai_df.empty:
        cust_ai = ai_df[ai_df["Customer id"] == customer_id]
        if not cust_ai.empty:
            st.divider()
            st.subheader("🤖 AI Prediction (Next Month)")
            ai_info = cust_ai.iloc[0]
            a1, a2 = st.columns(2)
            a1.metric("Predicted Usage", f"{ai_info['Next Month Usage']:,.2f} units")
            a2.metric("Predicted Bill", f"${ai_info['Next Month Bill']:,.2f}")

# ==================================================
# 2. CUSTOM UI / CSS
# ==================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, rgba(8, 15, 30, 0.96), rgba(14, 28, 48, 0.94)),
                url("https://images.unsplash.com/photo-1541888047970-17e923ce75d9?q=80&w=2000&auto=format&fit=crop");
    background-size: cover; background-position: center; background-attachment: fixed; color: #EAF1FA;
}
.block-container { max-width: 1600px; padding: 2rem 2.5rem 3rem 2.5rem; }
h1, h2, h3, h4, p, label, [data-testid="stMarkdownContainer"] { color: #F5F8FF !important; }
.hero-panel {
    background: linear-gradient(120deg, rgba(24, 48, 78, 0.98), rgba(18, 34, 58, 0.98));
    border: 1px solid rgba(119, 177, 255, 0.25); border-radius: 18px; padding: 28px 30px; margin-bottom: 24px;
}
.hero-label { color: #7DD3FC !important; font-size: 0.78rem; font-weight: 750; letter-spacing: 2px; margin-bottom: 8px; }
.hero-title { color: #FFFFFF !important; font-size: 2rem; font-weight: 800; line-height: 1.3; margin-bottom: 8px; }
.stTabs [data-baseweb="tab"] { background: rgba(23, 37, 59, 0.85); border-radius: 10px 10px 0 0; padding: 12px 18px; font-weight: 650; }
.stTabs [aria-selected="true"] { background: #1D4265 !important; border-bottom: 3px solid #38BDF8 !important; }
[data-testid="stMetric"] { background: rgba(26, 46, 72, 0.98); border: 1px solid rgba(148, 180, 215, 0.24); border-radius: 14px; padding: 20px; }
[data-testid="stDataFrame"] { border: 1px solid #425873; border-radius: 10px; }
hr { border-color: rgba(148, 163, 184, 0.25) !important; margin: 1.4rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 3. DATABASE LOADING
# ==================================================
st.markdown("""
<div class="hero-panel">
    <div class="hero-label">UTILITY INTELLIGENCE PLATFORM</div>
    <div class="hero-title">⚡ Live Utility Dashboard</div>
    <div>Monitor billing, click rows for customer details, and dynamically forecast out to 2035.</div>
</div>
""", unsafe_allow_html=True)

def load_db_data():
    conn = sqlite3.connect("utility_data.db")
    data = pd.read_sql("SELECT * FROM customer_billing", conn)
    conn.close()
    return data

df = load_db_data()
gas_df_full = df[df["meter type"] == "GA"]
elec_df_full = df[df["meter type"] == "EL"]

tab1, tab2, tab3 = st.tabs(["🗃️ Live Database", "📈 Company Totals", "🤖 AI Long-Term Forecast"])

# ==================================================
# TAB 1: LIVE DATABASE
# ==================================================
with tab1:
    st.header("🗃️ Live Database Records")
    st.write("👉 **Click on any row** in the tables below to view the customer's profile and consumption chart.")
    
    if st.button("🔄 Refresh Data", use_container_width=False): 
        st.rerun()
    st.divider()

    month_map = {i: calendar.month_name[i] for i in range(1, 13)}
    month_options = ["All Months"] + list(month_map.values())
    selected_month = st.selectbox("📅 Filter records by billing month", options=month_options)

    filtered_df = df.copy()
    if selected_month != "All Months":
        month_num = list(month_map.keys())[list(month_map.values()).index(selected_month)]
        filtered_df = filtered_df[filtered_df["Month"] == month_num]

    # GAS TABLE
    st.subheader("🔥 Gas Customers")
    gas_view = filtered_df[filtered_df["meter type"] == "GA"].reset_index(drop=True)
    gas_event = st.dataframe(gas_view, use_container_width=True, hide_index=True, height=350, on_select="rerun", selection_mode="single-row", key="db_gas")
    if gas_event.selection.rows:
        selected_cid = gas_view.iloc[gas_event.selection.rows[0]]["Customer id"]
        show_customer_popup(selected_cid, df)
    
    # ELECTRIC TABLE
    st.subheader("⚡ Electric Customers")
    elec_view = filtered_df[filtered_df["meter type"] == "EL"].reset_index(drop=True)
    elec_event = st.dataframe(elec_view, use_container_width=True, hide_index=True, height=350, on_select="rerun", selection_mode="single-row", key="db_elec")
    if elec_event.selection.rows:
        selected_cid = elec_view.iloc[elec_event.selection.rows[0]]["Customer id"]
        show_customer_popup(selected_cid, df)

# ==================================================
# TAB 2: COMPANY TOTALS
# ==================================================
with tab2:
    st.header("📈 Historical Company Totals")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Historical Revenue", f"${df['bill amount'].sum():,.2f}")
    c2.metric("🔥 Total Gas Revenue", f"${gas_df_full['bill amount'].sum():,.2f}")
    c3.metric("⚡ Total Electric Revenue", f"${elec_df_full['bill amount'].sum():,.2f}")
    st.divider()
    monthly_trend = (df.pivot_table(index="Month", columns="meter type", values="bill amount", aggfunc="sum")
        .reindex(columns=["GA", "EL"], fill_value=0).fillna(0).rename(columns={"GA": "Gas Revenue", "EL": "Electric Revenue"}))
    st.line_chart(monthly_trend, use_container_width=True)

# ==================================================
# TAB 3: AI LONG-TERM FORECAST
# ==================================================
with tab3:
    st.header("🤖 AI Multi-Year Forecast")

    if "forecast_data" not in st.session_state:
        st.session_state["forecast_data"] = None

    if st.button("🚀 Generate Real-Time Forecast", type="primary", use_container_width=True):
        with st.spinner("Analyzing data and calculating predictions out to 2035..."):
            try:
                response = requests.get("http://127.0.0.1:8000/predict", timeout=120)
                response.raise_for_status()
                st.session_state["forecast_data"] = response.json()
            except Exception as e:
                st.error(f"Error generating forecast: {e}")

    if st.session_state["forecast_data"] is not None:
        predictions_df = pd.DataFrame(st.session_state["forecast_data"])
        
        # High Usage Logic
        def flag_high_usage(bill):
            if bill > 200.0: return "🔴 HIGH USAGE"
            elif bill > 150.0: return "🟡 ELEVATED"
            return "🟢 NORMAL"
        predictions_df["Usage Status"] = predictions_df["Next Month Bill"].apply(flag_high_usage)

        # Dropdown includes "Next Month" + Years
        st.markdown("### 📅 Select Forecast Period")
        period_options = ["Next Month"] + [str(y) for y in range(2026, 2036)]
        selected_period = st.selectbox("Select time horizon to view:", options=period_options)
        
        # Determine column keys based on dropdown selection
        usg_col = f"{selected_period} Usage"
        bill_col = f"{selected_period} Bill"

        st.divider()
        
        # Dynamic KPIs
        st.subheader(f"🏢 Total Company Prediction ({selected_period})")
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Total Revenue ({selected_period})", f"${predictions_df[bill_col].sum():,.2f}")
        gas_preds = predictions_df[predictions_df["Meter Type"] == "GA"]
        elec_preds = predictions_df[predictions_df["Meter Type"] == "EL"]
        m2.metric(f"Gas Revenue", f"${gas_preds[bill_col].sum():,.2f}")
        m3.metric(f"Electric Revenue", f"${elec_preds[bill_col].sum():,.2f}")
        
        st.divider()

        # Detailed Tables with Usage Status Filtering
        st.subheader(f"📊 Detailed Forecast ({selected_period})")
        st.write("👉 **Click any row** to view the customer's historical vs predicted details.")
        
        # Usage Status Filters
        f1, f2, f3 = st.columns(3)
        with f1: normal_check = st.checkbox("🟢 NORMAL", value=True, key="status_normal")
        with f2: elevated_check = st.checkbox("🟡 ELEVATED", value=True, key="status_elevated")
        with f3: high_check = st.checkbox("🔴 HIGH USAGE", value=True, key="status_high")

        allowed_statuses = []
        if normal_check: allowed_statuses.append("🟢 NORMAL")
        if elevated_check: allowed_statuses.append("🟡 ELEVATED")
        if high_check: allowed_statuses.append("🔴 HIGH USAGE")

        # Apply Filters
        gas_preds_filtered = gas_preds[gas_preds["Usage Status"].isin(allowed_statuses)]
        elec_preds_filtered = elec_preds[elec_preds["Usage Status"].isin(allowed_statuses)]

        cols_to_show = ["Customer id", "Customer name", "Meter Type", "Usage Status", usg_col, bill_col]
        numeric_formats = {usg_col: "{:,.2f}", bill_col: "${:,.2f}"}

        # GAS FORECAST TABLE
        with st.expander(f"🔥 Gas Customers ({len(gas_preds_filtered)})", expanded=True):
            if not gas_preds_filtered.empty:
                gas_ai_view = gas_preds_filtered[cols_to_show].reset_index(drop=True)
                gas_ai_event = st.dataframe(gas_ai_view.style.format(numeric_formats), use_container_width=True, hide_index=True, height=350, on_select="rerun", selection_mode="single-row", key="ai_gas")
                if gas_ai_event.selection.rows:
                    selected_cid = gas_ai_view.iloc[gas_ai_event.selection.rows[0]]["Customer id"]
                    show_customer_popup(selected_cid, df, predictions_df)
            else:
                st.info("No Gas customers match the selected usage status.")

        # ELECTRIC FORECAST TABLE
        with st.expander(f"⚡ Electric Customers ({len(elec_preds_filtered)})", expanded=True):
            if not elec_preds_filtered.empty:
                elec_ai_view = elec_preds_filtered[cols_to_show].reset_index(drop=True)
                elec_ai_event = st.dataframe(elec_ai_view.style.format(numeric_formats), use_container_width=True, hide_index=True, height=350, on_select="rerun", selection_mode="single-row", key="ai_elec")
                if elec_ai_event.selection.rows:
                    selected_cid = elec_ai_view.iloc[elec_ai_event.selection.rows[0]]["Customer id"]
                    show_customer_popup(selected_cid, df, predictions_df)
            else:
                st.info("No Electric customers match the selected usage status.")