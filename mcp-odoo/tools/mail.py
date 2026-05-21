from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from odoo_client import OdooClient
from validators import validate_write_payload

logger = logging.getLogger(__name__)
client = OdooClient()

def wrap_response(data, summary=None, insights=None, model=None):
    return {
        "data": data,
        "summary": summary or {},
        "insights": insights or [],
        "meta": {
            "model": model,
            "record_count": len(data) if isinstance(data, list) else 1
        }
    }

#section 2: tool 15 - create activity
def create_activity(
    *,
    activity_type_id: int,
    summary: str,
    res_model: str,
    res_id: int,
    user_id: int,
    note: Optional[str] = None,
    date_deadline: str,
) -> Dict[str, Any]:
    """
    Create a scheduled activity in Odoo.

    Safety:
    - Create-only operation
    - Company-safe
    - Internal-user assignment only
    - Related record existence validation
    - Activity type validation
    - Centralized payload validation
    """

    # ------------------------------------------------------------------
    # Basic validation
    # ------------------------------------------------------------------

    if not summary or not summary.strip():
        raise ValueError("Activity summary is required.")

    summary = summary.strip()

    if not res_model or not res_model.strip():
        raise ValueError("res_model is required.")

    res_model = res_model.strip()

    # ------------------------------------------------------------------
    # Restrict allowed target models
    # Prevent arbitrary model probing through mail.activity
    # ------------------------------------------------------------------

    ALLOWED_ACTIVITY_MODELS = {
        "crm.lead",
        "sale.order",
        "purchase.order",
        "res.partner",
    }

    if res_model not in ALLOWED_ACTIVITY_MODELS:
        raise ValueError(
            f"Activities cannot be attached to model '{res_model}'."
        )

    # ------------------------------------------------------------------
    # Validate date format
    # ------------------------------------------------------------------

    if date_deadline:
        try:
            datetime.strptime(date_deadline, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                "date_deadline must be in YYYY-MM-DD format."
            )

    # ------------------------------------------------------------------
    # Prepare values
    # ------------------------------------------------------------------

    values: Dict[str, Any] = {
        "activity_type_id": activity_type_id,
        "summary": summary,
        "res_model": res_model,
        "res_id": res_id,
        "user_id": user_id,
    }

    if note:
        values["note"] = note.strip()

    if date_deadline:
        values["date_deadline"] = date_deadline

    # ------------------------------------------------------------------
    # Centralized validation layer
    # ------------------------------------------------------------------

    validation = validate_write_payload(
        client=client,
        model_name="mail.activity",
        values=values,
        operation="create",
    )

    if not validation["valid"]:
        raise ValueError(
            "Payload validation failed: "
            + "; ".join(validation["errors"])
        )

    values = validation["cleaned_values"]

    # ------------------------------------------------------------------
    # Verify activity type exists
    # ------------------------------------------------------------------

    activity_type = client.search_read(
        model="mail.activity.type",
        domain=[("id", "=", activity_type_id)],
        fields=["id", "name"],
        limit=1,
    )

    if not activity_type:
        raise ValueError(
            f"Activity type {activity_type_id} does not exist."
        )

    # ------------------------------------------------------------------
    # Verify assigned user exists and is internal
    # ------------------------------------------------------------------

    assigned_user = client.search_read(
        model="res.users",
        domain=[
            ("id", "=", user_id),
            ("share", "=", False),
        ],
        fields=["id", "name"],
        limit=1,
    )

    if not assigned_user:
        raise ValueError(
            f"Internal user {user_id} does not exist."
        )

    # ------------------------------------------------------------------
    # Verify related business record exists
    # ------------------------------------------------------------------

    related_record = client.search_read(
        model=res_model,
        domain=[("id", "=", res_id)],
        fields=["id"],
        limit=1,
    )

    if not related_record:
        raise ValueError(
            f"Record {res_id} does not exist in model '{res_model}'."
        )

    logger.info(
        "Tool create_activity invoked",
        extra={
            "activity_type_id": activity_type_id,
            "res_model": res_model,
            "res_id": res_id,
            "assigned_user_id": user_id,
            "caller_uid": client.uid,
        },
    )

    # ------------------------------------------------------------------
    # Create activity
    # ------------------------------------------------------------------

    try:

        activity_id = client.create(
            model="mail.activity",
            values=values,
        )

        logger.info(
            "Activity created successfully",
            extra={
                "activity_id": activity_id,
                "res_model": res_model,
                "res_id": res_id,
            },
        )

        return wrap_response(
            data={
                "activity_id": activity_id,
                "activity_type": activity_type[0]["name"],
                "assigned_user": assigned_user[0]["name"],
                "related_model": res_model,
                "related_record_id": res_id,
                "message": "Activity created successfully.",
            },
            summary={"status": "created"},
            insights=[
                f"Activity assigned to {assigned_user[0]['name']}",
                f"Attached to {res_model} record {res_id}",
            ],
            model="mail.activity",
        )

    except Exception as exc:

        logger.error(
            "create_activity failed",
            extra={
                "values": values,
                "res_model": res_model,
                "res_id": res_id,
            },
            exc_info=True,
        )

        if isinstance(exc, ValueError):
            raise

        raise RuntimeError(
            f"Failed to create activity: {str(exc)}"
        ) from exc


