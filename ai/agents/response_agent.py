"""
Response Agent

Purpose
-------
The response agent converts raw tool output into a
clear, user-friendly response.

It does not call tools and does not modify data.
It simply formats the results returned by the tool executor.
"""

import logging
import json
from typing import Any

from ai.graph.state import AgentState
from ai.llm.groq_client import get_llm


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logger = logging.getLogger("response_agent")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------
# System Prompt (small for Groq)
# ---------------------------------------------------------

RESPONSE_SYSTEM_PROMPT = """
You are an enterprise assistant.

Your job is to explain the result returned from a system tool.

Rules:

- Provide a clear answer to the user
- Be concise
- Do not invent data
- Only use information present in the tool output
- If the tool output contains an error, explain the error

Respond in plain text.
"""


# ---------------------------------------------------------
# Response Agent Node
# ---------------------------------------------------------

def response_agent(state: AgentState) -> AgentState:
    """
    LangGraph node responsible for generating the final response.

    Input State:
    {
        "tool_name": str,
        "tool_output": Any
    }

    Output State:
    {
        "final_response": str
    }
    """

    tool_name = state.get("tool_name")
    tool_output = state.get("tool_output")

    if tool_output is None:
        raise ValueError("Response agent received empty tool_output.")

    logger.info("Response agent formatting output from tool: %s", tool_name)

    llm = get_llm()

    try:

        tool_output_json = json.dumps(tool_output, indent=2)

        prompt = f"""
User Query:
{state.get("user_query")}

Tool Used:
{tool_name}

Tool Output:
{tool_output_json}
"""

        response = llm.invoke(
            [
                {"role": "system", "content": RESPONSE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
        )

        final_text = response.content.strip()

        state["final_response"] = final_text

        logger.info("Response generated successfully")

    except Exception as exc:

        logger.error("Response agent failed: %s", str(exc))

        raise

    return state