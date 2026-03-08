"""
CRM Agent

Purpose
-------
Handles all CRM-related requests once the supervisor
classifies the request domain as CRM.

Responsibilities:
- interpret the user query
- choose the correct CRM tool
- generate valid tool parameters

The agent must only use tools defined in the CRM tool set
and must respect the parameter structure of each tool.
"""

import json
import logging
from typing import Dict, Any

from ai.graph.state import AgentState
from ai.llm.groq_client import get_llm


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logger = logging.getLogger("crm_agent")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------
# System Prompt (compact for Groq)
# ---------------------------------------------------------

CRM_AGENT_SYSTEM_PROMPT = """
You are a CRM automation agent.

Your job is to choose the correct CRM tool and produce parameters.

Available CRM tools:

get_partner(
 partner_id, name, email, is_customer, is_supplier, limit
)

create_partner(
 name, email, phone, is_customer, is_supplier,
 street, city, zip, country_id
)

get_lead(
 lead_id, partner_id, stage_id, user_id, type, limit
)

update_lead_stage(
 lead_id, stage_id
)

get_stage(
 stage_id, name, is_won, limit
)

get_team(
 team_id, name, user_id, limit
)

create_activity(
 activity_type_id,
 user_id,
 date_deadline,
 res_model,
 res_id,
 summary,
 note
)

get_activity(
 user_id,
 res_model,
 date_deadline,
 state,
 limit
)

Output JSON only:

{
 "tool_name": "tool_name_here",
 "tool_input": {
     "param": "value"
 }
}

Rules:
- tool_name must be one of the tools above
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

        logger.error("CRM agent produced invalid JSON: %s", content)

        raise ValueError("CRM agent returned invalid JSON.")


# ---------------------------------------------------------
# CRM Agent Node
# ---------------------------------------------------------

def crm_agent(state: AgentState) -> AgentState:
    """
    LangGraph node responsible for CRM tool selection.

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
        raise ValueError("CRM agent received empty query.")

    logger.info("CRM agent received query: %s", user_query)

    llm = get_llm()

    try:

        response = llm.invoke(
            [
                {"role": "system", "content": CRM_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_query},
            ]
        )

        content = response.content

        logger.info("CRM agent raw response: %s", content)

        parsed = _parse_llm_json(content)

        tool_name = parsed.get("tool_name")
        tool_input = parsed.get("tool_input")

        if not tool_name:
            raise ValueError("CRM agent did not provide tool_name.")

        if not isinstance(tool_input, dict):
            raise ValueError("CRM agent tool_input must be a dictionary.")

        state["tool_name"] = tool_name
        state["tool_input"] = tool_input

        logger.info(
            "CRM agent selected tool | tool=%s params=%s",
            tool_name,
            tool_input,
        )

    except Exception as exc:

        logger.error("CRM agent failure: %s", str(exc))

        raise

    return state