from tools.erp import check_customer_credit
from odoo_client import ValidationError, OdooClient


def test_check_customer_credit():

    print("=" * 70)
    print("Testing check_customer_credit tool")
    print("=" * 70)

    client = OdooClient()

    # ----------------------------------------------------------
    # Find a real customer dynamically
    # ----------------------------------------------------------

    customer = client.search_read(
        model="res.partner",
        domain=[("customer_rank", ">", 0)],
        fields=["id"],
        limit=1,
    )

    if not customer:
        print("⚠ No customers found in database. Skipping test.")
        return

    partner_id = customer[0]["id"]

    # ----------------------------------------------------------
    # Test 1: Basic credit check
    # ----------------------------------------------------------

    print("\nTest 1: Basic credit check")

    result = check_customer_credit(partner_id=partner_id)

    print(result)

    assert "partner_id" in result
    assert "credit_status" in result

    print("  ✅ PASS")

    # ----------------------------------------------------------
    # Test 2: Non-existent customer
    # ----------------------------------------------------------

    print("\nTest 2: Non-existent customer")

    try:
        check_customer_credit(partner_id=999999)
        print("  ❌ FAIL")
    except ValidationError:
        print("  ✅ PASS")

    # ----------------------------------------------------------
    # Test 3: Invalid partner_id type
    # ----------------------------------------------------------

    print("\nTest 3: partner_id string")

    try:
        check_customer_credit(partner_id="abc")
        print("  ❌ FAIL")
    except ValidationError:
        print("  ✅ PASS")

    # ----------------------------------------------------------
    # Test 4: Negative partner_id
    # ----------------------------------------------------------

    print("\nTest 4: Negative partner_id")

    try:
        check_customer_credit(partner_id=-10)
        print("  ❌ FAIL")
    except ValidationError:
        print("  ✅ PASS")

    # ----------------------------------------------------------
    # Test 5: Validate structure
    # ----------------------------------------------------------

    print("\nTest 5: Validate response structure")

    result = check_customer_credit(partner_id=partner_id)

    assert "overdue_invoices" in result
    assert "credit_limit" in result
    assert "available_credit" in result

    print("  ✅ PASS")


if __name__ == "__main__":
    test_check_customer_credit()