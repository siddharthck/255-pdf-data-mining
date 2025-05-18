import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_PATH = "10k_analyzer.db"
UPLOAD_FOLDER = "uploads"

LLM_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MAX_TOKENS = 4000
TEMPERATURE = 0.3

EXTRACTION_PROMPTS = {
    "financial_metrics": """
    Extract key financial metrics from this 10-K section:
    - Revenue (current and previous year)
    - Net Income (current and previous year)
    - Total Assets
    - Total Liabilities
    - Cash and Cash Equivalents
    - Total Debt
    - Return on Equity
    - Operating Cash Flow
    
    Return as JSON with exact numbers and currency.
    """,
    
    "risk_factors": """
    Extract and summarize the main risk factors from this 10-K section.
    Categorize risks into: Market Risk, Credit Risk, Operational Risk, Regulatory Risk, Competitive Risk.
    Return as JSON with categories and bullet points.
    """,
    
    "business_overview": """
    Extract business overview information:
    - Main business segments
    - Key products/services
    - Geographic presence
    - Competitive advantages
    - Recent developments
    
    Return as structured JSON.
    """,
    
    "management_discussion": """
    Summarize Management Discussion & Analysis section:
    - Key financial performance highlights
    - Significant changes from previous year
    - Future outlook statements
    - Capital allocation priorities
    
    Return as structured summary.
    """
}

CHART_CONFIGS = {
    "revenue_trend": {
        "title": "Revenue Trend",
        "x_label": "Year",
        "y_label": "Revenue (in millions)",
        "chart_type": "line"
    },
    "financial_ratios": {
        "title": "Key Financial Ratios",
        "chart_type": "bar"
    },
    "risk_distribution": {
        "title": "Risk Factor Distribution",
        "chart_type": "pie"
    }
}

DEFAULT_FALLBACK_DATA = {
    "company_name": "Sample Corporation",
    "fiscal_year": "2023",
    "revenue": 100000000000,
    "net_income": 20000000000,
    "total_assets": 150000000000,
    "total_debt": 40000000000,
    "cash_equivalents": 15000000000,
    "segments": ["Product A", "Product B", "Services", "Technology", "International"],
    "risk_factors": [
        "Market competition and pricing pressure",
        "Supply chain and operational risks",
        "Regulatory and compliance requirements",
        "Economic and market volatility",
        "Technology and innovation challenges"
    ]
}