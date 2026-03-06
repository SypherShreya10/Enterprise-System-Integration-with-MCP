# tests/test_get_manufacturing_order.py

from tools.erp import get_manufacturing_order


def test_get_manufacturing_order():

    print("=" * 70)
    print("Testing get_manufacturing_order tool")
    print("=" * 70)

    # -------------------------------------------------------------
    # Test 1: Fetch manufacturing orders by product
    # -------------------------------------------------------------
    print("\nTest 1: Filter by product_id")

    result = get_manufacturing_order(product_id=1)

    print(result)
    assert isinstance(result, list)

    if result:
        assert "product_id" in result[0]

    print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 2: Filter by state
    # -------------------------------------------------------------
    print("\nTest 2: Filter by state")

    result = get_manufacturing_order(state="confirmed")

    print(result)
    assert isinstance(result, list)

    print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 3: Date range filtering
    # -------------------------------------------------------------
    print("\nTest 3: Date range filtering")

    result = get_manufacturing_order(
        date_from="2024-01-01",
        date_to="2099-01-01"
    )

    print(result)
    assert isinstance(result, list)

    print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 4: Invalid state
    # -------------------------------------------------------------
    print("\nTest 4: Invalid state")

    try:
        get_manufacturing_order(state="invalid_state")
        assert False, "Expected validation error"

    except Exception as e:
        print(f"  Correctly rejected: {e}")
        print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 5: Invalid date range
    # -------------------------------------------------------------
    print("\nTest 5: Invalid date range")

    try:
        get_manufacturing_order(
            date_from="2025-01-01",
            date_to="2024-01-01"
        )
        assert False

    except Exception as e:
        print(f"  Correctly rejected: {e}")
        print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 6: No filters provided
    # -------------------------------------------------------------
    print("\nTest 6: Missing filters")

    try:
        get_manufacturing_order()
        assert False

    except Exception as e:
        print(f"  Correctly rejected: {e}")
        print("  ✅ PASS")


    print("\n" + "=" * 70)
    print("✅ ALL get_manufacturing_order TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    test_get_manufacturing_order()