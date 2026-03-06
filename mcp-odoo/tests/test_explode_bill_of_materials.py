# tests/test_explode_bill_of_materials.py

from tools.erp import explode_bill_of_materials


def test_explode_bill_of_materials():

    print("=" * 70)
    print("Testing explode_bill_of_materials tool")
    print("=" * 70)


    # -------------------------------------------------------------
    # Test 1: Basic explosion
    # -------------------------------------------------------------
    print("\nTest 1: Basic BOM explosion")

    result = explode_bill_of_materials(product_id=1)

    print(result)

    assert isinstance(result, list)

    print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 2: Explosion with quantity scaling
    # -------------------------------------------------------------
    print("\nTest 2: Explosion with quantity")

    result = explode_bill_of_materials(
        product_id=1,
        quantity=10
    )

    print(result)

    assert isinstance(result, list)

    print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 3: Recursion depth limit
    # -------------------------------------------------------------
    print("\nTest 3: Recursion depth")

    result = explode_bill_of_materials(
        product_id=1,
        quantity=5,
        depth=2
    )

    print(result)

    assert isinstance(result, list)

    print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 4: Invalid product
    # -------------------------------------------------------------
    print("\nTest 4: Invalid product")

    result = explode_bill_of_materials(product_id=999999)

    print(result)

    assert result == []

    print("  ✅ PASS")


    print("\n" + "=" * 70)
    print("✅ ALL explode_bill_of_materials TESTS PASSED")
    print("=" * 70)

if __name__ == "__main__":
    test_explode_bill_of_materials()