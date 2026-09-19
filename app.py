from flask import Flask, request, jsonify, Response, redirect, session
from flask_cors import CORS
import sqlite3
import webview
import threading
import csv
import io
import phonenumbers
import traceback
from phonenumbers import NumberParseException

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'crm-dashboard-secret-key'
CORS(app)

DB_FILE = 'crm_database.db'
window = None

VALID_USERS = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'user': {'password': 'user123', 'role': 'user'},
}


def require_admin():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    return None


def get_valid_users():
    users = dict(VALID_USERS)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, role FROM app_users")
    for row in cursor.fetchall():
        users[row['username']] = {'password': row['password'], 'role': row['role']}
    conn.close()
    return users


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            company TEXT,
            status TEXT DEFAULT 'New',
            value REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # ensure required columns exist for older DBs
    try:
        cursor.execute("PRAGMA table_info(leads)")
        existing = [r[1] for r in cursor.fetchall()]
        if 'value' not in existing:
            cursor.execute("ALTER TABLE leads ADD COLUMN value REAL DEFAULT 0")
        if 'notes' not in existing:
            cursor.execute("ALTER TABLE leads ADD COLUMN notes TEXT")
        conn.commit()
    except Exception:
        tb = traceback.format_exc()
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write('\n--- init_db migration exception ---\n')
            f.write(tb)

    cursor.execute("SELECT COUNT(*) FROM leads")
    if cursor.fetchone()[0] == 0:
        sample_leads = [
            ('Alex Rivera', 'alex@techcorp.com', '+1 555-0192', 'TechCorp', 'New', 12000.0, 'Interested in enterprise tier'),
            ('Sarah Chen', 'sarah@innovate.io', '+1 555-0143', 'Innovate', 'Contacted', 8500.0, 'Demo scheduled for Friday'),
            ('Marcus Vance', 'marcus@apex.com', '+1 555-0188', 'Apex Systems', 'Qualified', 25000.0, 'Contract sent for review'),
            ('Elena Rostova', 'elena@cyber.net', '+1 555-0105', 'CyberNet', 'Closed', 18000.0, 'Deal closed successfully')
        ]
        cursor.executemany(
            "INSERT INTO leads (name, email, phone, company, status, value, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            sample_leads
        )

    cursor.execute("SELECT COUNT(*) FROM app_users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO app_users (username, password, role) VALUES (?, ?, ?)",
            [
                ('admin', 'admin123', 'admin'),
                ('user', 'user123', 'user'),
            ]
        )

    conn.commit()
    conn.close()


init_db()


def format_phone_e164(phone):
    phone = (phone or '').strip()
    if not phone:
        return ''
    try:
        if phone.startswith('+'):
            pn = phonenumbers.parse(phone, None)
        else:
            pn = phonenumbers.parse(phone, 'IN')
        if phonenumbers.is_valid_number(pn):
            return phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
        else:
            return None
    except NumberParseException:
        return None

@app.before_request
def require_auth():
    public_paths = {'/login', '/api/login', '/api/logout', '/api/me'}
    if request.path.startswith('/static/'):
        return None
    if request.path in public_paths:
        return None
    if not session.get('logged_in'):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Authentication required'}), 401
        return redirect('/login')

@app.route('/login')
def login_page():
    if session.get('logged_in'):
        return redirect('/')
    return app.send_static_file('login.html')

@app.route('/api/login', methods=['POST'])
def login_user():
    payload = request.get_json(silent=True) or {}
    username = (payload.get('username') or '').strip().lower()
    password = payload.get('password') or ''
    role = (payload.get('role') or '').strip().lower()

    user = get_valid_users().get(username)
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401
    if user['role'] != role:
        return jsonify({'error': 'Selected role does not match this account'}), 401
    if user['password'] != password:
        return jsonify({'error': 'Invalid username or password'}), 401

    session.clear()
    session['logged_in'] = True
    session['username'] = username
    session['role'] = user['role']
    return jsonify({'message': 'Login successful', 'username': username, 'role': user['role']})

@app.route('/api/logout', methods=['POST'])
def logout_user():
    session.clear()
    return jsonify({'message': 'Logged out'})

@app.route('/api/me')
def get_current_user():
    if not session.get('logged_in'):
        return jsonify({'authenticated': False}), 401
    return jsonify({
        'authenticated': True,
        'username': session.get('username'),
        'role': session.get('role')
    })

# --- WINDOW CONTROLS ---
@app.route('/api/window/minimize', methods=['POST'])
def minimize_window():
    if window:
        window.minimize()
    return jsonify({'status': 'minimized'})

@app.route('/api/window/close', methods=['POST'])
def close_window():
    if window:
        window.destroy()
    return jsonify({'status': 'closed'})

# --- CRM API ENDPOINTS ---
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect('/login')
    return app.send_static_file('index.html')

