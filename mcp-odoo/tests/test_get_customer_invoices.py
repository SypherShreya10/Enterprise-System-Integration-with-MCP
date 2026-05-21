import sys
from tools.erp import get_customer_invoices
from odoo_client import ValidationError


def test_get_customer_invoices():

    print("=" * 70)
    print("Testing get_customer_invoices tool")
    print("=" * 70)

    # ----------------------------------------------------------
    # Test 1: Basic query by partner
    # ----------------------------------------------------------
    print("\nTest 1: Query invoices by partner_id")

    result = get_customer_invoices(partner_id=1)

    print(result)
    assert isinstance(result, list)

    print("  ✅ PASS")

    # ----------------------------------------------------------
    # Test 2: Filter by payment_state
    # ----------------------------------------------------------
    print("\nTest 2: Filter unpaid invoices")

    result = get_customer_invoices(payment_state="not_paid")

    print(result)
    assert isinstance(result, list)

    print("  ✅ PASS")

    # ----------------------------------------------------------
    # Test 3: Filter by date range
    # ----------------------------------------------------------
    print("\nTest 3: Date range filter")

    result = get_customer_invoices(
        invoice_date_from="2023-01-01",
        invoice_date_to="2030-01-01"
    )

    print(result)
    assert isinstance(result, list)

    print("  ✅ PASS")

    # ----------------------------------------------------------
    # Test 4: Invalid payment_state
    # ----------------------------------------------------------
    print("\nTest 4: Invalid payment_state")

    try:
        get_customer_invoices(payment_state="unknown_state")
        print("  ❌ FAIL")

    except ValidationError:
        print("  ✅ PASS")

    # ----------------------------------------------------------
    # Test 5: Invalid move_type
    # ----------------------------------------------------------
    print("\nTest 5: Invalid move_type")

    try:
        get_customer_invoices(move_type="wrong_type")
        print("  ❌ FAIL")

    except ValidationError:
        print("  ✅ PASS")

    # ----------------------------------------------------------
    # Test 6: date_to before date_from
    # ----------------------------------------------------------
    print("\nTest 6: Invalid date range")

    try:
        get_customer_invoices(
            invoice_date_from="2030-01-01",
            invoice_date_to="2020-01-01"
        )
        print("  ❌ FAIL")

    except ValidationError:
        print("  ✅ PASS")

    # ----------------------------------------------------------
    # Test 7: No filters (should fail)
    # ----------------------------------------------------------
    print("\nTest 7: No filters")

    try:
        get_customer_invoices()
        print("  ❌ FAIL")

    except ValidationError:
        print("  ✅ PASS")

    # ----------------------------------------------------------
    # Test 8: limit > 100
    # ----------------------------------------------------------
    print("\nTest 8: limit > 100")

    try:
        get_customer_invoices(partner_id=1, limit=200)
        print("  ❌ FAIL")

    except ValidationError:
        print("  ✅ PASS")

    # ----------------------------------------------------------
    # Test 9: negative limit
    # ----------------------------------------------------------
    print("\nTest 9: negative limit")

    try:
        get_customer_invoices(partner_id=1, limit=-5)
        print("  ❌ FAIL")

    except ValidationError:
        print("  ✅ PASS")


if __name__ == "__main__":
    test_get_customer_invoices()