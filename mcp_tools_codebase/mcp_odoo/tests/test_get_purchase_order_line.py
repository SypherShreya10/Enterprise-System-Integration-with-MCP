from tools.erp import get_purchase_order_lines
from odoo_client import OdooClient, ValidationError

client = OdooClient()


# ---------------------------------------------------------
# Helper: fetch PO with lines
# ---------------------------------------------------------

def get_po_with_lines():

    orders = client.search_read(
        model="purchase.order.line",
        domain=[("id", "!=", 0)],
        fields=["order_id"],
        limit=1,
    )

    if not orders:
        return None

    return orders[0]["order_id"][0]


# ---------------------------------------------------------
# TEST 1: Valid order lines fetch
# ---------------------------------------------------------

def test_fetch_lines():

    print("\nTEST 026-1: Fetch order lines")

    order_id = get_po_with_lines()

    if not order_id:
        print("SKIP: No purchase order lines exist.")
        return

    result = get_purchase_order_lines(order_id=order_id)

    print(result)

    assert isinstance(result, list)

    for r in result:
        assert r["order_id"] == order_id


# ---------------------------------------------------------
# TEST 2: Structure validation
# ---------------------------------------------------------

def test_structure():

    print("\nTEST 026-2: Structure validation")

    order_id = get_po_with_lines()

    if not order_id:
        print("SKIP")
        return

    result = get_purchase_order_lines(order_id=order_id)

    if not result:
        print("No lines returned.")
        return

    r = result[0]

    required_fields = [
        "id",
        "order_id",
        "product_id",
        "product_name",
        "product_qty",
        "price_unit",
        "date_planned"
    ]

    for field in required_fields:
        assert field in r


# ---------------------------------------------------------
# TEST 3: Limit enforcement
# ---------------------------------------------------------

def test_limit():

    print("\nTEST 026-3: Limit enforcement")

    order_id = get_po_with_lines()

    if not order_id:
        print("SKIP")
        return

    result = get_purchase_order_lines(order_id=order_id, limit=2)

    print(result)

    assert len(result) <= 2


# ---------------------------------------------------------
# TEST 4: Invalid order_id
# ---------------------------------------------------------

def test_invalid_order():

    print("\nTEST 026-4: Invalid order_id")

    try:
        get_purchase_order_lines(order_id=99999999)
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)


# ---------------------------------------------------------
# TEST 5: Missing order_id
# ---------------------------------------------------------

def test_missing_order():

    print("\nTEST 026-5: Missing order_id")

    try:
        get_purchase_order_lines(order_id=None)
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)


# ---------------------------------------------------------
# RUN TESTS
# ---------------------------------------------------------

if __name__ == "__main__":

    test_fetch_lines()
    test_structure()
    test_limit()
    test_invalid_order()
    test_missing_order()

    print("\nALL TESTS COMPLETED FOR TOOL 026\n")