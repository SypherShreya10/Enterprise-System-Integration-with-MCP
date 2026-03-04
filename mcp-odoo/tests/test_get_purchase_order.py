from tools.erp import get_purchase_order
from odoo_client import OdooClient, ValidationError

client = OdooClient()


# ---------------------------------------------------------
# Helper: fetch existing purchase order
# ---------------------------------------------------------

def get_existing_po():
    result = client.search_read(
        model="purchase.order",
        domain=[("id", "!=", 0)],
        fields=["id", "name", "partner_id", "state"],
        limit=1,
    )
    return result[0] if result else None


# ---------------------------------------------------------
# TEST 1: Fetch by order_id
# ---------------------------------------------------------

def test_fetch_by_order_id():

    print("\nTEST 025-1: Fetch by order_id")

    po = get_existing_po()

    if not po:
        print("SKIP: No purchase orders found.")
        return

    result = get_purchase_order(order_id=po["id"])

    print(result)

    assert isinstance(result, list)
    assert result[0]["id"] == po["id"]


# ---------------------------------------------------------
# TEST 2: Filter by supplier
# ---------------------------------------------------------

def test_filter_by_supplier():

    print("\nTEST 025-2: Filter by supplier")

    po = get_existing_po()

    if not po:
        print("SKIP: No purchase orders found.")
        return

    supplier_id = po["partner_id"][0]

    result = get_purchase_order(partner_id=supplier_id)

    print(result)

    assert isinstance(result, list)

    for r in result:
        assert r["partner_id"] == supplier_id


# ---------------------------------------------------------
# TEST 3: Filter by state
# ---------------------------------------------------------

def test_filter_by_state():

    print("\nTEST 025-3: Filter by state")

    po = get_existing_po()

    if not po:
        print("SKIP: No purchase orders found.")
        return

    state = po["state"]

    result = get_purchase_order(state=state)

    print(result)

    for r in result:
        assert r["state"] == state


# ---------------------------------------------------------
# TEST 4: Date range filter
# ---------------------------------------------------------

def test_date_range():

    print("\nTEST 025-4: Date range filter")

    result = get_purchase_order(
        state="purchase",
        date_from="2020-01-01",
        date_to="2030-01-01"
    )

    print(result)

    assert isinstance(result, list)


# ---------------------------------------------------------
# TEST 5: Limit enforcement
# ---------------------------------------------------------

def test_limit():

    print("\nTEST 025-5: Limit enforcement")

    result = get_purchase_order(state="purchase", limit=2)

    print(result)

    assert len(result) <= 2


# ---------------------------------------------------------
# TEST 6: Invalid state
# ---------------------------------------------------------

def test_invalid_state():

    print("\nTEST 025-6: Invalid state")

    try:
        get_purchase_order(state="invalid_state")
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)


# ---------------------------------------------------------
# TEST 7: Invalid date format
# ---------------------------------------------------------

def test_invalid_date():

    print("\nTEST 025-7: Invalid date format")

    try:
        get_purchase_order(state="purchase", date_from="20-10-2024")
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)


# ---------------------------------------------------------
# TEST 8: date_to before date_from
# ---------------------------------------------------------

def test_invalid_date_range():

    print("\nTEST 025-8: date_to before date_from")

    try:
        get_purchase_order(
            state="purchase",
            date_from="2025-01-01",
            date_to="2020-01-01"
        )
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)


# ---------------------------------------------------------
# TEST 9: No filters provided
# ---------------------------------------------------------

def test_no_filters():

    print("\nTEST 025-9: No filters")

    try:
        get_purchase_order()
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)


# ---------------------------------------------------------
# RUN TESTS
# ---------------------------------------------------------

if __name__ == "__main__":

    test_fetch_by_order_id()
    test_filter_by_supplier()
    test_filter_by_state()
    test_date_range()
    test_limit()
    test_invalid_state()
    test_invalid_date()
    test_invalid_date_range()
    test_no_filters()

    print("\nALL TESTS COMPLETED FOR TOOL 025\n")