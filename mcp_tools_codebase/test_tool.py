from security.secure_tool import secure_tool
from mcp_odoo.server import get_partner_tool
import json

token = input("Paste JWT token: ")

result = get_partner_tool(
    token=token,
    name="MCP partner"
)

data = result 
print(json.dumps(data, indent=4))
# print(result)