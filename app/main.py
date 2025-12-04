from flask import Flask, request, jsonify
from non_crud_lib.settlement import calculate_settlement
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "expense.db")


def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Users table
        c.execute(
            """CREATE TABLE users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   email TEXT UNIQUE,
                   password TEXT
               )"""
        )
        # Groups table
        c.execute(
            """CREATE TABLE groups (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT,
                   owner INTEGER
               )"""
        )
        # Group membership (many-to-many)
        c.execute(
            """CREATE TABLE group_users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   group_id INTEGER,
                   user_id INTEGER
               )"""
        )
        # Expenses table
        c.execute(
            """CREATE TABLE expenses (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   group_id INTEGER,
                   payer INTEGER,
                   amount REAL,
                   description TEXT
               )"""
        )
        conn.commit()
        conn.close()


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


@app.route("/")
def index():
    return jsonify({"status": "running"})



# User management (CRUD)

@app.route("/user/register", methods=["POST"])
def register_user():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    hashed = generate_password_hash(password)

    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed))
        conn.commit()
        user_id = c.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "user already exists"}), 400

    conn.close()
    return jsonify({"status": "user created", "user_id": user_id}), 201


@app.route("/user/login", methods=["POST"])
def login_user():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "invalid credentials"}), 401

    user_id, hashed = row
    if check_password_hash(hashed, password):
        return jsonify({"status": "login ok", "user_id": user_id})
    else:
        return jsonify({"error": "invalid credentials"}), 401



# Group management

@app.route("/group", methods=["POST"])
def create_group():
    data = request.get_json() or {}
    name = data.get("name")
    owner = data.get("owner")  # owner should be user_id

    if not name or not owner:
        return jsonify({"error": "name and owner required"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO groups (name, owner) VALUES (?, ?)", (name, owner))
    group_id = c.lastrowid
    # add owner as group member
    c.execute("INSERT INTO group_users (group_id, user_id) VALUES (?, ?)", (group_id, owner))
    conn.commit()
    conn.close()
    return jsonify({"status": "group created", "group_id": group_id}), 201


@app.route("/groups", methods=["GET"])
def list_groups():
    owner = request.args.get("owner")  # optional filter
    conn = get_db_connection()
    c = conn.cursor()
    if owner:
        c.execute("SELECT id, name, owner FROM groups WHERE owner = ?", (owner,))
    else:
        c.execute("SELECT id, name, owner FROM groups")
    rows = c.fetchall()
    conn.close()
    groups = [{"id": r[0], "name": r[1], "owner": r[2]} for r in rows]
    return jsonify(groups)


@app.route("/group/<int:group_id>/add_user", methods=["POST"])
def add_user_to_group(group_id):
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    # ensure group exists
    c.execute("SELECT id FROM groups WHERE id = ?", (group_id,))
    if not c.fetchone():
        conn.close()
        return jsonify({"error": "group not found"}), 404

    # avoid duplicate membership
    c.execute(
        "SELECT id FROM group_users WHERE group_id = ? AND user_id = ?", (group_id, user_id)
    )
    if c.fetchone():
        conn.close()
        return jsonify({"status": "user already in group"}), 200

    c.execute("INSERT INTO group_users (group_id, user_id) VALUES (?, ?)", (group_id, user_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "user added to group"}), 201


@app.route("/group/<int:group_id>/members", methods=["GET"])
def group_members(group_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT u.id, u.email FROM users u JOIN group_users gu ON u.id = gu.user_id WHERE gu.group_id = ?",
        (group_id,),
    )
    rows = c.fetchall()
    conn.close()
    members = [{"id": r[0], "email": r[1]} for r in rows]
    return jsonify(members)



# Expense management (CRUD)

@app.route("/expense", methods=["POST"])
def create_expense():
    data = request.get_json() or {}
    required = ["group_id", "payer", "amount"]
    if not all(k in data for k in required):
        return jsonify({"error": "missing fields"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO expenses (group_id, payer, amount, description) VALUES (?, ?, ?, ?)",
        (data["group_id"], data["payer"], float(data["amount"]), data.get("description", "")),
    )
    expense_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"status": "created", "expense_id": expense_id}), 201


@app.route("/expenses", methods=["GET"])
def list_expenses():
    group_id = request.args.get("group_id")
    conn = get_db_connection()
    c = conn.cursor()
    if group_id:
        c.execute(
            "SELECT id, group_id, payer, amount, description FROM expenses WHERE group_id = ?",
            (group_id,),
        )
    else:
        c.execute("SELECT id, group_id, payer, amount, description FROM expenses")
    rows = c.fetchall()
    conn.close()
    expenses = [
        {"id": r[0], "group_id": r[1], "payer": r[2], "amount": r[3], "description": r[4]}
        for r in rows
    ]
    return jsonify(expenses)


@app.route("/expense/<int:expense_id>", methods=["GET"])
def get_expense(expense_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, group_id, payer, amount, description FROM expenses WHERE id = ?", (expense_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "expense not found"}), 404
    expense = {"id": row[0], "group_id": row[1], "payer": row[2], "amount": row[3], "description": row[4]}
    return jsonify(expense)


@app.route("/expense/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
    data = request.get_json() or {}
    fields = {}
    for key in ("group_id", "payer", "amount", "description"):
        if key in data:
            fields[key] = data[key]

    if not fields:
        return jsonify({"error": "no fields to update"}), 400

    set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
    values = [float(v) if k == "amount" else v for k, v in fields.items()]
    values.append(expense_id)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"UPDATE expenses SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})


@app.route("/expense/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})



# Settlement endpoint (non-CRUD)

@app.route("/settle/<int:group_id>", methods=["GET"])
def settle(group_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT payer, amount FROM expenses WHERE group_id = ?", (group_id,))
    rows = c.fetchall()
    conn.close()
    result = calculate_settlement(rows)
    return jsonify(result)


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
