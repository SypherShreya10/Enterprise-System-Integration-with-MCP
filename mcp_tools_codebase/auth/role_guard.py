from fastapi import Depends, HTTPException
from config.rbac_config import TOOL_PERMISSIONS
from auth.dependencies import get_current_user


def require_tool_access(tool_name):

    def role_checker(user=Depends(get_current_user)):

        user_role = user["role"]

        allowed_roles = TOOL_PERMISSIONS.get(tool_name)

        if allowed_roles is None:
            raise HTTPException(
                status_code=500,
                detail="Tool permission not defined"
            )

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' not allowed to access {tool_name}"
            )

        return user

    return role_checker