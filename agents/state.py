from typing import Any, Dict, List, Literal, TypedDict

from pydantic import BaseModel, Field


class RouteDecision(BaseModel):
    route: Literal["full_forecast_pipeline", "quick_data_lookup"] = Field(
        description="Choose 'full_forecast_pipeline' for forecasting, weather impact, budget planning, or raising tickets. Choose 'quick_data_lookup' for simple status/vendor/sales questions."
    )
    reasoning: str = Field(description="Brief reason why this route was selected")

class SKURecommendation(BaseModel):
    sku: str = Field(description="Product SKU code")
    product_name: str
    forecasted_demand: int = Field(description="Predicted unit demand based on weather + history")
    recommended_reorder_qty: int = Field(description="Units to order; 0 if stock is sufficient")
    financial_impact: float = Field(description="Estimated procurement cost")
    vendor_id: str
    risk_rationale: str = Field(description="Clear explanation linking weather forecast and stock levels")
    requires_ticket: bool = Field(description="True if immediate reorder or budget alert is needed")

class OptimizationPlan(BaseModel):
    executive_summary: str
    total_budget_required: float
    recommendations: List[SKURecommendation]

class InventraState(TypedDict):
    user_query: str
    region: str
    route: str
    route_reasoning: str
    historical_context: str
    weather_report: Dict[str, Any]
    advisory_context: str
    optimization_plan: Dict[str, Any]
    created_tickets: List[Dict[str, Any]]
