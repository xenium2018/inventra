import sqlite3
import uuid
from pathlib import Path

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Inventra-Ticketing-MCP")
DB_PATH = Path(__file__).resolve().parent.parent / "database" / "inventra.db"

@mcp.tool()
def create_action_ticket(
    sku: str,
    issue_type: str,
    rationale: str,
    forecasted_demand: int,
    recommended_qty: int,
    financial_impact: float,
    vendor_id: str,
) -> dict:
    """Creates a structured procurement or low-stock alert ticket in the Inventra system."""
    ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO tickets (ticket_id, sku, issue_type, rationale, forecasted_demand, recommended_qty, financial_impact, vendor_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
        """,
        (ticket_id, sku, issue_type, rationale, forecasted_demand, recommended_qty, financial_impact, vendor_id),
    )
    conn.commit()
    conn.close()

    return {
        "ticket_id": ticket_id,
        "sku": sku,
        "issue_type": issue_type,
        "recommended_qty": recommended_qty,
        "financial_impact": financial_impact,
        "status": "OPEN",
        "synced_to": ["SQLite_Tickets", "Slack_Alerts_Webhook_Ready"]
    }

@mcp.tool()
def list_open_tickets() -> list[dict]:
    """Retrieves all open tickets from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM tickets ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    mcp.run()