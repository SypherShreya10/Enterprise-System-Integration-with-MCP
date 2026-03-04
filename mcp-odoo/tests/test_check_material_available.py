from tools.erp import check_material_availability
from odoo_client import OdooClient, ValidationError

client = OdooClient()


# ---------------------------------------------------------
# Helper: Get a valid product
# ---------------------------------------------------------

def get_existing_product():
    products = client.search_read(
        model="product.product",
        domain=[("active", "=", True)],
        fields=["id", "name"],
        limit=1,
    )

    return products[0] if products else None


# ---------------------------------------------------------
# TEST 1: Basic availability check
# ---------------------------------------------------------

def test_basic_availability():

    print("\nTEST 027-1: Basic availability check")

    product = get_existing_product()

    if not product:
        print("SKIP: No active products found.")
        return

    result = check_material_availability(
        product_id=product["id"],
        quantity_needed=10,
    )

    print("AI TOOL OUTPUT:", result)

    assert isinstance(result, dict)
    assert result["product_id"] == product["id"]
    assert "current_stock" in result
    assert "incoming_qty" in result
    assert "total_available" in result
    assert "can_fulfill" in result


# ---------------------------------------------------------
# TEST 2: Availability with date filter
# ---------------------------------------------------------

def test_date_filter():

    print("\nTEST 027-2: Availability with date filter")

    product = get_existing_product()

    if not product:
        print("SKIP")
        return

    result = check_material_availability(
        product_id=product["id"],
        quantity_needed=5,
        date_needed="2030-01-01",
    )

    print("AI TOOL OUTPUT:", result)

    assert isinstance(result, dict)
    assert result["quantity_needed"] == 5


# ---------------------------------------------------------
# TEST 3: Large quantity (likely shortage)
# ---------------------------------------------------------

def test_large_quantity_shortage():

    print("\nTEST 027-3: Large quantity shortage scenario")

    product = get_existing_product()

    if not product:
        print("SKIP")
        return

    result = check_material_availability(
        product_id=product["id"],
        quantity_needed=100000,
    )

    print("AI TOOL OUTPUT:", result)

    assert result["can_fulfill"] is False
    assert result["shortage"] >= 0


# ---------------------------------------------------------
# TEST 4: Expected availability date logic
# ---------------------------------------------------------

def test_expected_date_logic():

    print("\nTEST 027-4: Expected availability date logic")

    product = get_existing_product()

    if not product:
        print("SKIP")
        return

    result = check_material_availability(
        product_id=product["id"],
        quantity_needed=5000,
    )

    print("AI TOOL OUTPUT:", result)

    if not result["can_fulfill"]:
        assert "expected_available_date" in result


# ---------------------------------------------------------
# TEST 5: Invalid product id
# ---------------------------------------------------------

def test_invalid_product():

    print("\nTEST 027-5: Invalid product id")

    try:
        check_material_availability(
            product_id=99999999,
            quantity_needed=10,
        )
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "does not exist" in str(e)


# ---------------------------------------------------------
# TEST 6: Negative quantity
# ---------------------------------------------------------

def test_negative_quantity():

    print("\nTEST 027-6: Negative quantity")

    product = get_existing_product()

    if not product:
        print("SKIP")
        return

    try:
        check_material_availability(
            product_id=product["id"],
            quantity_needed=-5,
        )
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "must be positive" in str(e)


# ---------------------------------------------------------
# TEST 7: Invalid date format
# ---------------------------------------------------------

def test_invalid_date():

    print("\nTEST 027-7: Invalid date format")

    product = get_existing_product()

    if not product:
        print("SKIP")
        return

    try:
        check_material_availability(
            product_id=product["id"],
            quantity_needed=10,
            date_needed="10-12-2025",
        )
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "YYYY-MM-DD" in str(e)


# ---------------------------------------------------------
# TEST 8: Zero quantity request
# ---------------------------------------------------------

def test_zero_quantity():

    print("\nTEST 027-8: Zero quantity request")

    product = get_existing_product()

    if not product:
        print("SKIP")
        return

    try:
        check_material_availability(
            product_id=product["id"],
            quantity_needed=0,
        )
    except ValidationError as e:
        print("EXPECTED FAILURE:", e)
        assert "must be positive" in str(e)


# ---------------------------------------------------------
# RUN ALL TESTS
# ---------------------------------------------------------

if __name__ == "__main__":

    test_basic_availability()
    test_date_filter()
    test_large_quantity_shortage()
    test_expected_date_logic()
    test_invalid_product()
    test_negative_quantity()
    test_invalid_date()
    test_zero_quantity()

    print("\ncheck_material_availability TESTS COMPLETED\n")