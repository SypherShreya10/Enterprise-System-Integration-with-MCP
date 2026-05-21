# from mcp.server.fastmcp import FastMCP
# 1
from odoo_client import OdooClient
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

client = OdooClient()

installed_modules_data = client.search_read(
    model="ir.module.module",
    domain=[("state", "=", "installed")],
    fields=["name"],
    limit=100,
    apply_company_scope=False
)

INSTALLED_MODULES = {m["name"] for m in installed_modules_data}

print("Installed Modules:", INSTALLED_MODULES)

# 2.
TOOL_MODULE_MAP = {
    # CRM
    "get_lead": "crm",
    "update_lead_stage": "crm",
    "get_stage": "crm",
    "get_team": "crm",

    # HR
    "get_employee": "hr",
    "get_department": "hr",
    "get_job": "hr",
    "get_employee_leaves": "hr",
    "check_employee_availability": "hr",
    "get_employee_attendance": "hr",

    # Sales
    "get_sale_order": "sale",
    "get_sale_order_lines": "sale",
    "create_sale_order": "sale",
    "get_customer_order_history": "sale",

    # Purchase / ERP
    "get_purchase_order": "purchase",
    "get_purchase_order_lines": "purchase",
    "check_material_availability": "purchase",
    "evaluate_purchase_order": "purchase",

    # Inventory
    "get_product": "stock",
    "get_product_stock": "stock",
    "check_product_availability": "stock",
    "get_stock_location": "stock",

    # Manufacturing
    "get_manufacturing_order": "mrp",
    "check_manufacturing_capacity": "mrp",
    "get_bill_of_materials": "mrp",
    "check_manufacturing_feasibility": "mrp",
    "explode_bill_of_materials": "mrp",

    # Accounting
    "get_customer_invoices": "account",
    "check_customer_credit": "account",
    "get_payment_history": "account",

    # Mail
    "create_activity": "mail",
    "get_activity": "mail",

    # Common (always available)
    "get_user": "base",
    "get_company": "base",
    "get_partner": "base",
    "create_partner": "base",
}

# 3.
def is_tool_enabled(tool_name: str) -> bool:
    required_module = TOOL_MODULE_MAP.get(tool_name)

    if not required_module:
        return True  # no restriction

    return required_module in INSTALLED_MODULES


# 4. 
def register_tool(name, module=None, description=None):
    def wrapper(func):
        required_module = module or TOOL_MODULE_MAP.get(name)

        if required_module and required_module not in INSTALLED_MODULES:
            return func

        return mcp.tool(
            name=name,
            description=description
        )(func)

    return wrapper


from tools.crm import (
    get_partner,
    create_partner,
    get_lead,
    update_lead_stage,
    get_stage,
    get_team,
)

from tools.common import (
    get_user,
    get_company, 
)

from tools.hr import (
    get_employee,
    get_department,
    get_job,
    get_employee_leaves,
    check_employee_availability,
    get_employee_attendance,
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
    get_purchase_order,
    get_purchase_order_lines,
    check_material_availability,
    evaluate_purchase_order,

    #Manufacturing tools:
    get_manufacturing_order,
    check_manufacturing_capacity,
    get_bill_of_materials,
    check_manufacturing_feasibility,
    explode_bill_of_materials,

    #Accounting tools
    get_customer_invoices,
    check_customer_credit,
    get_payment_history,


    check_order_fulfillment_feasibility,
    analyze_customer_relationship,
)

# ------------------------------------------------------------------------------
# Create MCP server
# ------------------------------------------------------------------------------

# mcp = FastMCP(
#     name="odoo-mcp-server"
#     # resources=True
# )
from mcp_instance import mcp
import metadata_resources
_ = metadata_resources
app = FastAPI()

# ------------------------------------------------------------------------------
# Tool: section 1: tool 1 - get_partner
# ------------------------------------------------------------------------------

