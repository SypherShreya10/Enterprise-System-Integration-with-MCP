from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from auth.jwt_handler import create_access_token
import mcp_odoo.server as mcp_server

app = FastAPI(title="Secure MCP Gateway")


# -----------------------------
# Fake users (demo)
# -----------------------------

users = {
    "viewer": {"password": "viewer123", "role": "viewer"},
    "operator": {"password": "operator123", "role": "operator"},
    "admin": {"password": "admin123", "role": "admin"},
    "manager": {"password": "manager123", "role": "manager"},
    "sales_user": {"password": "sales123", "role": "sales"},
}


# -----------------------------
# Login
# -----------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(data: LoginRequest):

    user = users.get(data.username)

    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": data.username,
        "role": user["role"]
    })

    return {"access_token": token}


# -----------------------------
# Generic Tool Call
# -----------------------------

class ToolRequest(BaseModel):
    token: str
    params: Dict[str, Any] = {}
    
@app.get("/tools")
def list_tools():

    tools = []

    for attr in dir(mcp_server):
        if attr.endswith("_tool"):
            tools.append(attr.replace("_tool", ""))

    return {"tools": tools}


@app.post("/tool/{tool_name}")
def call_tool(tool_name: str, request: ToolRequest):

    # Build function name
    func_name = f"{tool_name}_tool"

    # Check tool exists
    if not hasattr(mcp_server, func_name):
        raise HTTPException(status_code=404, detail="Tool not found")

    tool_func = getattr(mcp_server, func_name)

    try:
        result = tool_func(
            token=request.token,
            **request.params
        )

        return {"result": result}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    

# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel

# from auth.jwt_handler import create_access_token
# from mcp_odoo.server import create_partner_tool, get_partner_tool

# app = FastAPI(title="Secure MCP Gateway")


# # -----------------------------
# # Fake users (for demo)
# # -----------------------------

# users = {
#     "viewer": {"password": "viewer123", "role": "viewer"},
#     "operator": {"password": "operator123", "role": "operator"},
#     "admin": {"password": "admin123", "role": "admin"},
#     "manager": {"password": "manager123", "role": "manager"},
#     "sales_user": {"password": "sales123", "role": "sales"},
# }


# # -----------------------------
# # Login schema
# # -----------------------------

# class LoginRequest(BaseModel):
#     username: str
#     password: str


# # -----------------------------
# # Login endpoint
# # -----------------------------

# @app.post("/login")
# def login(data: LoginRequest):

#     user = users.get(data.username)

#     if not user or user["password"] != data.password:
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     token = create_access_token({
#         "sub": data.username,
#         "role": user["role"]
#     })

#     return {"access_token": token}


# # -----------------------------
# # Create partner schema
# # -----------------------------

# class CreatePartnerRequest(BaseModel):
#     token: str
#     name: str
#     email: str | None = None
#     phone: str | None = None
#     city: str | None = None


# # -----------------------------
# # Create partner endpoint
# # -----------------------------

# @app.post("/tools/create_partner")
# def create_partner(data: CreatePartnerRequest):

#     result = create_partner_tool(
#         token=data.token,
#         name=data.name,
#         email=data.email,
#         phone=data.phone,
#         city=data.city,
#         is_customer=True
#     )

#     return result


# # -----------------------------
# # Get partner schema
# # -----------------------------

# class GetPartnerRequest(BaseModel):
#     token: str
#     name: str


# @app.post("/tools/get_partner")
# def get_partner(data: GetPartnerRequest):

#     result = get_partner_tool(
#         token=data.token,
#         name=data.name
#     )

#     return result