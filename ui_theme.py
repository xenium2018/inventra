import streamlit as st

def render_header():
    st.markdown("""
    <style>
    @import url('https://googleapis.com');

    [data-testid="stAppViewContainer"], .stApp {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stHeader"] {
        background-color: rgba(241, 245, 249, 0.9) !important;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #cbd5e1;
    }
    [data-testid="stSidebar"] * {
        color: #0f172a !important;
    }
    h1, h2, h3, h4, p, label, span, div {
        color: #0f172a;
    }
    .block-container {
        padding-top: 1.25rem;
        max-width: 1440px;
    }

    /* Executive Hero Header */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 65%, #065f46 100%);
        border-radius: 14px;
        padding: 1.35rem 1.75rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.15);
    }
    .top-nav h2 { color: #ffffff !important; margin: 0; font-size: 1.65rem; }
    .top-nav p { color: #cbd5e1 !important; margin: 4px 0 0 0; font-size: 0.9rem; }
    .top-nav .nav-status {
        background: rgba(255, 255, 255, 0.12);
        color: #6ee7b7 !important;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* High-Contrast KPI Cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-left: 5px solid #10b981;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
    }
    .kpi-lbl { font-size: 0.75rem; color: #475569 !important; font-weight: 700; letter-spacing: 0.04em; }
    .kpi-val { font-family: 'JetBrains Mono', monospace; font-size: 1.65rem; font-weight: 700; color: #0f172a !important; margin-top: 4px; }

    /* Agent Pipeline Cards */
    .agent-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 0.75rem 0 1.25rem 0; }
    .agent-box {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 0.9rem 1rem;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
    }
    .agent-box.done {
        border-color: #10b981;
        background: #ecfdf5;
    }
    .agent-box b { color: #0f172a !important; font-size: 0.9rem; }
    .agent-box small { color: #475569 !important; font-size: 0.8rem; }

    /* SKU Action Cards */
    .sku-box {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-left: 5px solid #10b981;
        border-radius: 10px;
        padding: 1rem 1.15rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
    }
    .sku-box.urgent {
        border-left-color: #dc2626;
        background: #fef2f2;
    }
    .sku-title { color: #0f172a !important; font-size: 0.98rem; font-weight: 700; }
    .sku-meta { color: #1e293b !important; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; margin: 6px 0; }
    .sku-desc { color: #334155 !important; font-size: 0.85rem; line-height: 1.45; }

    /* Tabs & Metrics */
    button[data-baseweb="tab"] { color: #475569 !important; font-weight: 600 !important; font-size: 0.95rem !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #059669 !important; border-bottom-color: #059669 !important; }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 12px 16px;
        border-radius: 10px;
    }
    #MainMenu, footer { visibility: hidden; }
    </style>
    <div class="top-nav">
        <div>
            <h2>⚡ INVENTRA OS</h2>
            <p>Autonomous Weather-Aware Supply Chain & Financial Optimization</p>
        </div>
        <div class="nav-status">● Gemini 3.8 Flash &nbsp;|&nbsp; ● FAISS Index &nbsp;|&nbsp; ● MCP Active</div>
    </div>
    """, unsafe_allow_html=True)

def render_kpis(sku_count, open_tkts, exposure, audit_count):
    cols = st.columns(4)
    items = [
        ("TRACKED SKUS", str(sku_count), "#10b981"),
        ("OPEN MCP TICKETS", str(open_tkts), "#f59e0b"),
        ("REORDER EXPOSURE", f"₹{exposure:,.0f}", "#2563eb"),
        ("AUDIT DECISIONS", str(audit_count), "#7c3aed"),
    ]
    for col, (label, val, color) in zip(cols, items):
        col.markdown(
            f'<div class="kpi-card" style="border-left-color:{color};">'
            f'<div class="kpi-lbl">{label}</div>'
            f'<div class="kpi-val">{val}</div></div>',
            unsafe_allow_html=True,
        )

def render_pipeline(done: bool):
    cls = "agent-box done" if done else "agent-box"
    badge_color = "#059669" if done else "#64748b"
    tag = "COMPLETED" if done else "READY"
    st.markdown(f"""
    <div class="agent-grid">
        <div class="{cls}"><b>01. Data Agent</b> <span style="color:{badge_color};font-size:0.72rem;font-weight:700;">[{tag}]</span><br><small>SQLite + FAISS Rules</small></div>
        <div class="{cls}"><b>02. Weather Agent</b> <span style="color:{badge_color};font-size:0.72rem;font-weight:700;">[{tag}]</span><br><small>Risk & Anomaly Engine</small></div>
        <div class="{cls}"><b>03. Decision Agent</b> <span style="color:{badge_color};font-size:0.72rem;font-weight:700;">[{tag}]</span><br><small>Demand & Budget Plan</small></div>
        <div class="{cls}"><b>04. MCP Ticketing</b> <span style="color:{badge_color};font-size:0.72rem;font-weight:700;">[{tag}]</span><br><small>Auto-Routing & Audit</small></div>
    </div>
    """, unsafe_allow_html=True)

def render_sku_card(rec: dict):
    urgent = rec.get("requires_ticket") and rec.get("recommended_reorder_qty", 0) > 0
    cls = "sku-box urgent" if urgent else "sku-box"
    badge = '<span style="color:#dc2626;font-weight:700;font-size:0.78rem;">🚨 REORDER TICKET RAISED</span>' if urgent else '<span style="color:#059669;font-weight:700;font-size:0.78rem;">✅ STOCK SUFFICIENT</span>'
    st.markdown(
        f'<div class="{cls}">'
        f'<div class="sku-title">{rec["product_name"]} ({rec["sku"]}) — {badge}</div>'
        f'<div class="sku-meta">Forecast: <b>{rec["forecasted_demand"]}</b> | Order: <b>{rec["recommended_reorder_qty"]}</b> | Cost: <b>₹{rec["financial_impact"]:,.0f}</b> | Vendor: <b>{rec["vendor_id"]}</b></div>'
        f'<div class="sku-desc">{rec["risk_rationale"]}</div></div>',
        unsafe_allow_html=True,
    )
