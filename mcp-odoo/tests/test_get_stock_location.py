from tools.erp import get_stock_location
from odoo_client import OdooClient

client = OdooClient()


def get_existing_internal_location():
    """
    Helper to fetch a real internal location from database.
    """
    locations = client.search_read(
        model="stock.location",
        domain=[("usage", "=", "internal")],
        fields=["id", "name"],
        limit=1,
    )
    return locations[0] if locations else None


# ---------------------------------------------------------
# TEST 1: List all internal locations (default behavior)
# ---------------------------------------------------------

def test_list_all_internal_locations():
    print("\nTEST 1: List all internal locations")

    result = get_stock_location()

    print("AI TOOL OUTPUT:")
    print(result)

    assert isinstance(result, list)
    assert len(result) >= 1

    for loc in result:
        assert loc["usage"] == "internal"


# ---------------------------------------------------------
# TEST 2: Filter by valid location_id
# ---------------------------------------------------------

def test_filter_by_location_id():
    print("\nTEST 2: Filter by valid location_id")

    location = get_existing_internal_location()
    assert location is not None

    result = get_stock_location(location_id=location["id"])

    print("AI TOOL OUTPUT:")
    print(result)

    assert len(result) == 1
    assert result[0]["id"] == location["id"]


# ---------------------------------------------------------
# TEST 3: Filter by name (partial match)
# ---------------------------------------------------------

def test_filter_by_name():
    print("\nTEST 3: Filter by name")

    location = get_existing_internal_location()
    assert location is not None

    partial_name = location["name"][:3]

    result = get_stock_location(name=partial_name)

    print("AI TOOL OUTPUT:")
    print(result)

    assert len(result) >= 1

    for loc in result:
        assert partial_name.lower() in loc["name"].lower()


# ---------------------------------------------------------
# TEST 4: Limit enforcement
# ---------------------------------------------------------

def test_limit_enforcement():
    print("\nTEST 4: Limit enforcement")

    result = get_stock_location(limit=2)

    print("AI TOOL OUTPUT:")
    print(result)

    assert len(result) <= 2


# ---------------------------------------------------------
# TEST 5: Invalid limit (too high)
# ---------------------------------------------------------

def test_invalid_limit_high():
    print("\nTEST 5: Invalid limit (too high)")

    try:
        get_stock_location(limit=101)
    except ValueError as e:
        print("EXPECTED FAILURE:", e)
        assert "Limit must be between" in str(e)


# ---------------------------------------------------------
# TEST 6: Invalid limit (zero)
# ---------------------------------------------------------

def test_invalid_limit_zero():
    print("\nTEST 6: Invalid limit (zero)")

    try:
        get_stock_location(limit=0)
    except ValueError as e:
        print("EXPECTED FAILURE:", e)
        assert "Limit must be between" in str(e)


# ---------------------------------------------------------
# TEST 7: Invalid location_id (negative)
# ---------------------------------------------------------

def test_invalid_location_id():
    print("\nTEST 7: Invalid location_id")

    try:
        get_stock_location(location_id=-5)
    except ValueError as e:
        print("EXPECTED FAILURE:", e)
        assert "location_id must be positive" in str(e)


# ---------------------------------------------------------
# TEST 8: Invalid name (empty string)
# ---------------------------------------------------------

def test_invalid_name():
    print("\nTEST 8: Invalid name")

    try:
        get_stock_location(name="")
    except ValueError as e:
        print("EXPECTED FAILURE:", e)
        assert "name must be non-empty" in str(e)


# ---------------------------------------------------------
# TEST 9: Nonexistent location_id
# ---------------------------------------------------------

def test_nonexistent_location():
    print("\nTEST 9: Nonexistent location_id")

    result = get_stock_location(location_id=99999999)

    print("AI TOOL OUTPUT:")
    print(result)

    assert result == []


# ---------------------------------------------------------
# RUN ALL TESTS
# ---------------------------------------------------------

if __name__ == "__main__":
    test_list_all_internal_locations()
    test_filter_by_location_id()
    test_filter_by_name()
    test_limit_enforcement()
    test_invalid_limit_high()
    test_invalid_limit_zero()
    test_invalid_location_id()
    test_invalid_name()
    test_nonexistent_location()

    print("\nget_stock_location TESTS COMPLETED\n")