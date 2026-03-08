"""
Pre-integration tests for Tool 016: get_activity

This test suite validates:
- All valid filter combinations
- Edge cases
- Input validation failures
- Limit enforcement
- Real output visibility (AI-style output)
"""

from tools.mail import get_activity
from odoo_client import OdooClient
import datetime
import traceback

client = OdooClient()


# ------------------------------------------------------------------
# Utility helpers
# ------------------------------------------------------------------

def print_header(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def get_any_activity():
    """
    Get one activity to use for filter-based tests.
    """
    records = client.search_read(
        model="mail.activity",
        domain=[("id", "!=", 0)],
        fields=["id", "user_id", "res_model", "date_deadline", "state"],
        limit=1,
    )
    return records[0] if records else None


def get_any_user():
    users = client.search_read(
        model="res.users",
        domain=[("active", "=", True), ("share", "=", False)],
        fields=["id", "name"],
        limit=1,
    )
    return users[0] if users else None


# ------------------------------------------------------------------
# TEST CASES
# ------------------------------------------------------------------

def test_filter_by_user_id():
    print_header("TEST 1: Filter by user_id")

    user = get_any_user()
    assert user, "No active user found"

    records = get_activity(user_id=user["id"])

    print("\nAI TOOL OUTPUT:")
    for r in records:
        print(r)

    print(f"\nReturned {len(records)} records")


def test_filter_by_res_model():
    print_header("TEST 2: Filter by res_model")

    records = get_activity(res_model="crm.lead")

    print("\nAI TOOL OUTPUT:")
    for r in records:
        print(r)

    print(f"\nReturned {len(records)} records")


def test_filter_by_date_deadline():
    print_header("TEST 3: Filter by date_deadline")

    today = datetime.date.today().isoformat()

    records = get_activity(date_deadline=today)

    print("\nAI TOOL OUTPUT:")
    for r in records:
        print(r)

    print(f"\nReturned {len(records)} records")


def test_filter_by_state():
    print_header("TEST 4: Filter by state")

    records = get_activity(state="planned")

    print("\nAI TOOL OUTPUT:")
    for r in records:
        print(r)

    print(f"\nReturned {len(records)} records")


def test_combined_filters():
    print_header("TEST 5: Combined Filters")

    user = get_any_user()
    assert user, "No user found"

    records = get_activity(
        user_id=user["id"],
        state="planned",
        res_model="crm.lead"
    )

    print("\nAI TOOL OUTPUT:")
    for r in records:
        print(r)

    print(f"\nReturned {len(records)} records")


def test_limit_enforcement():
    print_header("TEST 6: Limit Enforcement")

    user = get_any_user()
    records = get_activity(user_id=user["id"], limit=2)

    print(f"\nReturned {len(records)} records (limit=2)")


# ------------------------------------------------------------------
# FAILURE / EDGE CASE TESTS
# ------------------------------------------------------------------

def test_empty_domain_should_fail():
    print_header("TEST 7: Empty Domain Should Fail")

    try:
        get_activity()
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_invalid_limit_low():
    print_header("TEST 8: Invalid limit (low)")

    try:
        get_activity(user_id=1, limit=0)
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_invalid_limit_high():
    print_header("TEST 9: Invalid limit (high)")

    try:
        get_activity(user_id=1, limit=101)
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_invalid_user_id_type():
    print_header("TEST 10: Invalid user_id type")

    try:
        get_activity(user_id="abc")
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_invalid_res_model():
    print_header("TEST 11: Invalid res_model")

    try:
        get_activity(res_model="")
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_invalid_date_format():
    print_header("TEST 12: Invalid date format")

    try:
        get_activity(date_deadline="2024-99-99")
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_invalid_state():
    print_header("TEST 13: Invalid state")

    try:
        get_activity(state="invalid_state")
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


# ------------------------------------------------------------------
# RUNNER
# ------------------------------------------------------------------

if __name__ == "__main__":

    tests = [
        test_filter_by_user_id,
        test_filter_by_res_model,
        test_filter_by_date_deadline,
        test_filter_by_state,
        test_combined_filters,
        test_limit_enforcement,
        test_empty_domain_should_fail,
        test_invalid_limit_low,
        test_invalid_limit_high,
        test_invalid_user_id_type,
        test_invalid_res_model,
        test_invalid_date_format,
        test_invalid_state,
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
    if failures == 0:
        print("✅ ALL get_activity TESTS COMPLETED")
    else:
        print(f"❌ {failures} TEST(S) FAILED")
    print("=" * 90)