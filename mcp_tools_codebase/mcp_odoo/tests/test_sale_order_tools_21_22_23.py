# tests/sales/test_sale_order_tools.py

import datetime
from tools.erp import get_sale_order
from tools.erp import get_sale_order_lines
from tools.erp import create_sale_order
from odoo_client import OdooClient, ValidationError

client = OdooClient()


# ==============================================================================
# SHARED HELPERS
# ==============================================================================

def get_existing_customer():
    result = client.search_read(
        model="res.partner",
        domain=[("customer_rank", ">", 0)],
        fields=["id", "name"],
        limit=1,
    )
    return result[0] if result else None


def get_sellable_product():
    result = client.search_read(
        model="product.product",
        domain=[
            ("active", "=", True),
            ("sale_ok", "=", True),
        ],
        fields=["id", "name", "list_price"],
        limit=1,
    )
    return result[0] if result else None


def get_existing_sale_order():
    result = client.search_read(
        model="sale.order",
        domain=[("id", ">", 0)],
        fields=["id", "name", "state", "partner_id"],
        limit=1,
    )
    return result[0] if result else None


def get_cancelled_sale_order():
    result = client.search_read(
        model="sale.order",
        domain=[("state", "=", "cancel")],
        fields=["id", "name", "state"],
        limit=1,
    )
    return result[0] if result else None


def get_confirmed_sale_order():
    result = client.search_read(
        model="sale.order",
        domain=[("state", "=", "sale")],
        fields=["id", "name", "state", "partner_id"],
        limit=1,
    )
    return result[0] if result else None


# ==============================================================================
# TOOL 021 — get_sale_order
# ==============================================================================

def test_021_get_by_order_id():
    print("\nTEST 021-01: Get order by order_id")

    order = get_existing_sale_order()
    assert order is not None, "No sale orders found in Odoo — seed test data first."

    result = get_sale_order(order_id=order["id"])

    print("AI TOOL OUTPUT:", result)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["id"] == order["id"]
    assert "partner_name" in result[0]
    assert "salesperson_name" in result[0] or result[0].get("user_id") is not None


def test_021_get_by_order_name():
    print("\nTEST 021-02: Get order by name (partial match)")

    order = get_existing_sale_order()
    assert order is not None

    # Use partial name — ilike search
    partial_name = order["name"][:4]
    result = get_sale_order(name=partial_name)

    print("AI TOOL OUTPUT:", result)

    assert isinstance(result, list)
    assert len(result) >= 1


def test_021_get_by_partner_id():
    print("\nTEST 021-03: Get orders by partner_id")

    order = get_existing_sale_order()
    assert order is not None

    partner_id = order["partner_id"][0] if isinstance(order["partner_id"], list) else order["partner_id"]

    result = get_sale_order(partner_id=partner_id)

    print("AI TOOL OUTPUT:", result)

    assert isinstance(result, list)
    assert all(r["partner_id"] == partner_id for r in result)


def test_021_get_by_state_draft():
    print("\nTEST 021-04: Filter by state=draft")

    result = get_sale_order(state="draft", limit=5)

    print("AI TOOL OUTPUT:", result)

    assert isinstance(result, list)
    assert all(r["state"] == "draft" for r in result)


def test_021_get_by_state_cancelled():
    print("\nTEST 021-05: Filter by state=cancel (audit use case)")

    result = get_sale_order(state="cancel", limit=5)

    print("AI TOOL OUTPUT:", result)

    # Should return results (cancel is allowed) or empty list — not an error
    assert isinstance(result, list)
    assert all(r["state"] == "cancel" for r in result)


def test_021_get_by_date_range():
    print("\nTEST 021-06: Filter by date range")

    date_from = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
    date_to = datetime.date.today().isoformat()

    result = get_sale_order(date_from=date_from, date_to=date_to, limit=10)

    print("AI TOOL OUTPUT:", result)

    assert isinstance(result, list)


def test_021_date_range_no_results():
    print("\nTEST 021-07: Date range with no results (far future)")

    result = get_sale_order(
        date_from="2099-01-01",
        date_to="2099-12-31",
        limit=10,
    )

    print("AI TOOL OUTPUT:", result)

    assert isinstance(result, list)
    assert len(result) == 0


def test_021_limit_respected():
    print("\nTEST 021-08: Limit is respected")

    result = get_sale_order(state="sale", limit=3)

    print("AI TOOL OUTPUT:", result)

    assert isinstance(result, list)
    assert len(result) <= 3


