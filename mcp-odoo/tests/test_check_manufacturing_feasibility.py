# tests/test_check_manufacturing_feasibility.py

from tools.erp import check_manufacturing_feasibility


def test_check_manufacturing_feasibility():

    print("=" * 70)
    print("Testing check_manufacturing_feasibility tool")
    print("=" * 70)


    # -------------------------------------------------------------
    # Test 1: Basic feasibility check
    # -------------------------------------------------------------
    print("\nTest 1: Basic feasibility")

    result = check_manufacturing_feasibility(
        product_id=1,
        quantity=10
    )

    print(result)

    assert "feasible" in result
    assert "materials" in result
    assert "blocking_components" in result
    assert "max_producible_quantity" in result
    assert "capacity" in result

    print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 2: Large quantity
    # -------------------------------------------------------------
    print("\nTest 2: Large production quantity")

    result = check_manufacturing_feasibility(
        product_id=1,
        quantity=10000
    )

    print(result)

    assert "feasible" in result
    assert "reason" in result
    assert "materials" in result
    assert "blocking_components" in result
    assert "max_producible_quantity" in result
    assert "capacity" in result
    print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 3: Invalid product
    # -------------------------------------------------------------
    print("\nTest 3: Invalid product")

    try:
        check_manufacturing_feasibility(
            product_id=999999,
            quantity=10
        )

        assert False

    except Exception as e:
        print(f"  Correctly rejected: {e}")
        print("  ✅ PASS")


    print("\n" + "=" * 70)
    print("✅ ALL check_manufacturing_feasibility TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    test_check_manufacturing_feasibility()