import logging
from ai.graph.state import AgentState

logger = logging.getLogger("router")
logger.setLevel(logging.INFO)


def route_domain(state: AgentState) -> str:

    domain = state.get("domain")

    if domain == "HR":
        return "hr_agent"

    if domain == "CRM":
        return "crm_agent"

    if domain == "ERP":
        return "erp_agent"

    raise ValueError(f"Unsupported domain: {domain}")