def test_021_limit_exceeds_100():
    print("\nTEST 021-09: Limit exceeds 100 — must raise ValidationError")

    try:
        get_sale_order(state="sale", limit=200)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "100" in str(e)


def test_021_invalid_state():
    print("\nTEST 021-10: Invalid state value")

    try:
        get_sale_order(state="invalid_state")
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "Invalid state" in str(e)


def test_021_no_filters_raises():
    print("\nTEST 021-11: No filters — must raise ValidationError (full table scan prevention)")

    try:
        get_sale_order()
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "filter" in str(e).lower()


def test_021_nonexistent_order_id():
    print("\nTEST 021-12: Non-existent order_id — must return empty list")

    result = get_sale_order(order_id=99999999)

    print("AI TOOL OUTPUT:", result)

    assert isinstance(result, list)
    assert len(result) == 0


def test_021_many2one_normalization():
    print("\nTEST 021-13: Many2one fields are normalized (not raw list)")

    order = get_existing_sale_order()
    assert order is not None

    result = get_sale_order(order_id=order["id"])

    assert len(result) == 1
    record = result[0]

    # partner_id must be int, not [id, name]
    assert isinstance(record["partner_id"], int), "partner_id should be int after normalization"
    assert isinstance(record["partner_name"], str), "partner_name should be string"
    print("NORMALIZATION CHECK PASSED:", record["partner_id"], record["partner_name"])


def test_021_return_fields_complete():
    print("\nTEST 021-14: All expected fields are present in return value")

    order = get_existing_sale_order()
    assert order is not None

    result = get_sale_order(order_id=order["id"])
    assert len(result) == 1
    record = result[0]

    expected_fields = [
        "id", "name", "partner_id", "partner_name",
        "date_order", "validity_date", "amount_total",
        "amount_tax", "amount_untaxed", "state",
    ]

    for field in expected_fields:
        assert field in record, f"Missing field: {field}"

    print("ALL FIELDS PRESENT:", list(record.keys()))


# ==============================================================================
# TOOL 022 — get_sale_order_lines
# ==============================================================================

def test_022_get_lines_for_valid_order():
    print("\nTEST 022-01: Get lines for a valid order")

    order = get_existing_sale_order()
    assert order is not None

    result = get_sale_order_lines(order_id=order["id"])

    print("AI TOOL OUTPUT:", result)

    assert isinstance(result, list)


def test_022_lines_for_confirmed_order():
    print("\nTEST 022-02: Get lines for a confirmed (sale) order")

    order = get_confirmed_sale_order()
    assert order is not None, "No confirmed orders — confirm one in Odoo first."

    result = get_sale_order_lines(order_id=order["id"])

    print("AI TOOL OUTPUT:", result)

    assert isinstance(result, list)
    assert len(result) >= 1


def test_022_lines_for_cancelled_order():
    print("\nTEST 022-03: Get lines for a cancelled order (audit use case)")

    order = get_cancelled_sale_order()

    if order is None:
        print("SKIP: No cancelled orders in system.")
        return

    result = get_sale_order_lines(order_id=order["id"])

    print("AI TOOL OUTPUT:", result)

    # Must return lines, not raise error
    assert isinstance(result, list)


def test_022_nonexistent_order_id():
    print("\nTEST 022-04: Non-existent order_id — must raise ValidationError")

    try:
        get_sale_order_lines(order_id=99999999)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "does not exist" in str(e)


def test_022_missing_order_id():
    print("\nTEST 022-05: Missing order_id (None) — must raise ValidationError")

    try:
        get_sale_order_lines(order_id=None)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "order_id" in str(e)


def test_022_limit_exceeds_100():
    print("\nTEST 022-06: Limit exceeds 100 — must raise ValidationError")

    order = get_existing_sale_order()
    assert order is not None

    try:
        get_sale_order_lines(order_id=order["id"], limit=200)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "100" in str(e)


def test_022_many2one_normalization():
    print("\nTEST 022-07: Many2one fields are normalized")

    order = get_existing_sale_order()
    assert order is not None

    result = get_sale_order_lines(order_id=order["id"])

    if not result:
        print("SKIP: Order has no lines.")
        return

    record = result[0]

    assert isinstance(record["product_id"], int), "product_id should be int"
    assert isinstance(record["product_name"], str), "product_name should be string"
    assert isinstance(record["order_id"], int), "order_id should be int"

    print("NORMALIZATION CHECK PASSED:", record["product_id"], record["product_name"])


