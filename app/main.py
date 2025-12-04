from flask import Flask, request, jsonify
from non_crud_lib.settlement import calculate_settlement
import sqlite3, os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'expense.db')

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT)''')
        c.execute('''CREATE TABLE groups (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, owner INTEGER)''')
        c.execute('''CREATE TABLE expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, group_id INTEGER, payer INTEGER, amount REAL, description TEXT)''')
        conn.commit()
        conn.close()

@app.route('/')
def index():
    return jsonify({"status": "running"})

@app.route('/expense', methods=['POST'])
def create_expense():
    data = request.get_json() or {}
    required = ['group_id','payer','amount']
    if not all(k in data for k in required):
        return jsonify({"error":"missing fields"}), 400
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO expenses (group_id,payer,amount,description) VALUES (?,?,?,?)',
              (data['group_id'], data['payer'], float(data['amount']), data.get('description','')))
    conn.commit()
    conn.close()
    return jsonify({"status": "created"}), 201

@app.route('/settle/<int:group_id>', methods=['GET'])
def settle(group_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT payer, amount FROM expenses WHERE group_id=?', (group_id,))
    rows = c.fetchall()
    conn.close()
    result = calculate_settlement(rows)
    return jsonify(result)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
