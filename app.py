import json

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from agents.graph import build_inventra_graph
from database.setup_db import get_db_connection, init_db, update_ticket_status
from ui_theme import (
    render_header,
    render_kpis,
    render_langgraph_diagram,
    render_pipeline,
    render_sku_card,
)

load_dotenv()
init_db()

st.set_page_config(page_title="INVENTRA | Supply & Finance OS", page_icon="⚡", layout="wide")
render_header()

@st.cache_resource
def get_compiled_graph():
    return build_inventra_graph()

# --- Sidebar Control Center ---
with st.sidebar:
    st.subheader("⚡ INVENTRA CONTROL")
    region = st.selectbox("📍 Target Region", ["south", "north", "east", "west", "central"])
    horizon = st.selectbox("🗓️ Forecast Horizon", ["Next 5 Days", "Next 30 Days", "Next 90 Days"])

    st.markdown("#### 🎯 Quick Scenarios")
    p_rain = st.button("🌧️ Heavy Rainfall Surge (South)", use_container_width=True)
    p_heat = st.button("☀️ Hot & Dry Spike (West)", use_container_width=True)
    p_low = st.button("🚨 Low-Stock & Vendor Audit", use_container_width=True)

    st.divider()
    if st.button("🔄 Sync CSVs from /data", use_container_width=True):
        init_db(force_reload_csv=True)
        st.toast("Reloaded CSVs into SQLite!", icon="✅")

# --- Load Live SQLite Data ---
with get_db_connection() as conn:
    inv_df = pd.read_sql("SELECT * FROM inventory", conn)
    fin_df = pd.read_sql("SELECT * FROM finance", conn)
    sales_df = pd.read_sql("SELECT * FROM sales_history", conn)
    tkt_df = pd.read_sql("SELECT * FROM tickets ORDER BY created_at DESC", conn)
    audit_df = pd.read_sql("SELECT * FROM audit_logs ORDER BY created_at DESC", conn)

open_tkts = int((tkt_df["status"] == "OPEN").sum()) if not tkt_df.empty else 0
exposure = float(tkt_df.loc[tkt_df["status"] == "OPEN", "financial_impact"].sum()) if not tkt_df.empty else 0.0
render_kpis(len(inv_df), open_tkts, exposure, len(audit_df))

# --- Main Workspace Tabs ---
tab_copilot, tab_tickets, tab_analytics, tab_data = st.tabs([
    "🤖 AI Command Copilot",
    "🎫 MCP Ticket Workbench",
    "📊 Portfolio Analytics",
    "🗄️ Data & Audit",
])