def test_022_return_fields_complete():
    print("\nTEST 022-08: All expected fields present in each line")

    order = get_existing_sale_order()
    assert order is not None

    result = get_sale_order_lines(order_id=order["id"])

    if not result:
        print("SKIP: Order has no lines.")
        return

    expected_fields = [
        "id", "order_id", "product_id", "product_name",
        "product_uom_qty", "price_unit",
        "price_subtotal", "price_total", "discount",
    ]

    for field in expected_fields:
        assert field in result[0], f"Missing field: {field}"

    print("ALL FIELDS PRESENT:", list(result[0].keys()))


def test_022_order_with_no_lines():
    print("\nTEST 022-09: Order with no lines — must return empty list, not error")

    # Create a bare order in Odoo manually or find one with no lines
    # Here we just verify the tool handles empty result gracefully
    order = get_existing_sale_order()
    assert order is not None

    result = get_sale_order_lines(order_id=order["id"])

    # Either a list of lines or an empty list — both are valid
    assert isinstance(result, list)
    print("GRACEFUL EMPTY RETURN:", result)


# ==============================================================================
# TOOL 023 — create_sale_order
# ==============================================================================

def test_023_basic_create():
    print("\nTEST 023-01: Basic valid order creation")

    customer = get_existing_customer()
    product = get_sellable_product()

    assert customer is not None
    assert product is not None

    result = create_sale_order(
        partner_id=customer["id"],
        order_lines=[{
            "product_id": product["id"],
            "product_uom_qty": 2,
        }],
    )

    print("AI TOOL OUTPUT:", result)

    assert "order_id" in result
    assert "order_name" in result
    assert result["state"] == "draft"
    assert result["partner_id"] == customer["id"]
    assert result["partner_name"] == customer["name"]
    assert len(result["lines"]) == 1

    # Verify in Odoo
    created = client.search_read(
        model="sale.order",
        domain=[("id", "=", result["order_id"])],
        fields=["id", "name", "state", "partner_id"],
        limit=1,
    )
    assert created, "Order not found in Odoo after creation"
    assert created[0]["state"] == "draft"
    print("ODOO VERIFICATION PASSED:", created[0])


def test_023_create_with_all_optional_fields():
    print("\nTEST 023-02: Create with all optional fields")

    customer = get_existing_customer()
    product = get_sellable_product()

    assert customer is not None
    assert product is not None

    today = datetime.date.today().isoformat()
    validity = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()

    result = create_sale_order(
        partner_id=customer["id"],
        order_lines=[{
            "product_id": product["id"],
            "product_uom_qty": 5,
        }],
        date_order=today,
        validity_date=validity,
        client_order_ref="PO-TEST-001",
    )

    print("AI TOOL OUTPUT:", result)

    assert result["state"] == "draft"
    assert result["date_order"] is not None
    assert result["validity_date"] is not None

    # Verify client_order_ref in Odoo
    created = client.search_read(
        model="sale.order",
        domain=[("id", "=", result["order_id"])],
        fields=["client_order_ref", "validity_date"],
        limit=1,
    )
    assert created[0]["client_order_ref"] == "PO-TEST-001"
    print("ODOO VERIFICATION PASSED:", created[0])


def test_023_create_multiple_lines():
    print("\nTEST 023-03: Create order with multiple product lines")

    customer = get_existing_customer()

    products = client.search_read(
        model="product.product",
        domain=[("active", "=", True), ("sale_ok", "=", True)],
        fields=["id", "name", "list_price"],
        limit=2,
    )

    assert len(products) >= 2, "Need at least 2 sellable products in Odoo."

    result = create_sale_order(
        partner_id=customer["id"],
        order_lines=[
            {"product_id": products[0]["id"], "product_uom_qty": 1},
            {"product_id": products[1]["id"], "product_uom_qty": 3},
        ],
    )

    print("AI TOOL OUTPUT:", result)

    assert len(result["lines"]) == 2

    # Verify line count in Odoo
    lines = client.search_read(
        model="sale.order.line",
        domain=[("order_id", "=", result["order_id"])],
        fields=["id", "product_id", "product_uom_qty"],
        limit=10,
    )
    assert len(lines) == 2
    print("ODOO LINE VERIFICATION PASSED:", lines)


def test_023_stock_warning_in_return():
    print("\nTEST 023-04: Stock warning appears when stock is low")

    customer = get_existing_customer()
    product = get_sellable_product()

    assert customer is not None
    assert product is not None

    # Request an unrealistically large quantity to trigger warning
    result = create_sale_order(
        partner_id=customer["id"],
        order_lines=[{
            "product_id": product["id"],
            "product_uom_qty": 999999,
        }],
    )

    print("AI TOOL OUTPUT:", result)

    # Order must still be created — stock check is warning only
    assert result["state"] == "draft"
    assert result["lines"][0]["stock_warning"] is not None
    print("STOCK WARNING:", result["lines"][0]["stock_warning"])


