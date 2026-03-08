from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict):
    """
    Shared state passed between LangGraph nodes.
    """

    messages: List[str]

    user_query: str

    intent: Optional[str]

    domain: Optional[str]

    tool_name: Optional[str]

    tool_input: Optional[Dict[str, Any]]

    tool_output: Optional[Any]

    final_response: Optional[str]