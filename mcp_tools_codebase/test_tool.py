from security.secure_tool import secure_tool
from mcp_odoo.server import get_partner_tool

token = input("Paste JWT token: ")

result = get_partner_tool(
    token=token,
    name="Admin"
)

print(result)