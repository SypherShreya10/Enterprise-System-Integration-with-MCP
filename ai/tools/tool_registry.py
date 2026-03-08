"""
Central registry of all MCP tools.
Agents and executors reference this registry
instead of importing tools directly.
"""

USE_MOCK = True  # switch this to False when connecting to real Odoo


if USE_MOCK:

    from ai.tools.mock_tools import (
        get_employee,
        get_department,
        get_job,
        get_employee_leaves,
        check_employee_availability,
        get_employee_attendance,
    )

    # simple mocks for CRM/ERP
    def create_partner(**kwargs):
        return {"status": "success", "partner_id": 101}

    def get_partner(**kwargs):
        return [{"id": 1, "name": "Tesla"}]

    def get_lead(**kwargs):
        return [{"id": 5, "name": "Big Deal"}]

    def update_lead_stage(**kwargs):
        return {"status": "updated"}

    def get_stage(**kwargs):
        return [{"id": 1, "name": "New"}]

    def get_team(**kwargs):
        return [{"id": 1, "name": "Sales Team"}]

    def create_activity(**kwargs):
        return {"activity": "created"}

    def get_activity(**kwargs):
        return [{"summary": "Follow up"}]

    def get_product(**kwargs):
        return [{"id": 1, "name": "Laptop"}]

    def get_product_stock(**kwargs):
        return {"product": "Laptop", "stock": 45}

    def check_product_availability(**kwargs):
        return {"available": True}

    def get_stock_location(**kwargs):
        return [{"id": 1, "name": "Warehouse"}]

    def get_sale_order(**kwargs):
        return [{"id": 100, "customer": "Tesla"}]

    def get_sale_order_lines(**kwargs):
        return [{"product": "Laptop", "qty": 2}]

    def create_sale_order(**kwargs):
        return {"order_id": 200}

    def get_customer_order_history(**kwargs):
        return [{"order_id": 100}]


else:

    from tools.hr import (
        get_employee,
        get_department,
        get_job,
        get_employee_leaves,
        check_employee_availability,
        get_employee_attendance,
    )

    from tools.crm import (
        get_partner,
        create_partner,
        get_lead,
        update_lead_stage,
        get_stage,
        get_team,
    )

    from tools.mail import (
        create_activity,
        get_activity,
    )

    from tools.erp import (
        get_product,
        get_product_stock,
        check_product_availability,
        get_stock_location,
        get_sale_order,
        get_sale_order_lines,
        create_sale_order,
        get_customer_order_history,
    )

# -------------------------------------------------
# HR Tools
# -------------------------------------------------

HR_TOOLS = {
    "get_employee": get_employee,
    "get_department": get_department,
    "get_job": get_job,
    "get_employee_leaves": get_employee_leaves,
    "check_employee_availability": check_employee_availability,
    "get_employee_attendance": get_employee_attendance,
}

# -------------------------------------------------
# CRM Tools
# -------------------------------------------------

CRM_TOOLS = {
    "get_partner": get_partner,
    "create_partner": create_partner,
    "get_lead": get_lead,
    "update_lead_stage": update_lead_stage,
    "get_stage": get_stage,
    "get_team": get_team,
    "create_activity": create_activity,
    "get_activity": get_activity,
}

# -------------------------------------------------
# ERP Tools
# -------------------------------------------------

ERP_TOOLS = {
    "get_product": get_product,
    "get_product_stock": get_product_stock,
    "check_product_availability": check_product_availability,
    "get_stock_location": get_stock_location,
    "get_sale_order": get_sale_order,
    "get_sale_order_lines": get_sale_order_lines,
    "create_sale_order": create_sale_order,
    "get_customer_order_history": get_customer_order_history,
}

# -------------------------------------------------
# Unified Tool Registry
# -------------------------------------------------

ALL_TOOLS = {
    **HR_TOOLS,
    **CRM_TOOLS,
    **ERP_TOOLS,
}