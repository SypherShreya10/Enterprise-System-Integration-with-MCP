from typing import Dict, Any, List
from odoo_client import OdooClient

# ---------------------------------------------------------------------------
# Fields that must NEVER be written — Odoo manages these automatically.
# ---------------------------------------------------------------------------
FORBIDDEN_FIELDS = {
    "create_uid",
    "create_date",
    "write_uid",
    "write_date",
    "__last_update",
    "message_ids",
    "activity_ids",
    "id",
}

AUTO_MANAGED_FIELDS = {
    "company_id",
    "active",
}

# ---------------------------------------------------------------------------
# Per-model uniqueness rules.
# Each entry: field_name → include_archived (True = also check inactive records)
# Only models/fields where Odoo enforces or business logic requires uniqueness.
# ---------------------------------------------------------------------------
MODEL_UNIQUE_FIELDS: Dict[str, Dict[str, bool]] = {
    "res.partner":   {"email": True},
    "hr.employee":   {"work_email": True},
    "res.users":     {"login": True},
    "product.product": {"default_code": False},  # SKU — archived products keep their code
}

def validate_write_payload(
    client: OdooClient,
    model_name: str,
    values: Dict[str, Any],
    operation: str = "create",
) -> Dict[str, Any]:
    """
    Run five validation gates before any create or write reaches Odoo.

    Gates:
        1. ACL — does this user have permission for this operation?
        2. Required fields — are all mandatory fields present?
        3. Value validation — are types and selection values correct?
        4. Uniqueness pre-flight — would this create a duplicate?
        5. Payload sanitisation — strip readonly and forbidden fields.

    Returns:
        {"valid": True,  "cleaned_values": {...}}   on success
        {"valid": False, "errors": [...]}            on failure

    The caller should check "valid" before calling client.create() or client.write().
    If valid, use "cleaned_values" as the payload — not the original values dict.
    """

    errors: List[str] = []
    cleaned_values: Dict[str, Any] = {}

    # =========================================================================
    # GATE 1 — ACL CHECK
    # Ask Odoo directly whether the authenticated user can perform this operation.
    # =========================================================================

    has_access = client.models.execute_kw(
        client.db,
        client.uid,
        client.password,
        model_name,
        "check_access_rights",
        [operation],
        {"raise_exception": False},
    )

    if not has_access:
        # Return immediately — no point running further gates.
        return {
            "valid": False,
            "errors": [
                f"User (uid={client.uid}) does not have '{operation}' "
                f"access on model '{model_name}'."
            ],
        }

    # =========================================================================
    # FETCH LIVE SCHEMA
    # fields_get() returns every field with type, required, readonly, selection.
    # This is the single source of truth for gates 2, 3, and 5.
    # FIX 1: use client.models.execute_kw directly — client.call() does not exist.
    # =========================================================================

    schema: Dict[str, Any] = client.models.execute_kw(
        client.db,
        client.uid,
        client.password,
        model_name,
        "fields_get",
        [],
        {
            "attributes": [
                "type",
                "required",
                "readonly",
                "selection",
            ]
        },
    )

    # =========================================================================
    # GATE 2 — REQUIRED FIELDS
    # Check every field marked required=True in the live schema.
    # Skip readonly fields — Odoo sets those automatically (e.g. employee_number).
    # =========================================================================

    for field_name, field_info in schema.items():
        if (
            operation == "create"
            and field_info.get("required")
            and not field_info.get("readonly")
            and field_name not in values
            and field_name not in FORBIDDEN_FIELDS
            and field_name not in AUTO_MANAGED_FIELDS
        ):
            errors.append(f"Missing required field: '{field_name}'")

    # =========================================================================
    # GATE 3 — VALUE VALIDATION
    # Check each value the caller provided against the live schema.
    # =========================================================================

    for field_name, value in values.items():

        # Skip forbidden fields here — Gate 5 will strip them.
        if field_name in FORBIDDEN_FIELDS:
            continue

        if field_name not in schema:
            errors.append(
                f"Field '{field_name}' does not exist on model '{model_name}'. "
                f"Check the schema via odoo://schema/{model_name}."
            )
            continue

        field_info = schema[field_name]
        field_type = field_info.get("type")

        # Selection — value must be exactly one of the allowed keys
        if field_type == "selection":
            allowed = [x[0] for x in (field_info.get("selection") or [])]
            if value not in allowed:
                errors.append(
                    f"Invalid value '{value}' for selection field '{field_name}'. "
                    f"Allowed values: {allowed}"
                )

        # Many2one — must be a positive integer (record ID), not a name string
        elif field_type == "many2one":
            if value is not None and not isinstance(value, int):
                errors.append(
                    f"Field '{field_name}' is a Many2one and expects an integer record ID. "
                    f"Got: '{value}' (type: {type(value).__name__}). "
                    f"Resolve the name to an ID first using the appropriate get_ tool."
                )
        
        # One2many / Many2many relational commands
        elif field_type in ("one2many", "many2many"):

            if not isinstance(value, list):
                errors.append(
                    f"Field '{field_name}' must be a list of Odoo command tuples."
                )

        elif field_type == "integer":
            if not isinstance(value, int):
                errors.append(f"Field '{field_name}' must be an integer.")

        elif field_type in ("float", "monetary"):
            if not isinstance(value, (int, float)):
                errors.append(f"Field '{field_name}' must be numeric.")

        elif field_type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"Field '{field_name}' must be True or False.")

    # =========================================================================
    # GATE 4 — UNIQUENESS PRE-FLIGHT
    # Only runs for models and fields that have known uniqueness requirements.
    # FIX 2: model-aware rules, not a generic field list.
    # FIX 2: includes archived records where specified (active in [True, False]).
    # =========================================================================
    
    unique_rules = MODEL_UNIQUE_FIELDS.get(model_name, {})
    
    for unique_field, include_archived in unique_rules.items():

        if unique_field not in values:
            continue  # Not being set in this payload — skip

        check_domain: List = [(unique_field, "=", values[unique_field])]

        if include_archived:
            # Check both active and archived — a duplicate on an archived record
            # will still cause a database constraint violation on restore.
            check_domain.append(("active", "in", [True, False]))

        try:
            existing = client.search_read(
                model=model_name,
                domain=check_domain,
                fields=["id"],
                limit=1,
                apply_company_scope=False,  # Uniqueness is global, not company-scoped
            )

            if existing:
                errors.append(
                    f"A record with {unique_field}='{values[unique_field]}' "
                    f"already exists in '{model_name}' (id={existing[0]['id']}). "
                    f"Provide a different value."
                )
        except Exception as e:
            # Domain validation in OdooClient may reject some domains —
            # log and skip rather than crashing the whole validation.
            errors.append(
                f"Uniqueness check for '{unique_field}' could not be completed: {e}"
            )

    # =========================================================================
    # GATE 5 — PAYLOAD SANITISATION
    # Build the clean payload: keep only writable fields that actually exist.
    # Strips: forbidden magic fields, readonly fields, unknown fields.
    # =========================================================================

    for field_name, value in values.items():

        if field_name in FORBIDDEN_FIELDS:
            continue  # Silently strip — Odoo manages these

        if field_name not in schema:
            continue  # Already flagged in Gate 3 if it was a user error

        if (
            schema[field_name].get("readonly")
            and schema[field_name].get("type")
            not in ("one2many", "many2many")
        ):
            continue

        cleaned_values[field_name] = value

    # =========================================================================
    # FINAL RESULT
    # =========================================================================

    if errors:
        return {
            "valid": False,
            "errors": errors,
        }

    return {
        "valid": True,
        "cleaned_values": cleaned_values,
    }