#section 3: tool 16 - get activity
def get_activity(
    *,
    user_id: Optional[int] = None,
    res_model: Optional[str] = None,
    date_deadline: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Fetch scheduled activities (mail.activity).

    LOW RISK: Read-only operation.

    Business Use Cases:
        - "What tasks are due today?"
        - "Show John's pending tasks"
        - "List CRM follow-ups"
        - "Show overdue sales tasks"

    Parameters:
        user_id: Filter by assigned user (positive integer)
        res_model: Filter by related model (e.g., 'crm.lead', 'sale.order')
        date_deadline: Filter by due date (YYYY-MM-DD format)
        state: Filter by activity state ('planned', 'today', 'overdue', 'done')
        limit: Max records (1–100)

    Returns:
        List of dictionaries containing:
        - id
        - activity_type_id
        - user_id
        - date_deadline
        - summary
        - note
        - res_model
        - res_id
        - state
        - create_date
        - write_date

    Safety Guarantees:
        - Read-only
        - Company-scoped automatically via OdooClient
        - No full table scans (at least one filter required)
        - Max 100 records
        - Strict field allowlist
        - Audit logging enforced
    """

    # ------------------------------------------------------------------
    # Input Validation
    # ------------------------------------------------------------------

    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")

    domain = []

    if user_id is not None:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id must be a positive integer")
        domain.append(("user_id", "=", user_id))

    if res_model is not None:
        if not isinstance(res_model, str) or not res_model.strip():
            raise ValueError("res_model must be a non-empty string")
        domain.append(("res_model", "=", res_model.strip()))

    if date_deadline is not None:
        try:
            datetime.date.fromisoformat(date_deadline)
        except Exception:
            raise ValueError("date_deadline must be in YYYY-MM-DD format")
        domain.append(("date_deadline", "=", date_deadline))

    if state is not None:
        allowed_states = ["planned", "today", "overdue", "done"]
        if state not in allowed_states:
            raise ValueError(
                f"state must be one of {allowed_states}"
            )
        domain.append(("state", "=", state))

    # Prevent full-table scans (client also guards this)
    if not domain:
        raise ValueError(
            "At least one filter must be provided "
            "(user_id, res_model, date_deadline, or state)"
        )

    # ------------------------------------------------------------------
    # Strict Field Allowlist
    # ------------------------------------------------------------------

    fields = [
        "id",
        "activity_type_id",
        "user_id",
        "date_deadline",
        "summary",
        "note",
        "res_model",
        "res_id",
        "state",
        "create_date",
        "write_date",
    ]

    # ------------------------------------------------------------------
    # Audit Logging
    # ------------------------------------------------------------------

    logger.info(
        "MCP Tool: get_activity",
        extra={
            "model": "mail.activity",
            "operation": "search_read",
            "domain": domain,
            "fields": fields,
            "limit": limit,
            "company_id": client.company_id,
            "caller_user_id": client.uid,
        },
    )

    # ------------------------------------------------------------------
    # Execute Safe Read
    # ------------------------------------------------------------------

    try:
        records = client.search_read(
            model="mail.activity",
            domain=domain,
            fields=fields,
            limit=limit,
        )

        logger.info(
            "get_activity completed",
            extra={"record_count": len(records)},
        )

        return wrap_response(
            data=records,
            summary={"count": len(records)},
            insights=[
                f"{len(records)} activities found"
            ] if records else ["No activities found"],
            model="mail.activity"
        )

    except Exception as exc:
        logger.error(
            f"get_activity failed: {type(exc).__name__}: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError(
            f"Failed to fetch activities: {str(exc)}"
        ) from exc