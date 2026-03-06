# tests/test_check_manufacturing_capacity.py

from tools.erp import check_manufacturing_capacity


def test_check_manufacturing_capacity():

    print("=" * 70)
    print("Testing check_manufacturing_capacity tool")
    print("=" * 70)

    # -------------------------------------------------------------
    # Test 1: Basic capacity check
    # -------------------------------------------------------------
    print("\nTest 1: Basic capacity query")

    result = check_manufacturing_capacity(
        date_from="2024-01-01",
        date_to="2099-01-01"
    )

    print(result)

    assert "scheduled_orders" in result
    assert "total_scheduled_qty" in result

    print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 2: Capacity with theoretical limit
    # -------------------------------------------------------------
    print("\nTest 2: Capacity with theoretical limit")

    result = check_manufacturing_capacity(
        date_from="2024-01-01",
        date_to="2099-01-01",
        theoretical_capacity=1000
    )

    print(result)

    assert "estimated_capacity_used" in result

    print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 3: Invalid date format
    # -------------------------------------------------------------
    print("\nTest 3: Invalid date format")

    try:
        check_manufacturing_capacity(
            date_from="invalid",
            date_to="2024-01-01"
        )

        assert False

    except Exception as e:
        print(f"  Correctly rejected: {e}")
        print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 4: Invalid capacity
    # -------------------------------------------------------------
    print("\nTest 4: Invalid theoretical capacity")

    try:
        check_manufacturing_capacity(
            date_from="2024-01-01",
            date_to="2099-01-01",
            theoretical_capacity=-100
        )

        assert False

    except Exception as e:
        print(f"  Correctly rejected: {e}")
        print("  ✅ PASS")


    print("\n" + "=" * 70)
    print("✅ ALL check_manufacturing_capacity TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    test_check_manufacturing_capacity()