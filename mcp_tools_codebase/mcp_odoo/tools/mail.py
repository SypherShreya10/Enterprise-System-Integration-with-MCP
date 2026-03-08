from typing import Optional, List, Dict, Any
import datetime
import logging
# from odoo_client import OdooClient
from mcp_odoo.odoo_client import OdooClient

logger = logging.getLogger(__name__)
client = OdooClient()

#section 3: tool - 15 create activity
def create_activity(
    *,
    activity_type_id: int,
    user_id: int,
    date_deadline: str,
    res_model: str,
    res_id: int,
    summary: Optional[str] = None,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a follow-up activity (mail.activity).

    MEDIUM RISK: Create-only operation.
    Used to schedule calls, meetings, emails, or reminders
    linked to an existing business record.

    Safety Guarantees:
    - Create-only (no updates)
    - No auto-completion (state remains 'planned')
    - Assigned user must be active internal user
    - Activity type must exist
    - Related record must exist and be accessible
    - Strict field allowlist
    - Company scoping enforced by OdooClient
    - Full audit logging
    """

    # ------------------------------------------------------------------
    # Input Validation
    # ------------------------------------------------------------------

    if not isinstance(activity_type_id, int) or activity_type_id <= 0:
        raise ValueError("activity_type_id must be a positive integer")

    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be a positive integer")

    if not isinstance(res_id, int) or res_id <= 0:
        raise ValueError("res_id must be a positive integer")

    if not isinstance(res_model, str) or not res_model.strip():
        raise ValueError("res_model must be a non-empty string")

    res_model = res_model.strip()

    try:
        deadline_date = datetime.date.fromisoformat(date_deadline)
    except Exception:
        raise ValueError("date_deadline must be in YYYY-MM-DD format")

    # ------------------------------------------------------------------
    # Verify Activity Type Exists (REFERENCE DATA)
    # ------------------------------------------------------------------

    activity_type = client.search_read(
        model="mail.activity.type",
        domain=[("id", "=", activity_type_id)],
        fields=["id", "name"],
        limit=1,
        apply_company_scope=False,  # reference data
    )

    if not activity_type:
        raise ValueError(
            f"Activity type with id={activity_type_id} does not exist"
        )

    activity_type_data = activity_type[0]

    # ------------------------------------------------------------------
    # Verify Assigned User is Active Internal User (SECURITY CRITICAL)
    # ------------------------------------------------------------------

    user = client.search_read(
        model="res.users",
        domain=[
            ("id", "=", user_id),
            ("active", "=", True),
            ("share", "=", False),  # block portal users
        ],
        fields=["id", "name"],
        limit=1,
    )

    if not user:
        raise ValueError(
            f"User with id={user_id} does not exist, is inactive, "
            "or is not an internal user"
        )

    user_data = user[0]

    # # ------------------------------------------------------------------
    # # Verify Related Record Exists (NON-EMPTY DOMAIN)
    # # ------------------------------------------------------------------

    # related = client.search_read(
    #     model=res_model,
    #     domain=[("id", "=", res_id)],
    #     fields=["id"],
    #     limit=1,
    # )

    # if not related:
    #     raise ValueError(
    #         f"Related record {res_model} with id={res_id} not found "
    #         "or not accessible in current company"
    #     )

    # ------------------------------------------------------------------
    # Verify Related Record Exists and Model is Valid
    # ------------------------------------------------------------------

    try:
        related = client.search_read(
            model=res_model,
            domain=[("id", "=", res_id)],
            fields=["id"],
            limit=1,
        )

    except Exception:
        # Model itself does not exist or is inaccessible
        raise ValueError(
            f"Model '{res_model}' does not exist or is not accessible"
        )

    if not related:
        raise ValueError(
            f"Related record {res_model} with id={res_id} not found "
            "or not accessible in current company"
        )

    # ------------------------------------------------------------------
    # Prepare Allowlisted Create Values
    # ------------------------------------------------------------------

    values: Dict[str, Any] = {
        "activity_type_id": activity_type_id,
        "user_id": user_id,
        "date_deadline": date_deadline,
        "res_model": res_model,
        "res_id": res_id,
    }

    if summary:
        values["summary"] = summary.strip()

    if note:
        values["note"] = note.strip()

    # Forbidden fields (never set):
    # - state
    # - date_done
    # - company_id

    # ------------------------------------------------------------------
    # Audit Logging (Before Create)
    # ------------------------------------------------------------------

    logger.info(
        "MCP Tool: create_activity",
        extra={
            "model": "mail.activity",
            "operation": "create",
            "activity_type": activity_type_data["name"],
            "assigned_user": user_data["name"],
            "res_model": res_model,
            "res_id": res_id,
            "date_deadline": date_deadline,
            "company_id": client.company_id,
            "caller_user_id": client.user_id,
        },
    )

    # ------------------------------------------------------------------
    # Create Activity
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
                "activity_type": activity_type_data["name"],
                "assigned_user": user_data["name"],
                "date_deadline": date_deadline,
            },
        )

        return {
            "activity_id": activity_id,
            "activity_type_id": activity_type_id,
            "activity_type_name": activity_type_data["name"],
            "assigned_user_id": user_id,
            "assigned_user_name": user_data["name"],
            "date_deadline": date_deadline,
            "res_model": res_model,
            "res_id": res_id,
            "summary": summary,
            "message": (
                f"Activity '{activity_type_data['name']}' created and assigned to "
                f"{user_data['name']} with deadline {date_deadline}"
            ),
        }

    except Exception as exc:
        logger.error(
            f"create_activity failed: {type(exc).__name__}: {str(exc)}",
            exc_info=True,
        )
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

        return records

    except Exception as exc:
        logger.error(
            f"get_activity failed: {type(exc).__name__}: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError(
            f"Failed to fetch activities: {str(exc)}"
        ) from exc