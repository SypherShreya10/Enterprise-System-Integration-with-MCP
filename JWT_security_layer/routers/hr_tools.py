from fastapi import APIRouter, Depends
from auth.role_guard import require_tool_access

router = APIRouter()


@router.get("/get_employee")
def get_employee(user=Depends(require_tool_access("get_employee"))):

    return {
        "employee": "John Doe",
        "department": "Engineering",
        "requested_by": user["sub"],
        "role": user["role"]
    }