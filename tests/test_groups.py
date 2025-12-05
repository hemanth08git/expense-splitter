from app.main import app, init_db
import os
import sqlite3

def setup_module(module):
    # Fresh DB for this test run
    db_path = os.path.join(os.path.dirname(__file__), "..", "app", "expense.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db()

def test_create_group_flow():
    client = app.test_client()

    # 1) Register owner user
    resp = client.post(
        "/user/register",
        json={"email": "owner@test.com", "password": "pass123"},
    )
    assert resp.status_code == 201
    user_id = resp.get_json()["user_id"]

    # 2) Create group for that user
    resp = client.post(
        "/group",
        json={"name": "Test Group", "owner": user_id},
    )
    assert resp.status_code == 201
    group_id = resp.get_json()["group_id"]

    # 3) Fetch groups
    resp = client.get("/groups")
    assert resp.status_code == 200
    groups = resp.get_json()
    assert any(g["id"] == group_id for g in groups)

    # 4) Check members
    resp = client.get(f"/group/{group_id}/members")
    assert resp.status_code == 200
    members = resp.get_json()
    assert any(m["id"] == user_id for m in members)