@register_tool(
    name="get_partner",
    description=(
        "Fetch partner (person or organization) records from Odoo.\n\n"
        "Search by partner_id, name (partial), or email (exact).\n"
        "Optional filters: is_customer, is_supplier.\n"
        "Returns a list of matching partners with safe fields only."
    ),
)
def get_partner_tool(
    partner_id: int | None = None,
    name: str | None = None,
    email: str | None = None,
    is_customer: bool | None = None,
    is_supplier: bool | None = None,
    limit: int = 10,
):
    return get_partner(
        partner_id=partner_id,
        name=name,
        email=email,
        is_customer=is_customer,
        is_supplier=is_supplier,
        limit=limit,
    )

# ------------------------------------------------------------------------------
# Tool: section 1: tool 2 - create_partner
# ------------------------------------------------------------------------------

@register_tool(
    name="create_partner",
    description=(
        "Create a new partner (contact / customer / supplier) in Odoo.\n\n"
        "Required: name.\n"
        "Optional: email, phone, address fields.\n"
        "Flags: is_customer, is_supplier.\n"
        "Company is automatically set and cannot be overridden."
    ),
)
def create_partner_tool(
    name: str,
    email: str | None = None,
    phone: str | None = None,
    is_customer: bool = False,
    is_supplier: bool = False,
    street: str | None = None,
    city: str | None = None,
    zip: str | None = None,
    country_id: int | None = None,
):
    return create_partner(
        name=name,
        email=email,
        phone=phone,
        is_customer=is_customer,
        is_supplier=is_supplier,
        street=street,
        city=city,
        zip=zip,
        country_id=country_id,
    )

# ------------------------------------------------------------------------------
# Tool: section 1: tool 3 - get_user
# ------------------------------------------------------------------------------

@register_tool(
    name="get_user",
    description=(
        "Fetch internal system users from Odoo (read-only).\n\n"
        "Use for audit and workflow routing.\n"
        "Search by user_id, login (email), or name.\n"
        "Only active internal users are returned."
    ),
)
def get_user_tool(
    user_id: int | None = None,
    login: str | None = None,
    name: str | None = None,
    limit: int = 10,
):
    return get_user(
        user_id=user_id,
        login=login,
        name=name,
        limit=limit,
    )

# ------------------------------------------------------------------------------
# Tool: section 1: tool 4 - get_company
# ------------------------------------------------------------------------------

@register_tool(
    name="get_company",
    description=(
        "Fetch current company information from Odoo.\n\n"
        "Returns company name, currency, and contact details.\n"
        "Cross-company access is forbidden."
    ),
)
def get_company_tool(
    company_id: int | None = None,
):
    return get_company(company_id=company_id)

# ------------------------------------------------------------------------------
# Tool: section 2: tool 5 - get_employee (READ)
# ------------------------------------------------------------------------------

