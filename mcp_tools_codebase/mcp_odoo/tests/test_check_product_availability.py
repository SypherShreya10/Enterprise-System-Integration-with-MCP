import datetime
from tools.erp import check_product_availability
from odoo_client import OdooClient

client = OdooClient()


def get_stockable_product():
    product = client.search_read(
        model="product.product",
        domain=[
            ("name", "=", "Large Cabinet"),
            ("active", "=", True),
        ],
        fields=["id", "name", "type"],
        limit=1,
    )

    return product[0] if product else None


def test_basic_stock_sufficient():
    print("\nTEST 1: Stock sufficient")

    product = get_stockable_product()
    assert product is not None

    result = check_product_availability(
        product_id=product["id"],
        quantity=1,
    )

    print("AI TOOL OUTPUT:")
    print(result)

    assert "can_fulfill" in result
    assert isinstance(result["can_fulfill"], bool)


def test_large_quantity_shortage():
    print("\nTEST 2: Large quantity shortage")

    product = get_stockable_product()
    assert product is not None

    result = check_product_availability(
        product_id=product["id"],
        quantity=999999,
    )

    print("AI TOOL OUTPUT:")
    print(result)

    assert result["can_fulfill"] is False
    assert result["shortage"] > 0


def test_with_date_required():
    print("\nTEST 3: With date_required")

    product = get_stockable_product()
    assert product is not None

    future_date = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()

    result = check_product_availability(
        product_id=product["id"],
        quantity=5,
        date_required=future_date,
    )

    print("AI TOOL OUTPUT:")
    print(result)

    assert "date_required" in result
    assert result["date_required"] == future_date


def test_invalid_product_id():
    print("\nTEST 4: Invalid product_id")

    try:
        check_product_availability(product_id=-1, quantity=5)
    except ValueError as e:
        print("EXPECTED FAILURE:", e)
        assert "product_id" in str(e)


def test_invalid_quantity():
    print("\nTEST 5: Invalid quantity")

    try:
        check_product_availability(product_id=1, quantity=-10)
    except ValueError as e:
        print("EXPECTED FAILURE:", e)
        assert "quantity" in str(e)


def test_invalid_date_format():
    print("\nTEST 6: Invalid date format")

    product = get_stockable_product()
    assert product is not None

    try:
        check_product_availability(
            product_id=product["id"],
            quantity=5,
            date_required="2026/12/01",
        )
    except ValueError as e:
        print("EXPECTED FAILURE:", e)
        assert "YYYY-MM-DD" in str(e)


def test_nonexistent_product():
    print("\nTEST 7: Nonexistent product")

    try:
        check_product_availability(product_id=99999999, quantity=5)
    except ValueError as e:
        print("EXPECTED FAILURE:", e)
        assert "not found" in str(e)


if __name__ == "__main__":
    test_basic_stock_sufficient()
    test_large_quantity_shortage()
    test_with_date_required()
    test_invalid_product_id()
    test_invalid_quantity()
    test_invalid_date_format()
    test_nonexistent_product()

    print("\ncheck_product_availability TESTS COMPLETED\n")