@app.route('/api/users', methods=['GET'])
def get_users():
    admin_error = require_admin()
    if admin_error:
        return admin_error

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, created_at FROM app_users ORDER BY id ASC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(users)


@app.route('/api/users', methods=['POST'])
def create_user():
    admin_error = require_admin()
    if admin_error:
        return admin_error

    payload = request.json or {}
    username = (payload.get('username') or '').strip().lower()
    password = payload.get('password') or ''
    role = (payload.get('role') or 'user').strip().lower()

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    if role not in {'admin', 'user'}:
        return jsonify({'error': 'Role must be admin or user'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO app_users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': user_id, 'username': username, 'role': role, 'message': 'User created'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'A user with this username already exists'}), 400


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    admin_error = require_admin()
    if admin_error:
        return admin_error

    payload = request.json or {}
    username = (payload.get('username') or '').strip().lower()
    password = payload.get('password')
    role = (payload.get('role') or '').strip().lower()

    if not username:
        return jsonify({'error': 'Username is required'}), 400
    if role and role not in {'admin', 'user'}:
        return jsonify({'error': 'Role must be admin or user'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        existing = cursor.execute("SELECT username, role, password FROM app_users WHERE id = ?", (user_id,)).fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        new_username = username
        new_role = role or existing['role']
        new_password = password if password not in (None, '') else existing['password']

        cursor.execute(
            "UPDATE app_users SET username = ?, password = ?, role = ? WHERE id = ?",
            (new_username, new_password, new_role, user_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'id': user_id, 'username': new_username, 'role': new_role, 'message': 'User updated'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'A user with this username already exists'}), 400


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    admin_error = require_admin()
    if admin_error:
        return admin_error

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM app_users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User deleted'})


@app.route('/api/leads', methods=['GET'])
def get_leads():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY id DESC")
    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(leads)
@app.route('/api/leads', methods=['POST'])
def create_lead():
    admin_error = require_admin()
    if admin_error:
        return admin_error

    payload = request.json or {}
    try:
        if not payload.get('name') or not payload.get('email'):
            return jsonify({'error': 'Name and Email are required'}), 400

        # validate/format phone to E.164
        phone_raw = payload.get('phone', '')
        formatted_phone = format_phone_e164(phone_raw)
        if formatted_phone is None:
            return jsonify({'error': 'Invalid phone number'}), 400

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO leads (name, email, phone, company, status, value, notes) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    payload['name'],
                    payload['email'],
                    formatted_phone,
                    payload.get('company', ''),
                    payload.get('status', 'New'),
                    float(payload.get('value', 0) or 0),
                    payload.get('notes', '')
                )
            )
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            return jsonify({'id': new_id, 'message': 'Lead created'}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'A lead with this email already exists'}), 400
    except Exception:
        tb = traceback.format_exc()
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write('\n--- create_lead exception ---\n')
            f.write(tb)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/leads/<int:lead_id>', methods=['PUT'])
def update_lead(lead_id):
    admin_error = require_admin()
    if admin_error:
        return admin_error

    payload = request.json or {}
    try:
        # validate/format phone to E.164
        phone_raw = payload.get('phone', '')
        formatted_phone = format_phone_e164(phone_raw)
        if formatted_phone is None:
            return jsonify({'error': 'Invalid phone number'}), 400

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """UPDATE leads SET name=?, email=?, phone=?, company=?, status=?, value=?, notes=?
                   WHERE id=?""",
                (
                    payload['name'],
                    payload['email'],
                    formatted_phone,
                    payload.get('company', ''),
                    payload.get('status', 'New'),
                    float(payload.get('value', 0) or 0),
                    payload.get('notes', ''),
                    lead_id
                )
            )
            conn.commit()
            conn.close()
            return jsonify({'message': 'Lead updated'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Email is already used by another lead'}), 400
    except Exception:
        tb = traceback.format_exc()
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write('\n--- update_lead exception ---\n')
            f.write(tb)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
def delete_lead(lead_id):
    admin_error = require_admin()
    if admin_error:
        return admin_error

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Lead deleted'})

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    admin_error = require_admin()
    if admin_error:
        return admin_error

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, company, status, value, notes, created_at FROM leads ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Company', 'Status', 'Deal Value (₹)', 'Notes', 'Created At'])
    for r in rows:
        writer.writerow(list(r))

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=crm_leads_export.csv"}
    )

def start_flask():
    app.run(port=5000, debug=True, use_reloader=False)

if __name__ == '__main__':
    init_db()
    t = threading.Thread(target=start_flask)
    t.daemon = True
    t.start()

    window = webview.create_window(
        'CRM Dashboard',
        'http://127.0.0.1:5000?v=1',
        frameless=True,
        width=1200,
        height=800,
        resizable=True
    )
    webview.start()