with tab_copilot:
    render_pipeline("last_result" in st.session_state)
    with st.expander("🔍 View Live LangGraph Workflow Topology", expanded=False):
        render_langgraph_diagram(get_compiled_graph())

    active_region = region
    preset = ""
    if p_rain:
        active_region = "south"
        preset = "Forecast inventory for the south region given heavy rain expected, check low-stock items, and raise MCP reorder tickets."
    elif p_heat:
        active_region = "west"
        preset = "Forecast inventory for the west region under hot and dry weather, show budget impact, and raise tickets for stockout risks."
    elif p_low:
        preset = f"Audit low-stock items in the {region} region, select the best vendors by quality and lead time, and raise reorder tickets."

    with st.form("copilot_form"):
        query = st.text_area(
            "Command Prompt",
            value=preset,
            height=80,
            placeholder="e.g., Raise tickets for items likely to run low due to upcoming rainfall in south...",
        )
        c_run, c_hint = st.columns([1, 2.5])
        submitted = c_run.form_submit_button("⚡ Execute Agents", type="primary", use_container_width=True)
        c_hint.caption(f"Target Region: **{active_region.upper()}** | Horizon: **{horizon}**")

    if submitted and query.strip():
        try:
            with st.status("Running Cooperative Multi-Agent Graph...", expanded=True) as status:
                res = get_compiled_graph().invoke({"user_query": f"[{horizon}] {query.strip()}", "region": active_region})
                st.session_state["last_result"] = res
                status.update(label="Multi-Agent Execution Complete", state="complete", expanded=False)
                st.rerun()
        except Exception as e:
            st.error(f"Pipeline Error: {e}")

    if "last_result" in st.session_state:
        res = st.session_state["last_result"]
        w = res["weather_report"]
        plan = res["optimization_plan"]
        rec_df = pd.DataFrame(plan["recommendations"])

        st.divider()
        left_col, right_col = st.columns([1.15, 1])

        with left_col:
            st.subheader("🧠 Executive Summary & Weather Telemetry")
            st.caption(f"🧭 **Supervisor Route:** `{res.get('route', 'full_forecast_pipeline')}` — {res.get('route_reasoning', '')}")
            st.info(plan["executive_summary"])
            st.warning(f"🌤️ **Weather Forecast ({w.get('region', active_region)}):** {w.get('forecast_summary', 'N/A')} | **Risk:** {w.get('anomaly_risk', 'MODERATE')}")

            if not rec_df.empty:
                fig = px.bar(
                    rec_df,
                    x="product_name",
                    y=["forecasted_demand", "recommended_reorder_qty"],
                    barmode="group",
                    title="Forecasted Demand vs. Recommended Reorder Qty",
                    color_discrete_sequence=["#2563eb", "#10b981"],
                    template="plotly_white",
                )
                fig.update_layout(height=330, legend_title_text="")
                st.plotly_chart(fig, use_container_width=True)

        with right_col:
            st.subheader(f"🎯 SKU Action Matrix (₹{plan['total_budget_required']:,.2f})")
            for rec in plan["recommendations"]:
                render_sku_card(rec)

        ex1, ex2, ex3 = st.columns(3)
        ex1.download_button("⬇️ Export CSV", rec_df.to_csv(index=False), "inventra_plan.csv", "text/csv", use_container_width=True)
        ex2.download_button("⬇️ Export JSON", json.dumps(plan, indent=2), "inventra_audit.json", "application/json", use_container_width=True)
        if res["created_tickets"]:
            tkt_ids = ", ".join([t["ticket_id"] for t in res["created_tickets"]])
            ex3.success(f"🎫 MCP Tickets: {tkt_ids}")

with tab_tickets:
    st.subheader("🎫 MCP Action Ticket Workflow")
    if tkt_df.empty:
        st.info("No MCP tickets in queue yet.")
    else:
        cf, ca1, ca2, ca3 = st.columns([1.2, 1, 1, 0.8])
        status_filter = cf.selectbox("Filter", ["ALL", "OPEN", "APPROVED", "DISPATCHED", "CLOSED"])
        selected_tkt = ca1.selectbox("Ticket ID", tkt_df["ticket_id"].tolist())
        new_status = ca2.selectbox("New Status", ["APPROVED", "DISPATCHED", "CLOSED", "OPEN"])
        ca3.write("")
        ca3.write("")
        if ca3.button("Update", type="primary", use_container_width=True):
            update_ticket_status(selected_tkt, new_status)
            st.toast(f"{selected_tkt} → {new_status}", icon="✅")
            st.rerun()

        view_df = tkt_df if status_filter == "ALL" else tkt_df[tkt_df["status"] == status_filter]
        st.dataframe(view_df, use_container_width=True)

with tab_analytics:
    st.subheader("📊 Inventory & Threshold Overview")
    if not inv_df.empty and "qty" in inv_df.columns and "reorder_threshold" in inv_df.columns:
        label_col = "name" if "name" in inv_df.columns else inv_df.columns
        fig_inv = px.bar(
            inv_df,
            x=label_col,
            y=["qty", "reorder_threshold"],
            barmode="group",
            color="region" if "region" in inv_df.columns else None,
            title="Current Stock (qty) vs. Reorder Threshold across Regions",
            template="plotly_white",
        )
        st.plotly_chart(fig_inv, use_container_width=True)
    st.dataframe(inv_df, use_container_width=True)

with tab_data:
    d1, d2, d3 = st.tabs(["📦 Inventory & Finance", "📈 Historical Sales", "📜 Audit Trail"])
    with d1:
        st.markdown("##### Inventory Master")
        st.dataframe(inv_df, use_container_width=True)
        st.markdown("##### Financial Ledger")
        st.dataframe(fin_df, use_container_width=True)
    with d2:
        st.markdown("##### Historical Sales (Top 100)")
        st.dataframe(sales_df.head(100), use_container_width=True)
    with d3:
        st.markdown("##### Persistent Audit Logs")
        st.dataframe(audit_df, use_container_width=True)
