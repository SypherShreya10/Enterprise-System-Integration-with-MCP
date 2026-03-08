


import functools
from auth.jwt_handler import verify_token
from config.rbac_config import TOOL_PERMISSIONS, ROLE_HIERARCHY
from security.audit_logger import log_audit


def secure_tool(tool_name: str):
    """
    Decorator to secure MCP tools using JWT + RBAC
    """

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            # -------------------------------------------------
            # STEP 1: Extract token (temporary simulation)
            # -------------------------------------------------

            token = kwargs.pop("token", None)

            if not token:
                raise Exception("Authentication token missing")

            # -------------------------------------------------
            # STEP 2: Verify JWT
            # -------------------------------------------------

            payload = verify_token(token)

            if not payload:
                return {"error": "Invalid or expired token"}

            user_role = payload.get("role")
            user = payload.get("sub")
            print("USER ROLE:", user_role)

            
            # -------------------------------------------------
            # STEP 3: RBAC Check
            # -------------------------------------------------

            required_roles = TOOL_PERMISSIONS.get(tool_name, [])
            print(f"[SECURITY] Checking access for tool {tool_name}")

            if not required_roles:
                return {"error": f"No permissions defined for tool {tool_name}"}

            required_role = required_roles[0]

            if ROLE_HIERARCHY[user_role] < ROLE_HIERARCHY[required_role]:
                print(f"[SECURITY] user={user} role={user_role} tool={tool_name} → DENIED")
                log_audit(user, user_role, tool_name, "DENIED")
                raise Exception(f"Role '{user_role}' not allowed for {tool_name}")

            print(f"[SECURITY] user={user} role={user_role} tool={tool_name} → ALLOWED")
            log_audit(user, user_role, tool_name, "ALLOWED")

            # -------------------------------------------------
            # STEP 4: Execute tool
            # -------------------------------------------------

            return func(*args, **kwargs)

        return wrapper

    return decorator



