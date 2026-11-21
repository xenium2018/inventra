import json
import logging
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.state import InventraState, OptimizationPlan, RouteDecision
from database.setup_db import get_db_connection
from database.vector_store import get_climate_advisory_retriever
from mcp_server.ticket_server import create_action_ticket
from mcp_server.tools import (
    get_financial_summary,
    get_inventory_status,
    get_low_stock_items,
    get_sales_summary,
    get_top_vendors,
    get_weather_forecast,
    in_region,
    inventory,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("inventra.orchestrator")


def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY is missing in your .env file.")
    return ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.15)


# --- 0. Supervisor Orchestrator Node ---
def supervisor_orchestrator_node(state: InventraState) -> dict:
    logger.info("Supervisor evaluating query: %s", state["user_query"])
    router_llm = get_llm().with_structured_output(RouteDecision)
    decision: RouteDecision = router_llm.invoke(
        f"""
        You are the Supervisor Orchestrator for Inventra.
        Decide the optimal multi-agent execution path for this user query:
        Query: "{state['user_query']}"

        - Choose 'full_forecast_pipeline' if the user asks about forecasts, weather impacts, demand surges, budget optimization, or raising reorder tickets.
        - Choose 'quick_data_lookup' if the user only asks to inspect existing inventory, past sales, finances, or top vendors without weather forecasting or ticket creation.
        """
    )
    logger.info("Supervisor selected route: %s (%s)", decision.route, decision.reasoning)
    return {"route": decision.route, "route_reasoning": decision.reasoning}


# --- 1. Data Understanding Agent ---
def data_understanding_node(state: InventraState) -> dict:
    reg = state.get("region", "").strip()
    tool_region = "" if reg.lower() == "all" else reg

    inv_status = get_inventory_status.invoke({"region": tool_region})
    sales_30d = get_sales_summary.invoke({"region": tool_region, "days": 30})
    fin_90d = get_financial_summary.invoke({"region": tool_region, "days": 90})
    low_stock = get_low_stock_items.invoke({"region": tool_region})
    top_vendors = get_top_vendors.invoke({})

    region_inv_df = in_region(inventory, tool_region).head(40)
    sku_records = region_inv_df.to_dict(orient="records")

    retriever = get_climate_advisory_retriever()
    advisories = retriever.invoke(state["user_query"])
    advisory_text = "\n".join([doc.page_content for doc in advisories])

    context = json.dumps(
        {
            "inventory_status_summary": inv_status,
            "sales_summary_30d": sales_30d,
            "financial_summary_90d": fin_90d,
            "low_stock_alert_report": low_stock,
            "top_vendors_report": top_vendors,
            "regional_sku_catalog": sku_records,
        },
        default=str,
        separators=(",", ":"),
    )
    return {"historical_context": context, "advisory_context": advisory_text}


# --- Fast-Path Lookup Node (When weather/tickets are skipped) ---
def quick_lookup_node(state: InventraState) -> dict:
    llm = get_llm()
    answer = llm.invoke(
        f"""
        Answer the user's operational query concisely using the verified tool outputs below.
        User Query: {state['user_query']}
        Tool Outputs: {state['historical_context']}
        """
    )

    # Gemini 3.x returns content as a list of blocks (e.g., thinking + text)
    if isinstance(answer.content, list):
        summary_text = "\n".join(
            block.get("text", "")
            for block in answer.content
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()
    else:
        summary_text = str(answer.content)

    plan = OptimizationPlan(
        executive_summary=summary_text or "No summary generated.",
        total_budget_required=0.0,
        recommendations=[],
    )
    weather_stub = {
        "region": state.get("region", "All").capitalize(),
        "forecast_summary": "Skipped (Quick Data Lookup route selected by Supervisor)",
        "anomaly_risk": "N/A",
    }

    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO audit_logs (user_query, region, weather_summary, agent_decisions) VALUES (?, ?, ?, ?)",
            (state["user_query"], state.get("region", "All"), json.dumps(weather_stub), json.dumps(plan.model_dump())),
        )

    return {
        "weather_report": weather_stub,
        "optimization_plan": plan.model_dump(),
        "created_tickets": [],
    }

