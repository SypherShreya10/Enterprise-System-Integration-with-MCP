"""
Router

Purpose
-------
The router determines which domain agent should handle the request.

It reads the 'domain' field produced by the supervisor agent and
routes the workflow to the correct domain-specific agent.

Routing is deterministic and does not use an LLM.
This improves security, reliability, and performance.

Supported Domains:
- HR
- CRM
- ERP
"""

import logging
from ai.graph.state import AgentState


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logger = logging.getLogger("router")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------
# Router Function
# ---------------------------------------------------------

def route_domain(state: AgentState) -> str:
    """
    Determine which agent node should execute next.

    Input State Example:
    {
        "domain": "HR"
    }

    Output:
        node name (str)
    """

    domain = state.get("domain")

    if not domain:
        raise ValueError("Router received state without 'domain' field.")

    logger.info("Router received domain classification: %s", domain)

    # -----------------------------------------------------
    # Routing Logic
    # -----------------------------------------------------

    if domain == "HR":
        logger.info("Routing to HR agent")
        return "hr_agent"

    elif domain == "CRM":
        logger.info("Routing to CRM agent")
        return "crm_agent"

    elif domain == "ERP":
        logger.info("Routing to ERP agent")
        return "erp_agent"

    # -----------------------------------------------------
    # Safety fallback
    # -----------------------------------------------------

    logger.error("Router received unsupported domain: %s", domain)

    raise ValueError(f"Unsupported domain returned by supervisor: {domain}")