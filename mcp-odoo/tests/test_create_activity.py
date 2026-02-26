"""
Pre-integration tests for Tool 015: create_activity

This test suite simulates how different roles (admin, manager, user)
would experience the tool, and prints real outputs exactly as an AI
agent would see them.
"""

from tools.crm import create_activity
from odoo_client import OdooClient
import datetime
import traceback

client = OdooClient()


def print_header(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


# ------------------------------------------------------------------
# Helper discovery functions
# ------------------------------------------------------------------

def get_activity_type():
    types = client.search_read(
        model="mail.activity.type",
        domain=[("id", "!=", 0)],
        fields=["id", "name"],
        limit=1,
        apply_company_scope=False,
    )
    return types[0] if types else None


def get_active_internal_users():
    return client.search_read(
        model="res.users",
        domain=[
            ("active", "=", True),
            ("share", "=", False),
            ("id", "!=", 0),
        ],
        fields=["id", "name"],
        limit=10,
    )


def get_any_active_lead():
    leads = client.search_read(
        model="crm.lead",
        domain=[("active", "=", True), ("id", "!=", 0)],
        fields=["id", "name"],
        limit=1,
    )
    return leads[0] if leads else None


# ------------------------------------------------------------------
# TESTS
# ------------------------------------------------------------------

def test_successful_activity_creation_for_each_user():
    print_header("TEST 1: Successful activity creation for each user role")

    activity_type = get_activity_type()
    lead = get_any_active_lead()
    users = get_active_internal_users()

    assert activity_type, "No activity type found"
    assert lead, "No active lead found"
    assert users, "No active users found"

    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    for user in users:
        print("\n--- Creating activity for user ---")
        print(f"User ID   : {user['id']}")
        print(f"User Name : {user['name']}")
        # print(f"Groups    : {user['groups_id']}")

        try:
            result = create_activity(
                activity_type_id=activity_type["id"],
                user_id=user["id"],
                date_deadline=tomorrow,
                res_model="crm.lead",
                res_id=lead["id"],
                summary="Follow-up call",
                note=f"Auto-created test activity for {user['name']}",
            )

            print("\nAI TOOL OUTPUT:")
            for k, v in result.items():
                print(f"  {k}: {v}")

        except Exception as e:
            print("\n❌ FAILED FOR THIS USER")
            print(f"Reason: {e}")


def test_invalid_activity_type():
    print_header("TEST 2: Invalid activity_type_id")

    lead = get_any_active_lead()
    user = get_active_internal_users()[0]
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    try:
        create_activity(
            activity_type_id=999999,
            user_id=user["id"],
            date_deadline=tomorrow,
            res_model="crm.lead",
            res_id=lead["id"],
        )
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_inactive_user_blocked():
    print_header("TEST 3: Inactive user should be blocked")

    inactive_users = client.search_read(
        model="res.users",
        domain=[("active", "=", False)],
        fields=["id", "name"],
        limit=1,
    )

    if not inactive_users:
        print("SKIP: No inactive users found")
        return

    lead = get_any_active_lead()
    activity_type = get_activity_type()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    try:
        create_activity(
            activity_type_id=activity_type["id"],
            user_id=inactive_users[0]["id"],
            date_deadline=tomorrow,
            res_model="crm.lead",
            res_id=lead["id"],
        )
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_invalid_res_model():
    print_header("TEST 4: Invalid res_model")

    user = get_active_internal_users()[0]
    activity_type = get_activity_type()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    try:
        create_activity(
            activity_type_id=activity_type["id"],
            user_id=user["id"],
            date_deadline=tomorrow,
            res_model="non.existent.model",
            res_id=1,
        )
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


def test_invalid_date_format():
    print_header("TEST 5: Invalid date format")

    user = get_active_internal_users()[0]
    activity_type = get_activity_type()
    lead = get_any_active_lead()

    try:
        create_activity(
            activity_type_id=activity_type["id"],
            user_id=user["id"],
            date_deadline="2024-99-99",
            res_model="crm.lead",
            res_id=lead["id"],
        )
    except ValueError as e:
        print("EXPECTED FAILURE:")
        print(e)


# ------------------------------------------------------------------
# RUNNER
# ------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_successful_activity_creation_for_each_user,
        test_invalid_activity_type,
        test_inactive_user_blocked,
        test_invalid_res_model,
        test_invalid_date_format,
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
        print("✅ ALL create_activity TESTS COMPLETED")
    else:
        print(f"❌ {failures} TEST(S) FAILED")
    print("=" * 90)