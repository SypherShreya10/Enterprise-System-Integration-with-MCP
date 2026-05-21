# from mcp.server.fastmcp import FastMCP
from typing import Dict, Any
from odoo_client import OdooClient
from mcp_instance import mcp
from typing import Optional
from typing import Set

# mcp = FastMCP()

print("LOADING metadata_resources")

# ---------------------------------------------------------------------------
# FIX 1: Singleton client — one authentication per server lifecycle,
#         not one per resource call. Avoids N×2 Odoo round-trips.
# ---------------------------------------------------------------------------
_client: Optional[OdooClient] = None

def _get_client() -> OdooClient:
    global _client
    if _client is None:
        _client = OdooClient()
    return _client


# ---------------------------------------------------------------------------
# FIX 2: Allowlist — mirrors ai_safety_execution_notes.md.
#         get_schema and get_access both check this before any Odoo call.
# ---------------------------------------------------------------------------
ALLOWED_MODELS: Set[str] = {
    "res.partner", "res.users", "res.company", "res.groups",
    "hr.employee", "hr.department", "hr.job", "hr.attendance", "hr.leave",
    "crm.lead", "crm.stage", "crm.team",
    "mail.activity",
    "product.product", "product.template",
    "stock.quant", "stock.location", "stock.move",
    "sale.order", "sale.order.line",
    "purchase.order", "purchase.order.line",
    "mrp.production", "mrp.bom",
    "account.move", "account.payment",
    "hr.contract.type",
    "hr.leave.type",
}

# ---------------------------------------------------------------------------
# FIX 3: Internal field prefixes to strip from schema responses.
#         Keeps LLM context clean — no UI noise, no computed display fields.
# ---------------------------------------------------------------------------
_INTERNAL_PREFIXES = ("__", "message_", "website_", "activity_")


# =========================================================
# RESOURCE 1: SCHEMA
# =========================================================

@mcp.resource("odoo://schema/{model_name}")
def get_schema(model_name: str) -> Dict[str, Any]:
    try:
        # FIX 2 applied: allowlist guard before any Odoo call
        if model_name not in ALLOWED_MODELS:
            return {
                "error": f"Model '{model_name}' is not in the introspection allowlist.",
                "model": model_name,
            }

        # FIX 1 applied: reuse singleton client
        client = _get_client()

        raw_fields = client.models.execute_kw(
            client.db,
            client.uid,
            client.password,
            model_name,
            "fields_get",
            [],
            {
                # FIX 3 applied: request only the attributes we need,
                # reducing payload size from Odoo significantly
                "attributes": [
                    "string", "type", "required",
                    "readonly", "selection", "relation", "help",
                ]
            }
        )

        # FIX 3 applied: strip internal/UI-only fields
        filtered_fields = {
            name: {
                "label": f.get("string", name),
                "type": f.get("type"),
                "required": f.get("required", False),
                "readonly": f.get("readonly", False),
                "selection": f.get("selection") if f.get("type") == "selection" else None,
                "relation": f.get("relation"),
            }
            for name, f in raw_fields.items()
            if not any(name.startswith(p) for p in _INTERNAL_PREFIXES)
            # Also skip readonly one2many fields — purely display, LLM never writes these
            and not (f.get("readonly") and f.get("type") == "one2many")
        }

        return {
            "model": model_name,
            "field_count": len(filtered_fields),
            "fields": filtered_fields,
        }

    except Exception as exc:
        return {"error": str(exc), "model": model_name}

print("Registered: schema")


# =========================================================
# RESOURCE 2: CAPABILITIES
# =========================================================

@mcp.resource("odoo://capabilities")
def get_capabilities() -> Dict[str, Any]:
    try:
        # FIX 1 applied: singleton client
        client = _get_client()

        # FIX 4 applied: raised limit to 500 to capture all installed modules.
        # Also filter to only modules relevant to your tool domains so the
        # LLM does not receive a dump of 300+ Odoo internal modules.
        RELEVANT_MODULES = {
            "base", "mail", "crm", "sale", "sale_management",
            "purchase", "stock", "mrp", "account", "hr",
            "hr_attendance", "hr_holidays",
        }

        modules = client.search_read(
            model="ir.module.module",
            domain=[
                ("state", "=", "installed"),
                ("name", "in", list(RELEVANT_MODULES))
            ],
            fields=["name", "shortdesc"],
            limit=500,
            apply_company_scope=False,
        )

        # Filter to only the modules your tools cover
        relevant = [
            m for m in modules if m["name"] in RELEVANT_MODULES
        ]

        return {
            "installed_modules": [m["name"] for m in relevant],
            "count": len(relevant),
            # Also surface the full list so dynamic tools/list in server.py
            # can use it if needed
            "all_installed_count": len(modules),
        }

    except Exception as exc:
        return {"error": str(exc)}