@register_tool(
    name="get_employee",
    description=(
        "Fetch employee information from Odoo (read-only).\n\n"
        "Search by employee_id, name, department, or job role.\n"
        "Only active employees from the current company are returned.\n"
        "Sensitive personal and payroll data is strictly excluded."
    ),
)
def get_employee_tool(
    employee_id: int | None = None,
    name: str | None = None,
    department_id: int | None = None,
    job_id: int | None = None,
    limit: int = 10,
):
    """
    MCP wrapper for get_employee.
    """
    return get_employee(
        employee_id=employee_id,
        name=name,
        department_id=department_id,
        job_id=job_id,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 2: tool 6 - get_department
# ------------------------------------------------------------------

@register_tool(
    name="get_department",
    description=(
        "Fetch company department structure.\n\n"
        "Supports listing all departments or searching by name, "
        "manager, or department ID."
    ),
)
def get_department_tool(
    department_id: int | None = None,
    name: str | None = None,
    manager_id: int | None = None,
    limit: int = 100,
):
    return get_department(
        department_id=department_id,
        name=name,
        manager_id=manager_id,
        limit=limit,
    )


# ------------------------------------------------------------------
# section 2: tool 7 - get_job
# ------------------------------------------------------------------

@register_tool(
    name="get_job",
    description=(
        "Fetch job role definitions.\n\n"
        "Supports searching by job name, department, or job ID."
    ),
)
def get_job_tool(
    job_id: int | None = None,
    name: str | None = None,
    department_id: int | None = None,
    limit: int = 100,
):
    return get_job(
        job_id=job_id,
        name=name,
        department_id=department_id,
        limit=limit,
    )


# ------------------------------------------------------------------
# section 2: tool 8 - get_employee_leaves
# ------------------------------------------------------------------

@register_tool(
    name="get_employee_leaves",
    description=(
        "Fetch approved employee leaves for availability planning.\n\n"
        "Only approved (validated) leaves are returned."
    ),
)
def get_employee_leaves_tool(
    employee_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 100,
):
    return get_employee_leaves(
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )

#section 2: tool 9 - check employee availability
@register_tool(
    name="check_employee_availability",
    description=(
        "Check if a specific employee is available within a date range.\n\n"
        "This is a composite read-only tool that verifies:\n"
        "- Employee exists and is active\n"
        "- Approved leaves overlapping the date range\n\n"
        "Returns availability summary including conflicting leave dates."
    ),
)
def check_employee_availability_tool(
    employee_id: int,
    date_from: str,
    date_to: str,
):
    return check_employee_availability(
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
    )

#section 2: tool 10 - get_employee attendance
@register_tool(
    name="get_employee_attendance",
    description=(
        "Fetch employee attendance (clock-in / clock-out) records.\n\n"
        "Supports filtering by employee and/or date.\n"
        "Used for workforce visibility and attendance checks."
    ),
)
def get_employee_attendance_tool(
    employee_id: int | None = None,
    date_filter: str | None = None,
    limit: int = 100,
):
    return get_employee_attendance(
        employee_id=employee_id,
        date_filter=date_filter,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 3: tool 11 - get_lead
# ------------------------------------------------------------------
@register_tool(
    name="get_lead",
    description=(
        "Fetch CRM leads or opportunities from Odoo (read-only).\n\n"
        "Supports filtering by lead_id, partner, stage, assigned user, "
        "or type ('lead' / 'opportunity').\n"
        "Only active, company-scoped records are returned."
    ),
)
def get_lead_tool(
    lead_id: int | None = None,
    partner_id: int | None = None,
    stage_id: int | None = None,
    user_id: int | None = None,
    type: str | None = None,
    limit: int = 10,
):
    return get_lead(
        lead_id=lead_id,
        partner_id=partner_id,
        stage_id=stage_id,
        user_id=user_id,
        type=type,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 3: tool 12 - update_lead_stage (HIGH RISK)
# ------------------------------------------------------------------

@register_tool(
    name="update_lead_stage",
    description=(
        "Move a CRM lead or opportunity to a new pipeline stage.\n\n"
        "HIGH RISK: This is the ONLY update operation allowed.\n"
        "Updates stage_id only. Lead must exist and be active.\n"
        "Company scoping and write constraints are enforced automatically."
    ),
)
def update_lead_stage_tool(
    lead_id: int,
    stage_id: int,
):
    return update_lead_stage(
        lead_id=lead_id,
        stage_id=stage_id,
    )

# ------------------------------------------------------------------
# section 3: tool 13 - get_stage
# ------------------------------------------------------------------

@register_tool(
    name="get_stage",
    description=(
        "Fetch CRM sales pipeline stages.\n\n"
        "Use this to understand the pipeline structure, stage order, "
        "and identify won/lost stages.\n"
        "Read-only reference data."
    ),
)
def get_stage_tool(
    stage_id: int | None = None,
    name: str | None = None,
    is_won: bool | None = None,
    limit: int = 100,
):
    return get_stage(
        stage_id=stage_id,
        name=name,
        is_won=is_won,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 3: tool 14 - get_team
# ------------------------------------------------------------------

@register_tool(
    name="get_team",
    description=(
        "Fetch CRM sales team information.\n\n"
        "Use this to understand sales team structure, team leaders, "
        "and members.\n"
        "Company-scoped, read-only reference data."
    ),
)
def get_team_tool(
    team_id: int | None = None,
    name: str | None = None,
    user_id: int | None = None,
    limit: int = 100,
):
    return get_team(
        team_id=team_id,
        name=name,
        user_id=user_id,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 3: tool 15 - create_activity
# ------------------------------------------------------------------

@register_tool(
    name="create_activity",
    description=(
        "Create a follow-up activity (call, meeting, reminder).\n\n"
        "Requires activity_type_id, assigned user, deadline, "
        "and related record (res_model, res_id).\n"
        "Create-only operation."
    ),
)
def create_activity_tool(
    activity_type_id: int,
    user_id: int,
    date_deadline: str,
    res_model: str,
    res_id: int,
    summary: str | None = None,
    note: str | None = None,
):
    return create_activity(
        activity_type_id=activity_type_id,
        user_id=user_id,
        date_deadline=date_deadline,
        res_model=res_model,
        res_id=res_id,
        summary=summary,
        note=note,
    )

# ------------------------------------------------------------------
# section 3: tool 16 - get_activity
# ------------------------------------------------------------------

@register_tool(
    name="get_activity",
    description=(
        "Fetch scheduled activities.\n\n"
        "Filter by assigned user, model, due date, or state.\n"
        "At least one filter is required."
    ),
)
def get_activity_tool(
    user_id: int | None = None,
    res_model: str | None = None,
    date_deadline: str | None = None,
    state: str | None = None,
    limit: int = 100,
):
    return get_activity(
        user_id=user_id,
        res_model=res_model,
        date_deadline=date_deadline,
        state=state,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 4: tool 17 - get_product
# ------------------------------------------------------------------

@register_tool(
    name="get_product",
    description=(
        "Fetch sellable product details from Odoo.\n\n"
        "Search by product_id, name, SKU (default_code), category, or type.\n"
        "Only active, sale-enabled products are returned.\n"
        "Cost fields are excluded."
    ),
)
def get_product_tool(
    product_id: int | None = None,
    name: str | None = None,
    default_code: str | None = None,
    categ_id: int | None = None,
    type: str | None = None,
    limit: int = 10,
):
    return get_product(
        product_id=product_id,
        name=name,
        default_code=default_code,
        categ_id=categ_id,
        type=type,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 4: tool 18 - get_product_stock
# ------------------------------------------------------------------

@register_tool(
    name="get_product_stock",
    description=(
        "Check inventory quantity for a product.\n\n"
        "Returns total quantity, reserved quantity, "
        "available quantity, and warehouse breakdown.\n"
        "Internal warehouse locations only."
    ),
)
def get_product_stock_tool(
    product_id: int,
    location_id: int | None = None,
):
    return get_product_stock(
        product_id=product_id,
        location_id=location_id,
    )

# ------------------------------------------------------------------
# section 4: tool 19 - check_product_availability
# ------------------------------------------------------------------

@register_tool(
    name="check_product_availability",
    description=(
        "Check whether requested quantity of a product can be fulfilled.\n\n"
        "Composite tool combining:\n"
        "- Current stock (stock.quant)\n"
        "- Reserved quantities\n"
        "- Incoming purchase orders (optional if date provided)\n\n"
        "Use case:\n"
        "'Can we deliver 200 units by Dec 15?'\n"
        "'Do we have enough stock for this order?'\n\n"
        "Returns stock breakdown, shortage (if any), and recommended action."
    ),
)
def check_product_availability_tool(
    product_id: int,
    quantity: float,
    date_required: str | None = None,
):
    return check_product_availability(
        product_id=product_id,
        quantity=quantity,
        date_required=date_required,
    )

# ------------------------------------------------------------------
# section 4: tool 20 - get_stock_location
# ------------------------------------------------------------------

@register_tool(
    name="get_stock_location",
    description=(
        "Fetch internal warehouse / stock location information.\n\n"
        "Supports:\n"
        "- Listing all internal warehouse locations\n"
        "- Filtering by location_id\n"
        "- Searching by partial location name\n\n"
        "Only internal company locations are returned.\n"
        "Customer, supplier, and transit locations are excluded."
    ),
)
def get_stock_location_tool(
    location_id: int | None = None,
    name: str | None = None,
    limit: int = 50,
):
    return get_stock_location(
        location_id=location_id,
        name=name,
        limit=limit,
    )


# ------------------------------------------------------------------
# section 5: tool 21 - get_sale_order
# ------------------------------------------------------------------

@register_tool(
    name="get_sale_order",
    description=(
        "Fetch sales orders from Odoo (read-only).\n\n"
        "Supports filtering by order_id, name, customer, state, "
        "or date range.\n"
        "At least one filter is required.\n"
        "Company-scoped automatically."
    ),
)
def get_sale_order_tool(
    order_id: int | None = None,
    name: str | None = None,
    partner_id: int | None = None,
    state: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 10,
):
    return get_sale_order(
        order_id=order_id,
        name=name,
        partner_id=partner_id,
        state=state,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 5: tool 22 - get_sale_order_lines
# ------------------------------------------------------------------

@register_tool(
    name="get_sale_order_lines",
    description=(
        "Fetch line items of a specific sales order.\n\n"
        "Requires order_id.\n"
        "Returns product details, quantity, price, and totals.\n"
        "Company-scoped automatically."
    ),
)
def get_sale_order_lines_tool(
    order_id: int,
    limit: int = 100,
):
    return get_sale_order_lines(
        order_id=order_id,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 5: tool 23 - create_sale_order (WRITE)
# ------------------------------------------------------------------

@register_tool(
    name="create_sale_order",
    description=(
        "Create a new sales order in Odoo.\n\n"
        "Creates order in draft state only.\n"
        "Price is derived from product list_price.\n"
        "Manual price override is not allowed.\n\n"
        "Validates:\n"
        "- Customer exists and is active\n"
        "- Products are sellable and active\n"
        "- Quantity is positive\n"
        "- No duplicate products\n"
        "- Date formats are correct\n"
        "- validity_date cannot be before date_order\n\n"
        "Returns order summary and line breakdown.\n"
        "Human confirmation is required before processing."
    ),
)
def create_sale_order_tool(
    partner_id: int,
    order_lines: list,
    date_order: str | None = None,
    validity_date: str | None = None,
    client_order_ref: str | None = None,
):
    return create_sale_order(
        partner_id=partner_id,
        order_lines=order_lines,
        date_order=date_order,
        validity_date=validity_date,
        client_order_ref=client_order_ref,
    )

# ------------------------------------------------------------------
# section 5: tool 24 - get_customer_order_history
# ------------------------------------------------------------------

@register_tool(
    name="get_customer_order_history",
    description=(
        "Fetch full sales history for a specific customer.\n\n"
        "Returns paginated order list (latest 100 max) and accurate\n"
        "analytics including total orders, revenue (confirmed only),\n"
        "average order value, most recent order dates, and state breakdown.\n\n"
        "Requires partner_id (must be a valid customer).\n"
        "Company-scoped automatically."
    ),
)
def get_customer_order_history_tool(
    partner_id: int,
):
    return get_customer_order_history(
        partner_id=partner_id,
    )

# ------------------------------------------------------------------
# section 6: tool 25 - get_purchase_order
# ------------------------------------------------------------------

@register_tool(
    name="get_purchase_order",
    description=(
        "Fetch purchase orders from Odoo (read-only).\n\n"
        "Supports filtering by order_id, supplier (partner_id), "
        "state, or expected delivery date range.\n"
        "At least one filter is required.\n"
        "Company-scoped automatically."
    ),
)
def get_purchase_order_tool(
    order_id: int | None = None,
    partner_id: int | None = None,
    state: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 10,
):
    return get_purchase_order(
        order_id=order_id,
        partner_id=partner_id,
        state=state,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 6: tool 26 - get_purchase_order_lines
# ------------------------------------------------------------------

@register_tool(
    name="get_purchase_order_lines",
    description=(
        "Fetch line items of a specific purchase order.\n\n"
        "Requires order_id.\n"
        "Returns product details, quantity ordered, price, "
        "and expected delivery date.\n"
        "Company-scoped automatically."
    ),
)
def get_purchase_order_lines_tool(
    order_id: int,
    limit: int = 100,
):
    return get_purchase_order_lines(
        order_id=order_id,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 6: tool 27 - check_material_availability
# ------------------------------------------------------------------

@register_tool(
    name="check_material_availability",
    description=(
        "Check if required raw materials are available for manufacturing.\n\n"
        "Composite tool combining:\n"
        "- Current stock levels (stock.quant)\n"
        "- Incoming approved purchase orders (purchase.order.line)\n\n"
        "Returns stock availability summary including:\n"
        "current_stock, incoming_qty, total_available, shortage,\n"
        "and expected_available_date if supply is insufficient.\n\n"
        "Use cases:\n"
        "'Do we have enough raw materials to manufacture 100 units?'\n"
        "'When will materials be available for production?'"
    ),
)
def check_material_availability_tool(
    product_id: int,
    quantity_needed: float,
    date_needed: str | None = None,
):
    return check_material_availability(
        product_id=product_id,
        quantity_needed=quantity_needed,
        date_needed=date_needed,
    )

# ------------------------------------------------------------------
# section 7: tool 28 - get_manufacturing_order
# ------------------------------------------------------------------

@register_tool(
    name="get_manufacturing_order",
    description=(
        "Fetch manufacturing orders from Odoo (read-only).\n\n"
        "Supports filtering by production_id, product_id, state, "
        "or production start date range.\n"
        "Returns manufacturing progress including produced and remaining quantity."
    ),
)
def get_manufacturing_order_tool(
    production_id: int | None = None,
    product_id: int | None = None,
    state: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 10,
):
    return get_manufacturing_order(
        production_id=production_id,
        product_id=product_id,
        state=state,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 7: tool 29 - check_manufacturing_capacity
# ------------------------------------------------------------------

@register_tool(
    name="check_manufacturing_capacity",
    description=(
        "Analyze manufacturing workload within a date range.\n\n"
        "Calculates total scheduled production quantity and "
        "compares it against theoretical capacity.\n\n"
        "Returns capacity usage percentage and available capacity."
    ),
)
def check_manufacturing_capacity_tool(
    date_from: str,
    date_to: str,
    theoretical_capacity: float | None = None,
):
    return check_manufacturing_capacity(
        date_from=date_from,
        date_to=date_to,
        theoretical_capacity=theoretical_capacity,
    )

# ------------------------------------------------------------------
# section 7: tool 30 - get_bill_of_materials
# ------------------------------------------------------------------

@register_tool(
    name="get_bill_of_materials",
    description=(
        "Fetch Bill of Materials (BOM) for a product.\n\n"
        "Returns the BOM structure including component products "
        "and required quantities per unit of the finished product.\n\n"
        "Used for manufacturing planning and material analysis."
    ),
)
def get_bill_of_materials_tool(
    product_id: int,
):
    return get_bill_of_materials(
        product_id=product_id,
    )

# ------------------------------------------------------------------
# section 7: tool 31 - check_manufacturing_feasibility
# ------------------------------------------------------------------

@register_tool(
    name="check_manufacturing_feasibility",
    description=(
        "Evaluate whether a product can be manufactured.\n\n"
        "Combines:\n"
        "- Bill of Materials analysis\n"
        "- Raw material availability\n"
        "- Manufacturing capacity\n\n"
        "Returns feasibility status, blocking components, "
        "maximum producible quantity, and capacity constraints."
    ),
)
def check_manufacturing_feasibility_tool(
    product_id: int,
    quantity: float,
    date_needed: str | None = None,
    theoretical_capacity: float | None = None,
):
    return check_manufacturing_feasibility(
        product_id=product_id,
        quantity=quantity,
        date_needed=date_needed,
        theoretical_capacity=theoretical_capacity,
    )

# ------------------------------------------------------------------
# section 7: tool 32 - explode_bill_of_materials
# ------------------------------------------------------------------

@register_tool(
    name="explode_bill_of_materials",
    description=(
        "Recursively expand a Bill of Materials.\n\n"
        "Breaks down a product into all required base components.\n"
        "Supports recursive multi-level BOMs.\n\n"
        "Useful for material planning and cost estimation."
    ),
)
def explode_bill_of_materials_tool(
    product_id: int,
    quantity: float = 1,
    depth: int = 5,
):
    return explode_bill_of_materials(
        product_id=product_id,
        quantity=quantity,
        depth=depth,
    )

# ------------------------------------------------------------------
# section 8: tool 33 - get_customer_invoices
# ------------------------------------------------------------------

@register_tool(
    name="get_customer_invoices",
    description=(
        "Fetch customer invoices or refunds from Odoo.\n\n"
        "Supports filtering by customer, payment status, invoice type, "
        "or invoice date range.\n"
        "Cancelled invoices are excluded.\n"
        "At least one filter must be provided."
    ),
)
def get_customer_invoices_tool(
    partner_id: int | None = None,
    move_type: str | None = None,
    payment_state: str | None = None,
    invoice_date_from: str | None = None,
    invoice_date_to: str | None = None,
    limit: int = 20,
):
    return get_customer_invoices(
        partner_id=partner_id,
        move_type=move_type,
        payment_state=payment_state,
        invoice_date_from=invoice_date_from,
        invoice_date_to=invoice_date_to,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 8: tool 34 - check_customer_credit
# ------------------------------------------------------------------

@register_tool(
    name="check_customer_credit",
    description=(
        "Evaluate the credit position of a customer.\n\n"
        "Calculates outstanding invoice balance, credit limit, "
        "available credit, and overdue invoices.\n\n"
        "Used before confirming large sales orders."
    ),
)
def check_customer_credit_tool(
    partner_id: int,
):
    return check_customer_credit(
        partner_id=partner_id,
    )

# ------------------------------------------------------------------
# section 8: tool 35 - get_payment_history
# ------------------------------------------------------------------

@register_tool(
    name="get_payment_history",
    description=(
        "Fetch paid invoice history for a customer.\n\n"
        "Provides a view of historical payments including "
        "invoice dates, due dates, and payment terms.\n\n"
        "Includes analytics such as total payments and payment profile."
    ),
)
def get_payment_history_tool(
    partner_id: int,
    limit: int = 50,
):
    return get_payment_history(
        partner_id=partner_id,
        limit=limit,
    )

# ------------------------------------------------------------------
# section 9: tool 36 - check_order_fulfillment_feasibility
# ------------------------------------------------------------------

@register_tool("check_order_fulfillment_feasibility", "sale")
def check_order_fulfillment_feasibility_tool(
    partner_id: int,
    product_id: int,
    quantity: float,
    date_required: str,
):
    return check_order_fulfillment_feasibility(
        partner_id=partner_id,
        product_id=product_id,
        quantity=quantity,
        date_required=date_required,
    )


# ------------------------------------------------------------------
# section 9: tool 37 - analyze_customer_relationship
# ------------------------------------------------------------------

@register_tool("analyze_customer_relationship", "crm")
def analyze_customer_relationship_tool(
    partner_id: int,
):
    return analyze_customer_relationship(
        partner_id=partner_id,
    )


# tool 38: evaluate_purchase_order
@register_tool(
    name="evaluate_purchase_order",
    description=(
        "Evaluate whether a purchase order should be approved.\n\n"
        "This is a decision-support tool (read-only).\n\n"
        "It analyzes:\n"
        "- Purchase order amount vs approval policy\n"
        "- Current PO state\n"
        "- Material availability (stock vs required)\n\n"
        "Returns:\n"
        "- Whether the PO can be approved\n"
        "- Detailed conditions and reasoning\n"
        "- Recommendation for the user\n\n"
        "IMPORTANT: This tool does NOT approve the PO.\n"
        "User must manually approve in Odoo."
    ),
)
def evaluate_purchase_order_tool(
    order_id: int,
):
    return evaluate_purchase_order(
        order_id=order_id,
    )

# ------------------------------------------------------------------------------
# Server entry point
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()


# ------------------------------------------------------------------------------
# Odoo Webhook Endpoint
# ------------------------------------------------------------------------------

@app.post("/webhook/odoo")
async def odoo_webhook(request: Request):

    payload = await request.json()

    print("Webhook received:", payload)

    return JSONResponse(
        content={
            "status": "received"
        }
    )