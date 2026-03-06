# tests/test_get_bill_of_materials.py

from tools.erp import get_bill_of_materials


def test_get_bill_of_materials():

    print("=" * 70)
    print("Testing get_bill_of_materials tool")
    print("=" * 70)


    # -------------------------------------------------------------
    # Test 1: Valid product
    # -------------------------------------------------------------
    print("\nTest 1: Valid product BOM")

    result = get_bill_of_materials(product_id=1)

    print(result)

    assert "product_id" in result
    assert "bom_line_ids" in result

    print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 2: Component structure
    # -------------------------------------------------------------
    print("\nTest 2: Component structure validation")

    result = get_bill_of_materials(product_id=1)

    for comp in result["bom_line_ids"]:
        assert "component_id" in comp
        assert "component_name" in comp

    print("  ✅ PASS")


    # -------------------------------------------------------------
    # Test 3: Non-existent product
    # -------------------------------------------------------------
    print("\nTest 3: Invalid product")

    try:
        get_bill_of_materials(product_id=999999)

        assert False

    except Exception as e:
        print(f"  Correctly rejected: {e}")
        print("  ✅ PASS")


    print("\n" + "=" * 70)
    print("✅ ALL get_bill_of_materials TESTS PASSED")
    print("=" * 70)

if __name__ == "__main__":
    test_get_bill_of_materials()