from security.secure_tool import secure_tool
from mcp_odoo.server import create_partner_tool

token = input("Paste JWT token: ")

result = create_partner_tool(
    token=token,
    name="MCP partner 003",
    email="mcppartner003@xyz.com",
    phone="1234567890",
    is_customer=True,
    city="Mexico"
)

print(result)