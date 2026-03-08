"""
Pre-integration tests for Tool 017: get_product

Covers:
- All valid filter combinations
- Limit enforcement
- Invalid inputs
- Edge cases
- Real output visibility
"""

from tools.erp import get_product
from odoo_client import OdooClient
import traceback

client = OdooClient()


def print_header(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def get_any_active_product():
    records = client.search_read(
        model="product.product",
        domain=[("active", "=", True), ("sale_ok", "=", True)],
        fields=["id", "name", "default_code", "categ_id", "type"],
        limit=1,
    )
    return records[0] if records else None


# -------------------------------------------------------------
# POSITIVE TESTS
# -------------------------------------------------------------

def test_filter_by_product_id():
    print_header("TEST 1: Filter by product_id")

    product = get_any_active_product()
    assert product, "No active sellable product found"

    result = get_product(product_id=product["id"])

    print("AI TOOL OUTPUT:")
    for r in result:
        print(r)


def test_filter_by_name():
    print_header("TEST 2: Filter by name")

    result = get_product(name="a")

    print("AI TOOL OUTPUT:")
    for r in result:
        print(r)


def test_filter_by_default_code():
    print_header("TEST 3: Filter by default_code")

    result = get_product(default_code="")

    # This should fail — default_code cannot be empty
    print("This line should not execute")


def test_filter_by_category():
    print_header("TEST 4: Filter by category")

    product = get_any_active_product()
    assert product and product["categ_id"]

    result = get_product(categ_id=product["categ_id"][0])

    print("AI TOOL OUTPUT:")
    for r in result:
        print(r)


def test_filter_by_type():
    print_header("TEST 5: Filter by type")

    result = get_product(type="product")

    print("AI TOOL OUTPUT:")
    for r in result:
        print(r)


def test_combined_filters():
    print_header("TEST 6: Combined Filters")

    result = get_product(name="a", type="product", limit=5)

    print("AI TOOL OUTPUT:")
    for r in result:
        print(r)


def test_limit_enforcement():
    print_header("TEST 7: Limit Enforcement")

    result = get_product(name="a", limit=2)
    print(f"Returned {len(result)} records (limit=2)")


# -------------------------------------------------------------
# NEGATIVE / EDGE TESTS
# -------------------------------------------------------------

def test_no_filter_should_fail():
    print_header("TEST 8: No filter should fail")

    try:
        get_product()
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_invalid_limit():
    print_header("TEST 9: Invalid limit")

    try:
        get_product(name="a", limit=101)
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_invalid_type():
    print_header("TEST 10: Invalid type")

    try:
        get_product(type="invalid")
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_invalid_product_id():
    print_header("TEST 11: Invalid product_id")

    try:
        get_product(product_id=-1)
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


# -------------------------------------------------------------
# RUNNER
# -------------------------------------------------------------

if __name__ == "__main__":

    tests = [
        test_filter_by_product_id,
        test_filter_by_name,
        test_filter_by_category,
        test_filter_by_type,
        test_combined_filters,
        test_limit_enforcement,
        test_no_filter_should_fail,
        test_invalid_limit,
        test_invalid_type,
        test_invalid_product_id,
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
    print("get_product TEST SUMMARY")
    print("=" * 90)
    print("Failures:", failures)