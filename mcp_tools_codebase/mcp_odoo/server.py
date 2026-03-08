from mcp.server.fastmcp import FastMCP
from security.secure_tool import secure_tool

from mcp_odoo.tools.crm import (
    get_partner,
    create_partner,
    get_lead,
    update_lead_stage,
    get_stage,
    get_team,
)
from mcp_odoo.tools.common import (
    get_user,
    get_company, 
)

from mcp_odoo.tools.hr import (
    get_employee,
    get_department,
    get_job,
    get_employee_leaves,
    check_employee_availability,
    get_employee_attendance,
)

from mcp_odoo.tools.mail import (
    create_activity,
    get_activity,
)

from mcp_odoo.tools.erp import (
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
)

# ------------------------------------------------------------------------------
# Create MCP server
# ------------------------------------------------------------------------------

mcp = FastMCP(
    name="odoo-mcp-server",
)

# ------------------------------------------------------------------------------
# Tool: section 1: tool 1 - get_partner
# ------------------------------------------------------------------------------

@mcp.tool(
    name="get_partner",
    description=(
        "Fetch partner (person or organization) records from Odoo.\n\n"
        "Search by partner_id, name (partial), or email (exact).\n"
        "Optional filters: is_customer, is_supplier.\n"
        "Returns a list of matching partners with safe fields only."
    ),
)
@secure_tool("get_partner")
def get_partner_tool(
    token: str,
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

@mcp.tool(
    name="create_partner",
    description=(
        "Create a new partner (contact / customer / supplier) in Odoo.\n\n"
        "Required: name.\n"
        "Optional: email, phone, address fields.\n"
        "Flags: is_customer, is_supplier.\n"
        "Company is automatically set and cannot be overridden."
    ),
)
@secure_tool("create_partner")
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

@mcp.tool(
    name="get_user",
    description=(
        "Fetch internal system users from Odoo (read-only).\n\n"
        "Use for audit and workflow routing.\n"
        "Search by user_id, login (email), or name.\n"
        "Only active internal users are returned."
    ),
)
@secure_tool("get_user")
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

@mcp.tool(
    name="get_company",
    description=(
        "Fetch current company information from Odoo.\n\n"
        "Returns company name, currency, and contact details.\n"
        "Cross-company access is forbidden."
    ),
)
@secure_tool("get_company")
def get_company_tool(
    company_id: int | None = None,
):
    return get_company(company_id=company_id)

# ------------------------------------------------------------------------------
# Tool: section 2: tool 5 - get_employee (READ)
# ------------------------------------------------------------------------------

@mcp.tool(
    name="get_employee",
    description=(
        "Fetch employee information from Odoo (read-only).\n\n"
        "Search by employee_id, name, department, or job role.\n"
        "Only active employees from the current company are returned.\n"
        "Sensitive personal and payroll data is strictly excluded."
    ),
)
@secure_tool("get_employee")
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

@mcp.tool(
    name="get_department",
    description=(
        "Fetch company department structure.\n\n"
        "Supports listing all departments or searching by name, "
        "manager, or department ID."
    ),
)
@secure_tool("get_department")
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

@mcp.tool(
    name="get_job",
    description=(
        "Fetch job role definitions.\n\n"
        "Supports searching by job name, department, or job ID."
    ),
)
@secure_tool("get_job")
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

@mcp.tool(
    name="get_employee_leaves",
    description=(
        "Fetch approved employee leaves for availability planning.\n\n"
        "Only approved (validated) leaves are returned."
    ),
)
@secure_tool("get_employee_leaves")
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
@mcp.tool(
    name="check_employee_availability",
    description=(
        "Check if a specific employee is available within a date range.\n\n"
        "This is a composite read-only tool that verifies:\n"
        "- Employee exists and is active\n"
        "- Approved leaves overlapping the date range\n\n"
        "Returns availability summary including conflicting leave dates."
    ),
)
@secure_tool("check_employee_availability")
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
@mcp.tool(
    name="get_employee_attendance",
    description=(
        "Fetch employee attendance (clock-in / clock-out) records.\n\n"
        "Supports filtering by employee and/or date.\n"
        "Used for workforce visibility and attendance checks."
    ),
)
@secure_tool("get_employee_attendance")
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
@mcp.tool(
    name="get_lead",
    description=(
        "Fetch CRM leads or opportunities from Odoo (read-only).\n\n"
        "Supports filtering by lead_id, partner, stage, assigned user, "
        "or type ('lead' / 'opportunity').\n"
        "Only active, company-scoped records are returned."
    ),
)
@secure_tool("get_lead")
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

@mcp.tool(
    name="update_lead_stage",
    description=(
        "Move a CRM lead or opportunity to a new pipeline stage.\n\n"
        "HIGH RISK: This is the ONLY update operation allowed.\n"
        "Updates stage_id only. Lead must exist and be active.\n"
        "Company scoping and write constraints are enforced automatically."
    ),
)
@secure_tool("update_lead_stage")
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

@mcp.tool(
    name="get_stage",
    description=(
        "Fetch CRM sales pipeline stages.\n\n"
        "Use this to understand the pipeline structure, stage order, "
        "and identify won/lost stages.\n"
        "Read-only reference data."
    ),
)
@secure_tool("get_stage")
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

@mcp.tool(
    name="get_team",
    description=(
        "Fetch CRM sales team information.\n\n"
        "Use this to understand sales team structure, team leaders, "
        "and members.\n"
        "Company-scoped, read-only reference data."
    ),
)
@secure_tool("get_team")
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

@mcp.tool(
    name="create_activity",
    description=(
        "Create a follow-up activity (call, meeting, reminder).\n\n"
        "Requires activity_type_id, assigned user, deadline, "
        "and related record (res_model, res_id).\n"
        "Create-only operation."
    ),
)
@secure_tool("create_activity")
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

@mcp.tool(
    name="get_activity",
    description=(
        "Fetch scheduled activities.\n\n"
        "Filter by assigned user, model, due date, or state.\n"
        "At least one filter is required."
    ),
)
@secure_tool("get_activity")
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

@mcp.tool(
    name="get_product",
    description=(
        "Fetch sellable product details from Odoo.\n\n"
        "Search by product_id, name, SKU (default_code), category, or type.\n"
        "Only active, sale-enabled products are returned.\n"
        "Cost fields are excluded."
    ),
)
@secure_tool("get_product")
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

@mcp.tool(
    name="get_product_stock",
    description=(
        "Check inventory quantity for a product.\n\n"
        "Returns total quantity, reserved quantity, "
        "available quantity, and warehouse breakdown.\n"
        "Internal warehouse locations only."
    ),
)
@secure_tool("get_product_stock")
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

@mcp.tool(
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
@secure_tool("check_product_availability")
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

@mcp.tool(
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
@secure_tool("get_stock_location")
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

@mcp.tool(
    name="get_sale_order",
    description=(
        "Fetch sales orders from Odoo (read-only).\n\n"
        "Supports filtering by order_id, name, customer, state, "
        "or date range.\n"
        "At least one filter is required.\n"
        "Company-scoped automatically."
    ),
)
@secure_tool("get_sale_order")
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

@mcp.tool(
    name="get_sale_order_lines",
    description=(
        "Fetch line items of a specific sales order.\n\n"
        "Requires order_id.\n"
        "Returns product details, quantity, price, and totals.\n"
        "Company-scoped automatically."
    ),
)
@secure_tool("get_sale_order_lines")
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

@mcp.tool(
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
@secure_tool("create_sale_order")
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

@mcp.tool(
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
@secure_tool("get_customer_order_history")
def get_customer_order_history_tool(
    partner_id: int,
):
    return get_customer_order_history(
        partner_id=partner_id,
    )

# ------------------------------------------------------------------
# section 6: tool 25 - get_purchase_order
# ------------------------------------------------------------------

@mcp.tool(
    name="get_purchase_order",
    description=(
        "Fetch purchase orders from Odoo (read-only).\n\n"
        "Supports filtering by order_id, supplier (partner_id), "
        "state, or expected delivery date range.\n"
        "At least one filter is required.\n"
        "Company-scoped automatically."
    ),
)
@secure_tool("get_purchase_order")
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

@mcp.tool(
    name="get_purchase_order_lines",
    description=(
        "Fetch line items of a specific purchase order.\n\n"
        "Requires order_id.\n"
        "Returns product details, quantity ordered, price, "
        "and expected delivery date.\n"
        "Company-scoped automatically."
    ),
)
@secure_tool("get_purchase_order_lines")
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

@mcp.tool(
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
@secure_tool("check_material_availability")
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

# ------------------------------------------------------------------------------
# Server entry point
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
