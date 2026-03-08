"""
LangGraph Builder

Purpose
-------
Defines the complete workflow graph connecting all agents.

Workflow:

START
 ↓
Supervisor
 ↓
Router
 ↓
HR / CRM / ERP Agent
 ↓
Tool Executor
 ↓
Response Agent
 ↓
END
"""

import logging

from langgraph.graph import StateGraph, START, END

from ai.graph.state import AgentState
from ai.graph.router import route_domain

from ai.agents.supervisor import supervisor_agent
from ai.agents.hr_agent import hr_agent
from ai.agents.crm_agent import crm_agent
from ai.agents.erp_agent import erp_agent
from ai.agents.response_agent import response_agent

from ai.tools.tool_executor import tool_executor


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logger = logging.getLogger("graph_builder")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------
# Build Graph
# ---------------------------------------------------------

def build_graph():
    """
    Constructs and compiles the LangGraph workflow.
    """

    logger.info("Building LangGraph workflow")

    builder = StateGraph(AgentState)

    # -----------------------------------------------------
    # Register Nodes
    # -----------------------------------------------------

    builder.add_node("supervisor", supervisor_agent)

    builder.add_node("hr_agent", hr_agent)
    builder.add_node("crm_agent", crm_agent)
    builder.add_node("erp_agent", erp_agent)

    builder.add_node("tool_executor", tool_executor)

    builder.add_node("response_agent", response_agent)

    # -----------------------------------------------------
    # Start Edge
    # -----------------------------------------------------

    builder.add_edge(START, "supervisor")

    # -----------------------------------------------------
    # Conditional Routing
    # -----------------------------------------------------

    builder.add_conditional_edges(
        "supervisor",
        route_domain,
        {
            "hr_agent": "hr_agent",
            "crm_agent": "crm_agent",
            "erp_agent": "erp_agent",
        },
    )

    # -----------------------------------------------------
    # Tool Execution
    # -----------------------------------------------------

    builder.add_edge("hr_agent", "tool_executor")
    builder.add_edge("crm_agent", "tool_executor")
    builder.add_edge("erp_agent", "tool_executor")

    # -----------------------------------------------------
    # Response Generation
    # -----------------------------------------------------

    builder.add_edge("tool_executor", "response_agent")

    # -----------------------------------------------------
    # End
    # -----------------------------------------------------

    builder.add_edge("response_agent", END)

    graph = builder.compile()

    logger.info("LangGraph compiled successfully")

    return graph