"""
Prompt templates for LLM-powered trend analysis.
"""

ANALYSIS_SYSTEM_PROMPT = """You are a food trend analyst for Picnic Technologies, a leading online supermarket in Europe.

Your role is to evaluate food trends and determine:
1. How well they fit Picnic's product offerings
2. Market readiness and adoption timeline
3. Customer sentiment
4. Recommended actions and potential risks

Picnic serves customers in:
- Netherlands (NL) - Primary market
- Germany (DE) - Growing market
- France (FR) - Expansion market

Picnic focuses on:
- Fresh groceries and everyday essentials
- High quality at competitive prices
- Fast delivery within 20 minutes
- Sustainability and reducing food waste
- Middle-class families as primary customers

When analyzing trends, consider:
- Is this trend relevant to Picnic's product categories?
- Does it align with customer demographics and preferences?
- Is the trend sustainable or a short-term fad?
- What's the expected adoption timeline in NL/DE/FR markets?
- Are there any risks (supply chain, regulation, health concerns)?
"""


ANALYSIS_USER_PROMPT_TEMPLATE = """Analyze this food trend:

**Trend**: {trend_name}
**Score**: {score}
**Countries**: {countries}
**Sources**: {sources}

Provide analysis in JSON format with these fields:

{{
  "product_fit": "high|medium|low",
  "product_fit_reasoning": "Brief explanation (1-2 sentences) of why this trend fits or doesn't fit Picnic's product offerings",
  "market_readiness": "ready|emerging|niche",
  "adoption_timeline": "now|3-6mo|6-12mo|12mo+",
  "sentiment": "positive|neutral|negative",
  "recommended_actions": ["action1", "action2"],
  "risks": ["risk1", "risk2"]
}}

Guidelines:
- **product_fit**: high=perfect for Picnic's catalog, medium=requires some adaptation, low=not suitable
- **market_readiness**: ready=mainstream adoption, emerging=growing interest, niche=early adopters only
- **adoption_timeline**: Estimated time until trend reaches NL/DE/FR markets (if not already there)
- **sentiment**: Customer sentiment toward this trend
- **recommended_actions**: 2-4 specific actions Picnic should take (e.g., "Source organic matcha suppliers", "Add product to NL catalog")
- **risks**: 2-3 potential risks or concerns (e.g., "Supply chain instability", "Short-term fad")

Be concise but specific. Focus on actionable insights.
"""


def create_analysis_prompt(trend: dict) -> str:
    """
    Create analysis prompt for a single trend.

    Args:
        trend: Trend dictionary with keys: trend, score, countries, sources

    Returns:
        Formatted prompt string
    """
    return ANALYSIS_USER_PROMPT_TEMPLATE.format(
        trend_name=trend.get("trend", "Unknown"),
        score=trend.get("score", 0),
        countries=", ".join(trend.get("countries", [])),
        sources=", ".join(trend.get("sources", [])) if "sources" in trend else "Multiple sources",
    )
