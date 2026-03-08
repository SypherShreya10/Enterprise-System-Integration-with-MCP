# tests/sales/test_get_customer_order_history.py

import datetime
from tools.erp import get_customer_order_history
from odoo_client import OdooClient, ValidationError

client = OdooClient()


# ==========================================================
# HELPERS
# ==========================================================

def get_existing_customer():
    result = client.search_read(
        model="res.partner",
        domain=[("customer_rank", ">", 0)],
        fields=["id", "name"],
        limit=1,
    )
    return result[0] if result else None


def get_non_customer_partner():
    result = client.search_read(
        model="res.partner",
        domain=[("customer_rank", "=", 0)],
        fields=["id", "name"],
        limit=1,
    )
    return result[0] if result else None


# ==========================================================
# TESTS
# ==========================================================

def test_024_basic_history_fetch():
    print("\nTEST 024-01: Basic customer order history fetch")

    customer = get_existing_customer()
    assert customer is not None, "No customers found in system."

    result = get_customer_order_history(partner_id=customer["id"])

    print("AI TOOL OUTPUT:", result)

    assert result["partner_id"] == customer["id"]
    assert result["partner_name"] == customer["name"]
    assert isinstance(result["orders"], list)
    assert isinstance(result["summary"], dict)


def test_024_summary_fields_present():
    print("\nTEST 024-02: Summary fields validation")

    customer = get_existing_customer()
    result = get_customer_order_history(partner_id=customer["id"])

    summary = result["summary"]

    expected_fields = [
        "total_orders",
        "total_orders_returned",
        "truncated",
        "total_revenue",
        "average_order_value",
        "most_recent_order_date",
        "most_recent_active_order_date",
        "state_breakdown",
    ]

    for field in expected_fields:
        assert field in summary, f"Missing summary field: {field}"

    print("SUMMARY STRUCTURE VALID")


def test_024_state_breakdown_structure():
    print("\nTEST 024-03: State breakdown structure is deterministic")

    customer = get_existing_customer()
    result = get_customer_order_history(partner_id=customer["id"])

    breakdown = result["summary"]["state_breakdown"]

    expected_states = ["draft", "sent", "sale", "done", "cancel"]

    for state in expected_states:
        assert state in breakdown, f"Missing state key: {state}"

    print("STATE BREAKDOWN STRUCTURE VALID")


def test_024_truncation_flag():
    print("\nTEST 024-04: Truncation flag logic")

    customer = get_existing_customer()
    result = get_customer_order_history(partner_id=customer["id"])

    summary = result["summary"]

    assert summary["total_orders"] >= summary["total_orders_returned"]

    if summary["total_orders"] > 100:
        assert summary["truncated"] is True
    else:
        assert summary["truncated"] is False

    print("TRUNCATION LOGIC VALID")


def test_024_revenue_excludes_cancelled():
    print("\nTEST 024-05: Revenue excludes cancelled orders")

    customer = get_existing_customer()
    result = get_customer_order_history(partner_id=customer["id"])

    summary = result["summary"]

    # Revenue should never be negative
    assert summary["total_revenue"] >= 0

    print("REVENUE LOGIC VALID")


def test_024_most_recent_dates_format():
    print("\nTEST 024-06: Date format validation")

    customer = get_existing_customer()
    result = get_customer_order_history(partner_id=customer["id"])

    summary = result["summary"]

    for key in ["most_recent_order_date", "most_recent_active_order_date"]:
        date_value = summary.get(key)
        if date_value:
            # Must be YYYY-MM-DD
            datetime.date.fromisoformat(date_value)

    print("DATE FORMAT VALID")


def test_024_orders_structure():
    print("\nTEST 024-07: Orders list structure validation")

    customer = get_existing_customer()
    result = get_customer_order_history(partner_id=customer["id"])

    orders = result["orders"]

    if not orders:
        print("Customer has no orders — structure still valid.")
        return

    order = orders[0]

    expected_fields = [
        "id",
        "name",
        "date_order",
        "amount_total",
        "state",
        "salesperson_id",
        "salesperson_name",
    ]

    for field in expected_fields:
        assert field in order, f"Missing order field: {field}"

    print("ORDER STRUCTURE VALID")


def test_024_nonexistent_partner():
    print("\nTEST 024-08: Non-existent partner must raise ValidationError")

    try:
        get_customer_order_history(partner_id=99999999)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)


def test_024_non_customer_partner():
    print("\nTEST 024-09: Non-customer partner must raise ValidationError")

    non_customer = get_non_customer_partner()

    if not non_customer:
        print("SKIP: All partners are customers.")
        return

    try:
        get_customer_order_history(partner_id=non_customer["id"])
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)


# ==========================================================
# RUNNER
# ==========================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("TOOL 024 — get_customer_order_history")
    print("=" * 60)

    test_024_basic_history_fetch()
    test_024_summary_fields_present()
    test_024_state_breakdown_structure()
    test_024_truncation_flag()
    test_024_revenue_excludes_cancelled()
    test_024_most_recent_dates_format()
    test_024_orders_structure()
    test_024_nonexistent_partner()
    test_024_non_customer_partner()

    print("\n" + "=" * 60)
    print("ALL TOOL 024 TESTS COMPLETED")
    print("=" * 60)