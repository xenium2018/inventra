"""Inventra's tools: simple Python functions over our sample data.

The @tool decorator turns each function into a tool an agent can call.
The function's docstring tells the agent what the tool does, so write it clearly.
"""

from pathlib import Path

import pandas as pd
from langchain_core.tools import tool

DATA = Path(__file__).resolve().parent.parent / "data"
TODAY = pd.Timestamp("2024-10-31")     # our sample data ends here, so we pretend today is 31 October 2024

inventory = pd.read_csv(DATA / "inventory.csv")
sales = pd.read_csv(DATA / "sales.csv", parse_dates=["date"])
finance = pd.read_csv(DATA / "finance.csv", parse_dates=["date"])
vendors = pd.read_csv(DATA / "vendors.csv")


def in_region(table, region):
    """Keep only the rows for one region (or all rows if no region is given)."""
    if region:
        return table[table["region"].str.lower() == region.lower()]
    return table


@tool
def get_inventory_status(region: str = "") -> str:
    """Get the stock levels: total products, total units, and how many are low on stock.
    region is north, south, east, west or central; leave it empty for all regions."""
    items = in_region(inventory, region)
    low = items[items["qty"] <= items["reorder_threshold"]]
    return (f"Products: {len(items)}, total units: {items['qty'].sum()}, "
            f"low on stock: {len(low)} {list(low['name'])}")


@tool
def get_sales_summary(region: str = "", days: int = 30) -> str:
    """Get sales for the last few days: units sold, revenue, and the top 3 products."""
    recent = in_region(sales, region)
    recent = recent[recent["date"] > TODAY - pd.Timedelta(days=days)]
    top = recent.groupby("sku")["qty"].sum().sort_values(ascending=False).head(3)
    names = []
    for sku in top.index:
        names.append(inventory[inventory["sku"] == sku]["name"].iloc[0])
    return f"Last {days} days: {recent['qty'].sum()} units sold, revenue Rs {recent['revenue'].sum():,.0f}, top products: {names}"


@tool
def get_financial_summary(region: str = "", days: int = 90) -> str:
    """Get money in (sales) and money out (purchases) for the last few days, and the profit."""
    recent = in_region(finance, region)
    recent = recent[recent["date"] > TODAY - pd.Timedelta(days=days)]
    income = recent[recent["type"] == "sale"]["amount"].sum()
    spending = recent[recent["type"] == "purchase"]["amount"].sum()
    return f"Last {days} days: sales Rs {income:,.0f}, purchases Rs {spending:,.0f}, profit Rs {income - spending:,.0f}"


@tool
def get_low_stock_items(region: str = "") -> str:
    """List products at or below their reorder threshold, with a suggested reorder quantity and their vendor."""
    items = in_region(inventory, region)
    low = items[items["qty"] <= items["reorder_threshold"]]
    lines = []
    for _, item in low.iterrows():
        vendor = vendors[vendors["vendor_id"] == item["vendor_id"]].iloc[0]
        reorder = item["reorder_threshold"] * 2 - item["qty"]
        lines.append(f"{item['name']} ({item['region']}): {item['qty']} left, threshold {item['reorder_threshold']}, "
                     f"reorder {reorder} from {vendor['name']} ({vendor['lead_time_days']} days)")
    if len(lines) == 0:
        return "No products are low on stock."
    return "\n".join(lines)


@tool
def get_top_vendors() -> str:
    """List the 5 best vendors by quality score, with their lead time and reliability."""
    best = vendors.sort_values("quality_score", ascending=False).head(5)
    lines = []
    for _, vendor in best.iterrows():
        lines.append(f"{vendor['name']}: quality {vendor['quality_score']}/5, lead time {vendor['lead_time_days']} days, "
                     f"reliability {vendor['reliability_rating']}")
    return "\n".join(lines)


# Sample weather for the next 5 days (simulated, so no weather API key is needed today)
SAMPLE_WEATHER = {
    "north": "Cold mornings, 6 to 24 C, dry all week",
    "south": "Heavy rain expected, 24 to 29 C, 60 to 85 mm a day",
    "east": "Thunderstorms likely midweek, 18 to 29 C",
    "west": "Hot and dry, 23 to 35 C",
    "central": "Clear and pleasant, 14 to 32 C",
}


@tool
def get_weather_forecast(region: str) -> str:
    """Get the 5-day weather forecast for a region (north, south, east, west or central)."""
    forecast = SAMPLE_WEATHER.get(region.lower(), "No forecast for that region")
    return f"{region.capitalize()} (sample forecast): {forecast}"
