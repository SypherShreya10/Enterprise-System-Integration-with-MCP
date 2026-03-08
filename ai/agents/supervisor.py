"""
Supervisor Agent

Purpose
-------
The Supervisor Agent is the first reasoning step in the LangGraph pipeline.

Responsibilities:
- Read the user's query
- Determine the business domain
- Determine the high-level intent
- Pass structured routing information to the router

The supervisor does NOT:
- call tools
- modify business data
- generate the final answer

This design improves:
- security
- predictability
- auditability
"""

import json
import logging
from typing import Any, Dict

from ai.graph.state import AgentState
from ai.llm.groq_client import get_llm


# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------

logger = logging.getLogger("supervisor_agent")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------
# System Prompt (optimized for small LLMs like Groq)
# ---------------------------------------------------------

SUPERVISOR_SYSTEM_PROMPT = """
You are the Supervisor AI for an enterprise automation system.

Your task is to classify a user request into:
1) domain
2) intent

Allowed domains:
HR   → employees, departments, attendance, leave, availability
CRM  → customers, leads, opportunities, activities
ERP  → products, inventory, orders

Output JSON only:

{
 "domain": "HR | CRM | ERP",
 "intent": "snake_case_intent"
}

Examples:

User: Is John available tomorrow?
Output:
{
 "domain": "HR",
 "intent": "check_employee_availability"
}

User: Create a customer called Tesla
Output:
{
 "domain": "CRM",
 "intent": "create_partner"
}

User: How many units of product A are in stock?
Output:
{
 "domain": "ERP",
 "intent": "check_product_stock"
}

Rules:
- JSON only
- no explanations
- domain must be HR, CRM, or ERP
"""


# ---------------------------------------------------------
# Helper Function
# ---------------------------------------------------------

def _parse_llm_json(content: str) -> Dict[str, Any]:
    """
    Safely parse LLM JSON output.

    This helper ensures:
    - whitespace removed
    - JSON errors handled
    """

    try:
        return json.loads(content.strip())
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse supervisor JSON output: %s", content)
        raise ValueError("Supervisor returned invalid JSON.") from exc


# ---------------------------------------------------------
# Supervisor Agent
# ---------------------------------------------------------

def supervisor_agent(state: AgentState) -> AgentState:
    """
    LangGraph node for supervisor classification.

    Input State:
        {
            "user_query": str
        }

    Output State:
        {
            "domain": str
            "intent": str
        }
    """

    user_query = state.get("user_query")

    if not user_query:
        raise ValueError("Supervisor agent received empty query.")

    logger.info("Supervisor received query: %s", user_query)

    llm = get_llm()

    try:

        response = llm.invoke(
            [
                {"role": "system", "content": SUPERVISOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_query},
            ]
        )

        content = response.content

        logger.info("Supervisor raw LLM response: %s", content)

        parsed = _parse_llm_json(content)

        domain = parsed.get("domain")
        intent = parsed.get("intent")

        if not domain or not intent:
            raise ValueError("Supervisor output missing required fields.")

        # enforce allowed domains
        if domain not in {"HR", "CRM", "ERP"}:
            raise ValueError(f"Invalid domain returned: {domain}")

        state["domain"] = domain
        state["intent"] = intent

        logger.info(
            "Supervisor classification complete | Domain=%s | Intent=%s",
            domain,
            intent,
        )

    except Exception as exc:

        logger.error("Supervisor agent failure: %s", str(exc))

        raise

    return state