from functools import lru_cache

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings


@lru_cache(maxsize=1)
def get_climate_advisory_retriever():
    docs = [
        Document(
            page_content="Advisory: Unseasonal cyclonic rainfall in Northern plains increases umbrella and rainwear demand by 220% within 48 hours. Prioritize suppliers with short lead times.",
            metadata={"source": "IMD_Climate_Brief", "category": "Rainwear"}
        ),
        Document(
            page_content="Advisory: Heatwave alerts (temperatures > 40°C) trigger a 180% surge in portable coolers and electrolyte beverages. Bulk discounts apply on high-volume beverage orders.",
            metadata={"source": "Seasonal_Retail_Playbook", "category": "Heatwave"}
        ),
        Document(
            page_content="Finance Policy: Maintain at least 20% liquidity buffer in procurement reserve; prioritize high-margin weather-sensitive SKUs during severe weather warnings.",
            metadata={"source": "CFO_Guidelines", "category": "Finance"}
        ),
    ]
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 2})