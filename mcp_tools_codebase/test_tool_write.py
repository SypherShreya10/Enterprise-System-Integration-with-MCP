from security.secure_tool import secure_tool
from mcp_odoo.server import create_partner_tool
import json

token = input("Paste JWT token: ")

result = create_partner_tool(
    token=token,
    name="MCP partner 010",
    email="mcppartner010@xyz.com",
    phone="1234567890",
    is_customer=True,
    city="Pune"
)

data = result 
print(json.dumps(data, indent=4))

# print(result)