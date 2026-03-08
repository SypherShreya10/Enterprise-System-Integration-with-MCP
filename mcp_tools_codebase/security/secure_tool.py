


import functools
from auth.jwt_handler import verify_token
from config.rbac_config import TOOL_PERMISSIONS


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

            allowed_roles = TOOL_PERMISSIONS.get(tool_name)

            if not allowed_roles:
                return {"error": "Tool permission not configured"}

            if user_role not in allowed_roles:
                print(f"[SECURITY] user={user} role={user_role} tool={tool_name} → DENIED")
                return {"error": f"Role '{user_role}' not allowed for {tool_name}"}
            
            print(f"[SECURITY] user={user} role={user_role} tool={tool_name} → ALLOWED")

            # -------------------------------------------------
            # STEP 4: Execute tool
            # -------------------------------------------------

            return func(*args, **kwargs)

        return wrapper

    return decorator










# import functools
# from auth.jwt_handler import verify_token
# from config.rbac_config import TOOL_PERMISSIONS


# def secure_tool(tool_name):
#     """
#     Decorator to secure MCP tools using JWT + RBAC
#     """

#     def decorator(func):

#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):

#             token = kwargs.pop("token", None)

#             if not token:
#                 raise Exception("Authentication token missing")

#             payload = verify_token(token)

#             role = payload.get("role")
#             user = payload.get("sub")

#             print("USER ROLE:", role)

#             allowed_roles = TOOL_PERMISSIONS.get(tool_name, [])

#             if role not in allowed_roles:
#                 print(f"[SECURITY] user={user} role={role} tool={tool_name} → DENIED")
#                 raise Exception(f"Role '{role}' not allowed for {tool_name}")

#             print(f"[SECURITY] user={user} role={role} tool={tool_name} → ALLOWED")

#             return func(*args, **kwargs)

#         return wrapper

#     return decorator




