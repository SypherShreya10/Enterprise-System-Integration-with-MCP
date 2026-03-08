"""
ERP Agent

Purpose
-------
Handles all ERP-related queries including:

- products
- inventory
- stock availability
- warehouse locations
- sales orders

Responsibilities:
- interpret the user query
- choose the correct ERP tool
- generate valid tool parameters
"""

import json
import logging
from typing import Dict, Any

from ai.graph.state import AgentState
from ai.llm.groq_client import get_llm


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logger = logging.getLogger("erp_agent")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------
# System Prompt (optimized for Groq)
# ---------------------------------------------------------

ERP_AGENT_SYSTEM_PROMPT = """
You are an ERP automation agent.

Your job is to select the correct ERP tool and produce parameters.

Available ERP tools:

get_product(
 product_id, name, default_code, categ_id, type, limit
)

get_product_stock(
 product_id, location_id
)

check_product_availability(
 product_id, quantity, date_required
)

get_stock_location(
 location_id, name, limit
)

get_sale_order(
 order_id, name, partner_id, state, date_from, date_to, limit
)

get_sale_order_lines(
 order_id, limit
)

create_sale_order(
 partner_id,
 order_lines,
 date_order,
 validity_date,
 client_order_ref
)

get_customer_order_history(
 partner_id
)

Output JSON only:

{
 "tool_name": "tool_name_here",
 "tool_input": {
     "param": "value"
 }
}

Rules:

- tool_name must match one of the tools above
- parameters must match the tool definition
- do not invent parameters
- omit optional parameters if not needed
- output JSON only
"""


# ---------------------------------------------------------
# JSON Parser
# ---------------------------------------------------------

def _parse_llm_json(content: str) -> Dict[str, Any]:

    try:
        return json.loads(content.strip())

    except json.JSONDecodeError:

        logger.error("ERP agent produced invalid JSON: %s", content)

        raise ValueError("ERP agent returned invalid JSON.")


# ---------------------------------------------------------
# ERP Agent Node
# ---------------------------------------------------------

def erp_agent(state: AgentState) -> AgentState:
    """
    LangGraph node responsible for ERP tool selection.

    Input State:
    {
        "user_query": str
    }

    Output State:
    {
        "tool_name": str
        "tool_input": dict
    }
    """

    user_query = state.get("user_query")

    if not user_query:
        raise ValueError("ERP agent received empty query.")

    logger.info("ERP agent received query: %s", user_query)

    llm = get_llm()

    try:

        response = llm.invoke(
            [
                {"role": "system", "content": ERP_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_query},
            ]
        )

        content = response.content

        logger.info("ERP agent raw response: %s", content)

        parsed = _parse_llm_json(content)

        tool_name = parsed.get("tool_name")
        tool_input = parsed.get("tool_input")

        if not tool_name:
            raise ValueError("ERP agent did not provide tool_name.")

        if not isinstance(tool_input, dict):
            raise ValueError("ERP agent tool_input must be a dictionary.")

        state["tool_name"] = tool_name
        state["tool_input"] = tool_input

        logger.info(
            "ERP agent selected tool | tool=%s params=%s",
            tool_name,
            tool_input,
        )

    except Exception as exc:

        logger.error("ERP agent failure: %s", str(exc))

        raise

    return state