print("Registered: capabilities")


# =========================================================
# RESOURCE 3: ACCESS
# =========================================================

@mcp.resource("odoo://access/{model_name}")
def get_access(model_name: str) -> Dict[str, Any]:
    try:
        # FIX 2 applied: allowlist guard
        if model_name not in ALLOWED_MODELS:
            return {
                "error": f"Model '{model_name}' is not in the introspection allowlist.",
                "model": model_name,
            }

        # FIX 1 applied: singleton client
        client = _get_client()

        # FIX 5 applied: check actual permissions for the CURRENT USER
        # using check_access_rights, not aggregating across all groups.
        # check_access_rights returns True/False for the authenticated uid.
        permissions = {}
        for operation in ("read", "write", "create", "unlink"):
            try:
                result = client.models.execute_kw(
                    client.db,
                    client.uid,
                    client.password,
                    model_name,
                    "check_access_rights",
                    [operation],
                    {"raise_exception": False},
                )
                permissions[operation if operation != "unlink" else "delete"] = bool(result)
            except Exception:
                permissions[operation if operation != "unlink" else "delete"] = False

        return {
            "model": model_name,
            "permissions": permissions,
            # Surface the user context so the LLM knows whose permissions these are
            # "checked_for_uid": client.uid,
            "user_context": "authenticated_user",
            "company_id": client.company_id,
        }

    except Exception as exc:
        return {"error": str(exc)}

print("Registered: access")


# =========================================================
# RESOURCE 4: POLICIES
# =========================================================

@mcp.resource("odoo://policies/{domain}")
def get_policies(domain: str) -> Dict[str, Any]:

    result = {}

    try:
        # FIX 1 applied: singleton client
        client = _get_client()

        if domain == "sales":
            # FIX 6 applied: removed per-customer credit limits — that is a
            # data leak and belongs in check_customer_credit tool, not here.
            # Policy resource returns company-level credit settings only.
            company = client.search_read(
                model="res.company",
                domain=[("id", "=", client.company_id)],
                fields=["name", "currency_id"],
                limit=1,
                apply_company_scope=False,
            )

            result["company"] = company[0] if company else {}
            result["note"] = (
                "Individual customer credit limits are fetched per-customer "
                "via the check_customer_credit tool, not exposed here as policy."
            )

        elif domain == "purchase":
            # FIX 8 applied: wrapped in try/except for Odoo version compatibility.
            # po_double_validation moved from res.company in Odoo 16+.
            try:
                company = client.search_read(
                    model="res.company",
                    domain=[("id", "=", client.company_id)],
                    fields=[
                        "po_double_validation",
                        "po_double_validation_amount",
                    ],
                    limit=1,
                    apply_company_scope=False,
                )

                if company:
                    validation_type = company[0].get("po_double_validation")
                    result["approval_policy"] = validation_type
                    result["approval_required"] = validation_type != "one_step"
                    result["threshold_active"] = validation_type not in ("one_step", None)
                    result["approval_threshold"] = company[0].get("po_double_validation_amount")
                else:
                    result["approval_policy"] = None
                    result["approval_required"] = None
                    result["approval_threshold"] = None
                    result["note"] = (
                        "Purchase approval configuration not available — "
                        "check Settings > Purchase manually."
                    )

            except Exception:
                result["approval_policy"] = None
                result["note"] = (
                    "Purchase approval configuration not available in this "
                    "Odoo version — check Settings > Purchase manually."
                )

        elif domain == "hr":
            # FIX 7 applied: replaced meaningless domain [('id', '!=', 0)]
            # with [('active', '=', True)] and added apply_company_scope=False
            # since hr.leave.type is global in some Odoo versions.
            leave_types = client.search_read(
                model="hr.leave.type",
                domain=[("active", "=", True)],
                fields=[
                    "name",
                    "requires_allocation",
                    "leave_validation_type",
                ],
                limit=50,
                apply_company_scope=False,
            )

            result["leave_policies"] = leave_types
            result["leave_type_count"] = len(leave_types)

        else:
            result["error"] = (
                f"Unknown policy domain '{domain}'. "
                "Supported domains: 'sales', 'purchase', 'hr'."
            )

        return result

    except Exception as exc:
        return {"error": str(exc)}

print("Registered: policies")