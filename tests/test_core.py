"""
NeevDB - Full Test Suite (Phase 1 + Phase 2)
Run this file to verify everything is working correctly.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from neevdb import NeevDB


def run_tests():
    print("=" * 55)
    print("  NeevDB - Full Test Suite")
    print("=" * 55)

    db = NeevDB("test_database.json")
    db.create_table("users")

    db.insert("users", {"name": "Alice",  "age": 25, "city": "Mumbai"})
    db.insert("users", {"name": "Bob",    "age": 17, "city": "Delhi"})
    db.insert("users", {"name": "Carol",  "age": 30, "city": "Pune"})
    db.insert("users", {"name": "Dev",    "age": 22, "city": "Mumbai"})
    db.insert("users", {"name": "Esha",   "age": 19, "city": "Delhi"})

    print("\n── Phase 1: CRUD ──")

    print("\n[Test 1] find_all...")
    assert len(db.find_all("users")) == 5
    print("  PASSED ✓")

    print("\n[Test 2] find with condition...")
    assert len(db.find("users", lambda r: r["age"] > 18)) == 4
    print("  PASSED ✓")

    print("\n[Test 3] update...")
    db.update("users", lambda r: r["name"] == "Bob", {"age": 20})
    assert db.find("users", lambda r: r["name"] == "Bob")[0]["age"] == 20
    print("  PASSED ✓")

    print("\n[Test 4] delete...")
    db.delete("users", lambda r: r["name"] == "Esha")
    assert db.count("users") == 4
    print("  PASSED ✓")

    print("\n── Phase 2: Query Engine ──")

    print("\n[Test 5] SELECT * FROM users...")
    assert len(db.query("SELECT * FROM users")) == 4
    print("  PASSED ✓")

    print("\n[Test 6] WHERE age > 20...")
    assert len(db.query("SELECT * FROM users WHERE age > 20")) == 3
    print("  PASSED ✓")

    print("\n[Test 7] WHERE city = Mumbai...")
    assert len(db.query("SELECT * FROM users WHERE city = Mumbai")) == 2
    print("  PASSED ✓")

    print("\n[Test 8] ORDER BY age ASC...")
    results = db.query("SELECT * FROM users ORDER BY age")
    ages = [r["age"] for r in results]
    assert ages == sorted(ages)
    print("  PASSED ✓")

    print("\n[Test 9] ORDER BY age DESC...")
    results = db.query("SELECT * FROM users ORDER BY age DESC")
    ages = [r["age"] for r in results]
    assert ages == sorted(ages, reverse=True)
    print("  PASSED ✓")

    print("\n[Test 10] LIMIT 2...")
    assert len(db.query("SELECT * FROM users LIMIT 2")) == 2
    print("  PASSED ✓")

    print("\n[Test 11] SELECT specific columns...")
    results = db.query("SELECT name, city FROM users")
    assert "age" not in results[0] and "name" in results[0]
    print("  PASSED ✓")

    print("\n[Test 12] WHERE + ORDER BY + LIMIT combined...")
    results = db.query("SELECT * FROM users WHERE age > 20 ORDER BY name LIMIT 2")
    assert len(results) == 2
    print("  PASSED ✓")

    db.drop_table("users")
    if os.path.exists("test_database.json"):
        os.remove("test_database.json")

    print("\n" + "=" * 55)
    print("  All 12 tests PASSED! NeevDB Phase 2 complete! 🚀")
    print("=" * 55)


if __name__ == "__main__":
    run_tests()