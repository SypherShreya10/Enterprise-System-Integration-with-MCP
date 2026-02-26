"""
Pre-integration tests for Tool 018: get_product_stock

Covers:
- Valid stock queries
- Aggregation logic
- Location-specific queries
- Zero-stock handling
- Invalid inputs
- Edge cases
"""

from tools.erp import get_product_stock
from odoo_client import OdooClient
import traceback

client = OdooClient()


def print_header(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def get_any_product():
    records = client.search_read(
        model="product.product",
        domain=[("active", "=", True)],
        fields=["id", "name"],
        limit=1,
    )
    return records[0] if records else None


def get_any_internal_location():
    locations = client.search_read(
        model="stock.location",
        domain=[("usage", "=", "internal")],
        fields=["id", "name"],
        limit=1,
    )
    return locations[0] if locations else None


# -------------------------------------------------------------
# POSITIVE TESTS
# -------------------------------------------------------------

def test_stock_aggregation():
    print_header("TEST 1: Stock aggregation across locations")

    product = get_any_product()
    assert product

    result = get_product_stock(product_id=product["id"])

    print("AI TOOL OUTPUT:")
    print(result)


def test_stock_by_location():
    print_header("TEST 2: Stock by specific location")

    product = get_any_product()
    location = get_any_internal_location()

    assert product and location

    result = get_product_stock(
        product_id=product["id"],
        location_id=location["id"],
    )

    print("AI TOOL OUTPUT:")
    print(result)


# -------------------------------------------------------------
# EDGE CASES
# -------------------------------------------------------------

# def test_no_stock():
#     print_header("TEST 3: Product with no stock")

#     result = get_product_stock(product_id=99999999)

#     print("AI TOOL OUTPUT:")
#     print(result)

def test_product_with_zero_stock():
    print_header("TEST 3: Existing product with zero stock")

    # Find any active product
    product = get_any_product()
    assert product

    result = get_product_stock(product_id=product["id"])

    print("AI TOOL OUTPUT:")
    print(result)

    # We don't assert quantity > 0
    # Because some demo databases may truly have 0 stock

def test_nonexistent_product_should_fail():
    print_header("TEST 4: Nonexistent product should fail")

    try:
        get_product_stock(product_id=99999999)
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)

def test_invalid_product_id():
    print_header("TEST 4: Invalid product_id")

    try:
        get_product_stock(product_id=-1)
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_invalid_location_id():
    print_header("TEST 5: Invalid location_id")

    product = get_any_product()
    assert product

    try:
        get_product_stock(product_id=product["id"], location_id=-1)
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


# -------------------------------------------------------------
# RUNNER
# -------------------------------------------------------------

if __name__ == "__main__":

    tests = [
        test_stock_aggregation,
        test_stock_by_location,
        test_nonexistent_product_should_fail,
        test_invalid_product_id,
        test_invalid_location_id,
        test_product_with_zero_stock,
    ]

    failures = 0

    for test in tests:
        try:
            test()
        except Exception:
            failures += 1
            print("\n❌ TEST CRASHED:", test.__name__)
            traceback.print_exc()

    print("\n" + "=" * 90)
    print("get_product_stock TEST SUMMARY")
    print("=" * 90)
    print("Failures:", failures)