# --- 2. Weather Forecasting Agent ---
def weather_forecast_node(state: InventraState) -> dict:
    reg = state.get("region", "south").strip().lower()
    if reg not in ["north", "south", "east", "west", "central"]:
        reg = "south"

    forecast_text = get_weather_forecast.invoke({"region": reg})
    risk = "HIGH" if any(w in forecast_text.lower() for w in ["heavy rain", "thunderstorm", "hot"]) else "MODERATE"

    return {
        "weather_report": {
            "region": reg.capitalize(),
            "source": "Inventra Weather Tool",
            "forecast_summary": forecast_text,
            "anomaly_risk": risk,
        }
    }


# --- 3. Decision & Optimization Agent ---
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=20), reraise=True)
def _invoke_gemini_optimizer(prompt: str) -> OptimizationPlan:
    llm = get_llm().with_structured_output(OptimizationPlan)
    return llm.invoke(prompt)


def decision_optimization_node(state: InventraState) -> dict:
    prompt = f"""
    You are the Decision & Optimization Agent for Inventra.
    Use the tool outputs, regional SKU catalog, weather forecast, and policy advisories to generate an action plan.

    User Query: {state['user_query']}
    Weather Forecast: {json.dumps(state['weather_report'])}
    Policy Advisories: {state['advisory_context']}
    Tool & Inventory Data: {state['historical_context']}

    Rules:
    - Focus on SKUs in the regional_sku_catalog impacted by the weather or already at/below reorder_threshold.
    - Map product_name from the 'name' column and use exact 'sku' and 'vendor_id' values from the catalog.
    - Calculate financial_impact using unit cost/price if available in the catalog, or a realistic estimate.
    - Set requires_ticket=True for items needing immediate reorder.
    """
    plan = _invoke_gemini_optimizer(prompt)
    return {"optimization_plan": plan.model_dump()}


# --- 4. MCP Ticket Generation & Audit Logging ---
def mcp_ticketing_node(state: InventraState) -> dict:
    plan = state["optimization_plan"]
    tickets = []

    for rec in plan.get("recommendations", []):
        if rec.get("requires_ticket") and rec.get("recommended_reorder_qty", 0) > 0:
            ticket = create_action_ticket(
                sku=rec["sku"],
                issue_type="WEATHER_SURGE_REORDER",
                rationale=rec["risk_rationale"],
                forecasted_demand=rec["forecasted_demand"],
                recommended_qty=rec["recommended_reorder_qty"],
                financial_impact=rec["financial_impact"],
                vendor_id=rec["vendor_id"],
            )
            tickets.append(ticket)

    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO audit_logs (user_query, region, weather_summary, agent_decisions) VALUES (?, ?, ?, ?)",
            (
                state["user_query"],
                state.get("region", "All"),
                json.dumps(state["weather_report"]),
                json.dumps(plan),
            ),
        )

    return {"created_tickets": tickets}


# --- Conditional Router Function ---
def route_after_data(state: InventraState) -> str:
    if state.get("route") == "quick_data_lookup":
        return "quick_lookup_agent"
    return "weather_agent"


def build_inventra_graph():
    workflow = StateGraph(InventraState)

    # Nodes
    workflow.add_node("supervisor", supervisor_orchestrator_node)
    workflow.add_node("data_agent", data_understanding_node)
    workflow.add_node("quick_lookup_agent", quick_lookup_node)
    workflow.add_node("weather_agent", weather_forecast_node)
    workflow.add_node("decision_agent", decision_optimization_node)
    workflow.add_node("mcp_ticket_agent", mcp_ticketing_node)

    # Edges & Conditional Routing
    workflow.set_entry_point("supervisor")
    workflow.add_edge("supervisor", "data_agent")
    workflow.add_conditional_edges(
        "data_agent",
        route_after_data,
        {
            "quick_lookup_agent": "quick_lookup_agent",
            "weather_agent": "weather_agent",
        },
    )
    workflow.add_edge("quick_lookup_agent", END)
    workflow.add_edge("weather_agent", "decision_agent")
    workflow.add_edge("decision_agent", "mcp_ticket_agent")
    workflow.add_edge("mcp_ticket_agent", END)

    return workflow.compile()