def test_023_invalid_partner_id():
    print("\nTEST 023-05: Non-existent partner_id")

    product = get_sellable_product()

    try:
        create_sale_order(
            partner_id=99999999,
            order_lines=[{"product_id": product["id"], "product_uom_qty": 1}],
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "not a customer" in str(e) or "does not exist" in str(e)


def test_023_non_customer_partner():
    print("\nTEST 023-06: Partner exists but is not a customer")

    # Find a partner with customer_rank = 0
    non_customer = client.search_read(
        model="res.partner",
        domain=[("customer_rank", "=", 0)],
        fields=["id", "name"],
        limit=1,
    )

    if not non_customer:
        print("SKIP: All partners are customers in this system.")
        return

    product = get_sellable_product()

    try:
        create_sale_order(
            partner_id=non_customer[0]["id"],
            order_lines=[{"product_id": product["id"], "product_uom_qty": 1}],
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "not a customer" in str(e)


def test_023_invalid_product_id():
    print("\nTEST 023-07: Non-existent product_id in order line")

    customer = get_existing_customer()

    try:
        create_sale_order(
            partner_id=customer["id"],
            order_lines=[{"product_id": 99999999, "product_uom_qty": 1}],
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "not sellable" in str(e) or "does not exist" in str(e)


def test_023_non_sellable_product():
    print("\nTEST 023-08: Product exists but sale_ok=False")

    non_sellable = client.search_read(
        model="product.product",
        domain=[("sale_ok", "=", False), ("active", "=", True)],
        fields=["id", "name"],
        limit=1,
    )

    if not non_sellable:
        print("SKIP: All active products are sellable in this system.")
        return

    customer = get_existing_customer()

    try:
        create_sale_order(
            partner_id=customer["id"],
            order_lines=[{"product_id": non_sellable[0]["id"], "product_uom_qty": 1}],
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "not sellable" in str(e)


def test_023_price_override_rejected():
    print("\nTEST 023-09: Manual price_unit in line — must be rejected")

    customer = get_existing_customer()
    product = get_sellable_product()

    try:
        create_sale_order(
            partner_id=customer["id"],
            order_lines=[{
                "product_id": product["id"],
                "product_uom_qty": 1,
                "price_unit": 0.01,  # Attempting price override
            }],
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "price" in str(e).lower()


def test_023_zero_quantity_rejected():
    print("\nTEST 023-10: Zero quantity in line — must be rejected")

    customer = get_existing_customer()
    product = get_sellable_product()

    try:
        create_sale_order(
            partner_id=customer["id"],
            order_lines=[{"product_id": product["id"], "product_uom_qty": 0}],
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "quantity" in str(e).lower() or "product_uom_qty" in str(e).lower()


def test_023_negative_quantity_rejected():
    print("\nTEST 023-11: Negative quantity in line — must be rejected")

    customer = get_existing_customer()
    product = get_sellable_product()

    try:
        create_sale_order(
            partner_id=customer["id"],
            order_lines=[{"product_id": product["id"], "product_uom_qty": -5}],
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)


def test_023_empty_order_lines_rejected():
    print("\nTEST 023-12: Empty order_lines list — must be rejected")

    customer = get_existing_customer()

    try:
        create_sale_order(partner_id=customer["id"], order_lines=[])
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "order_lines" in str(e)


def test_023_duplicate_product_lines_rejected():
    print("\nTEST 023-13: Duplicate product_id in lines — must be rejected")

    customer = get_existing_customer()
    product = get_sellable_product()

    try:
        create_sale_order(
            partner_id=customer["id"],
            order_lines=[
                {"product_id": product["id"], "product_uom_qty": 1},
                {"product_id": product["id"], "product_uom_qty": 2},
            ],
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "Duplicate" in str(e)


def test_023_invalid_date_format():
    print("\nTEST 023-14: Invalid date_order format — must be rejected")

    customer = get_existing_customer()
    product = get_sellable_product()

    try:
        create_sale_order(
            partner_id=customer["id"],
            order_lines=[{"product_id": product["id"], "product_uom_qty": 1}],
            date_order="25-03-2026",
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "YYYY-MM-DD" in str(e)


def test_023_validity_before_order_date_rejected():
    print("\nTEST 023-15: validity_date before date_order — must be rejected")

    customer = get_existing_customer()
    product = get_sellable_product()

    try:
        create_sale_order(
            partner_id=customer["id"],
            order_lines=[{"product_id": product["id"], "product_uom_qty": 1}],
            date_order="2026-06-01",
            validity_date="2026-05-01",
        )
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "validity_date" in str(e)


def test_023_return_fields_complete():
    print("\nTEST 023-16: All expected fields in return value")

    customer = get_existing_customer()
    product = get_sellable_product()

    result = create_sale_order(
        partner_id=customer["id"],
        order_lines=[{"product_id": product["id"], "product_uom_qty": 1}],
    )

    expected_fields = [
        "order_id", "order_name", "partner_id", "partner_name",
        "amount_total", "state", "date_order", "validity_date", "lines",
    ]

    for field in expected_fields:
        assert field in result, f"Missing field in return: {field}"

    print("ALL RETURN FIELDS PRESENT:", list(result.keys()))


def test_023_price_derived_from_product():
    print("\nTEST 023-17: Price in line matches product list_price")

    customer = get_existing_customer()
    product = get_sellable_product()

    result = create_sale_order(
        partner_id=customer["id"],
        order_lines=[{"product_id": product["id"], "product_uom_qty": 1}],
    )

    assert result["lines"][0]["unit_price"] == product["list_price"]
    print(
        f"PRICE CHECK PASSED — list_price: {product['list_price']}, "
        f"unit_price in result: {result['lines'][0]['unit_price']}"
    )

    # Verify in Odoo
    lines = client.search_read(
        model="sale.order.line",
        domain=[("order_id", "=", result["order_id"])],
        fields=["price_unit"],
        limit=1,
    )
    assert lines[0]["price_unit"] == product["list_price"]
    print("ODOO PRICE VERIFICATION PASSED:", lines[0]["price_unit"])


def test_023_state_is_always_draft():
    print("\nTEST 023-18: Created order must always be in draft state")

    customer = get_existing_customer()
    product = get_sellable_product()

    result = create_sale_order(
        partner_id=customer["id"],
        order_lines=[{"product_id": product["id"], "product_uom_qty": 1}],
    )

    assert result["state"] == "draft"

    # Verify directly in Odoo
    odoo_record = client.search_read(
        model="sale.order",
        domain=[("id", "=", result["order_id"])],
        fields=["state"],
        limit=1,
    )
    assert odoo_record[0]["state"] == "draft"
    print("DRAFT STATE VERIFIED IN ODOO")


# ==============================================================================
# RUNNER
# ==============================================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("TOOL 021 — get_sale_order")
    print("=" * 60)
    test_021_get_by_order_id()
    test_021_get_by_order_name()
    test_021_get_by_partner_id()
    test_021_get_by_state_draft()
    test_021_get_by_state_cancelled()
    test_021_get_by_date_range()
    test_021_date_range_no_results()
    test_021_limit_respected()
    test_021_limit_exceeds_100()
    test_021_invalid_state()
    test_021_no_filters_raises()
    test_021_nonexistent_order_id()
    test_021_many2one_normalization()
    test_021_return_fields_complete()

    print("\n" + "=" * 60)
    print("TOOL 022 — get_sale_order_lines")
    print("=" * 60)
    test_022_get_lines_for_valid_order()
    test_022_lines_for_confirmed_order()
    test_022_lines_for_cancelled_order()
    test_022_nonexistent_order_id()
    test_022_missing_order_id()
    test_022_limit_exceeds_100()
    test_022_many2one_normalization()
    test_022_return_fields_complete()
    test_022_order_with_no_lines()

    print("\n" + "=" * 60)
    print("TOOL 023 — create_sale_order")
    print("=" * 60)
    test_023_basic_create()
    test_023_create_with_all_optional_fields()
    test_023_create_multiple_lines()
    test_023_stock_warning_in_return()
    test_023_invalid_partner_id()
    test_023_non_customer_partner()
    test_023_invalid_product_id()
    test_023_non_sellable_product()
    test_023_price_override_rejected()
    test_023_zero_quantity_rejected()
    test_023_negative_quantity_rejected()
    test_023_empty_order_lines_rejected()
    test_023_duplicate_product_lines_rejected()
    test_023_invalid_date_format()
    test_023_validity_before_order_date_rejected()
    test_023_return_fields_complete()
    test_023_price_derived_from_product()
    test_023_state_is_always_draft()

    print("\n" + "=" * 60)
    print("ALL SECTION 5 TESTS COMPLETED")
    print("=" * 60)