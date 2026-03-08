
"""
HR Agent

Purpose
-------
Handles all HR-related requests after the supervisor
classifies the domain as HR.

Responsibilities:
- interpret the user query
- select the correct HR tool
- generate valid tool parameters

The agent MUST only use the HR tools defined in the
tool registry.

It must also produce parameters that match the
actual tool function signatures.
"""

import json
import logging
import re
from typing import Dict, Any

from ai.graph.state import AgentState
from ai.llm.groq_client import get_llm


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logger = logging.getLogger("hr_agent")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------
# Allowed HR Tools
# ---------------------------------------------------------

ALLOWED_HR_TOOLS = {
    "get_employee",
    "get_department",
    "get_job",
    "get_employee_leaves",
    "check_employee_availability",
    "get_employee_attendance",
}


# ---------------------------------------------------------
# System Prompt
# ---------------------------------------------------------

HR_AGENT_SYSTEM_PROMPT = """
You are an HR automation agent for an enterprise system.

Your task is to select the correct HR tool and provide
parameters required for that tool.

You are NOT allowed to generate HR data yourself.
All real data will be retrieved by the tool.

Allowed HR tools:

get_employee(
    employee_id: int | None,
    name: str | None,
    department_id: int | None,
    job_id: int | None,
    limit: int
)

get_department(
    department_id: int | None,
    name: str | None,
    manager_id: int | None,
    limit: int
)

get_job(
    job_id: int | None,
    name: str | None,
    department_id: int | None,
    limit: int
)

get_employee_leaves(
    employee_id: int | None,
    date_from: str | None,
    date_to: str | None,
    limit: int
)

check_employee_availability(
    employee_id: int,
    date_from: str,
    date_to: str
)

get_employee_attendance(
    employee_id: int | None,
    date_filter: str | None,
    limit: int
)

Output JSON ONLY:

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
- do NOT wrap JSON in markdown
"""


# ---------------------------------------------------------
# JSON Cleaning
# ---------------------------------------------------------

def _clean_llm_json(content: str) -> str:
    """
    Removes markdown wrappers like ```json ... ``` if present.
    """

    cleaned = content.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"```[a-zA-Z]*", "", cleaned)
        cleaned = cleaned.replace("```", "")

    return cleaned.strip()


# ---------------------------------------------------------
# JSON Parser
# ---------------------------------------------------------

def _parse_llm_json(content: str) -> Dict[str, Any]:

    cleaned = _clean_llm_json(content)

    try:
        parsed = json.loads(cleaned)

    except json.JSONDecodeError:
        logger.error("HR agent produced invalid JSON: %s", content)
        raise ValueError("HR agent returned invalid JSON.")

    return parsed


# ---------------------------------------------------------
# Parameter Sanitization
# ---------------------------------------------------------

def _sanitize_parameters(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prevent unsafe parameters.
    """

    if "limit" in tool_input:

        try:
            tool_input["limit"] = int(tool_input["limit"])
        except Exception:
            tool_input["limit"] = 10

        # Prevent extremely large queries
        tool_input["limit"] = min(tool_input["limit"], 50)

    return tool_input


# ---------------------------------------------------------
# HR Agent Node
# ---------------------------------------------------------

def hr_agent(state: AgentState) -> AgentState:
    """
    LangGraph node responsible for HR tool selection.

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
        raise ValueError("HR agent received empty query.")

    logger.info("HR agent received query: %s", user_query)

    llm = get_llm()

    try:

        response = llm.invoke(
            [
                {"role": "system", "content": HR_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_query},
            ]
        )

        content = response.content

        logger.info("HR agent raw response: %s", content)

        parsed = _parse_llm_json(content)

        tool_name = parsed.get("tool_name")
        tool_input = parsed.get("tool_input", {})

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if tool_name not in ALLOWED_HR_TOOLS:
            raise ValueError(f"Invalid HR tool selected: {tool_name}")

        if not isinstance(tool_input, dict):
            raise ValueError("HR agent tool_input must be a dictionary.")

        tool_input = _sanitize_parameters(tool_input)

        state["tool_name"] = tool_name
        state["tool_input"] = tool_input

        logger.info(
            "HR agent selected tool | tool=%s params=%s",
            tool_name,
            tool_input,
        )

    except Exception as exc:

        logger.error("HR agent failure: %s", str(exc))
        raise

    return state

