import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from mcp_server.tools import (
    get_financial_summary,
    get_inventory_status,
    get_low_stock_items,
    get_sales_summary,
    get_top_vendors,
    get_weather_forecast,
)

load_dotenv()

model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL"),
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

agent = create_agent(
    model=model,
    tools=[
        get_inventory_status,
        get_sales_summary,
        get_financial_summary,
        get_low_stock_items,
        get_top_vendors,
        get_weather_forecast,
    ],
    system_prompt="You are an inventory management assistant for Inventra.",
)


def invoke_agent(query: str) -> str:
    result = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": query}
            ]
        }
    )

    return result["messages"][-1].content


if __name__ == "__main__":
    print(invoke_agent("What is the current low-stock status?"))