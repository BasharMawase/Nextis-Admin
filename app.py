from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import pandas as pd
import os
import sqlite3
import json
import uuid
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'nextis_secret_key_change_in_production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DB_NAME'] = 'nexsis.db'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(app.config['DB_NAME'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT,
            location TEXT,
            phone TEXT,
            anydesk TEXT,
            source_file TEXT,
            extra_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            rating INTEGER,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

def migrate_schema():
    """Ensure extra_data column exists"""
    conn = get_db_connection()
    try:
        conn.execute("ALTER TABLE clients ADD COLUMN extra_data TEXT")
    except sqlite3.OperationalError:
        pass 
    conn.commit()
    conn.close()

def format_phone_number(phone):
    """Format phone number to Israeli standard"""
    if pd.isna(phone) or phone == 'אין':
        return 'אין'
    
    # Remove non-digits
    digits = ''.join(filter(str.isdigit, str(phone)))
    
    # Handle country code
    if digits.startswith('972'):
        digits = '0' + digits[3:]
    
    # Standard format: 05X-XXXXXXX
    if len(digits) == 10 and digits.startswith('05'):
        return f"{digits[:3]}-{digits[3:]}"
        
    # Landline: 0X-XXXXXXX
    if len(digits) == 9 and digits.startswith('0'):
        return f"{digits[:2]}-{digits[2:]}"
        
    return phone

def migrate_phones():
    """Update all existing phones in DB"""
    conn = get_db_connection()
    try:
        clients = conn.execute("SELECT id, phone FROM clients").fetchall()
        for client in clients:
            old_phone = client['phone']
            new_phone = format_phone_number(old_phone)
            if old_phone != new_phone:
                conn.execute("UPDATE clients SET phone = ? WHERE id = ?", (new_phone, client['id']))
        conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()

# Initialize/Update DB on startup
init_db()
migrate_schema()
migrate_phones()

def normalize_city(city):
    """Normalize city names"""
    city = str(city).strip()
    if 'באקה' in city:
        return 'באקה אל גרבייה'
    return city

def process_excel(file_path):
    """Process uploaded Excel file"""
    try:
        if file_path.endswith('.csv'):
             df = pd.read_csv(file_path)
        else:
             df = pd.read_excel(file_path)
    except Exception as e:
        raise ValueError(f"Could not read file: {e}")

    df.columns = df.columns.str.strip()
    
    # Column mapping with Priority Logic
    rename_map = {}
    used_cols = set()
    
    # Priority configurations: Target -> List of Keywords (High priority first)
    priorities = {
        'location': ['עיר', 'city', 'ישוב', 'יישוב', 'מיקום', 'location', 'כתובת', 'address', 'מקום'],
        'anydesk': ['anydesk', 'אנידסק'],
        'phone': ['phone', 'mobile', 'cell', 'tel', 'טלפון', 'נייד', 'פלאפון'],
        'business_name': ['שם עסק', 'שם העסק', 'עסק', 'business', 'company', 'name', 'שם', 'לקוח', 'client']
    }
    
    for target, keywords in priorities.items():
        found_col = None
        for kw in keywords:
            for col in df.columns:
                col_lower = str(col).lower()
                if col in used_cols: continue
                
                # Check for keyword match
                if kw in col_lower:
                    found_col = col
                    break
            if found_col: break
        
        if found_col:
            rename_map[found_col] = target
            used_cols.add(found_col)

    if rename_map:
        df.rename(columns=rename_map, inplace=True)
    
        # Store all data as JSON before filtering
    df_filled = df.fillna('')
    # Convert all columns to string to avoid serialization issues
    df_filled = df_filled.astype(str)
    df['extra_data'] = df_filled.apply(lambda row: json.dumps(row.to_dict(), ensure_ascii=False), axis=1)

    # Fill missing columns for SQL schema
    for col in ['location', 'anydesk', 'phone', 'business_name']:
        if col not in df.columns:
            df[col] = 'אין'
    
    # Select columns including extra_data
    df = df[['business_name', 'location', 'phone', 'anydesk', 'extra_data']]
    
    # Normalize locations and format phones
    df['location'] = df['location'].apply(normalize_city)
    df['phone'] = df['phone'].apply(format_phone_number)
    
    return df

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('client_home'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        secret_code = request.form.get('secret_code', '')
        
        role = 'client'
        if secret_code == 'Admin123':  # Simple admin code
            role = 'admin'
            
        hashed_pw = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                         (username, hashed_pw, role))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/api/reviews', methods=['GET', 'POST'])
def handle_reviews():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.json
        conn.execute('INSERT INTO reviews (username, rating, comment) VALUES (?, ?, ?)',
                     (data.get('username', 'Anonymous'), data.get('rating'), data.get('comment')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    reviews = conn.execute('SELECT * FROM reviews ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in reviews])

@app.route('/')
def client_home():
    return render_template('client.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    conn = get_db_connection()
    added_count = 0
    
    for file in files:
        if file:
            original_filename = file.filename
            # Use UUID for safe storage
            ext = os.path.splitext(original_filename)[1]
            safe_filename = f"{uuid.uuid4()}{ext}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            file.save(filepath)
            
            try:
                df = process_excel(filepath)
                df['source_file'] = original_filename
                
                # Append to DB
                df.to_sql('clients', conn, if_exists='append', index=False)
                added_count += len(df)
            except Exception as e:
                return jsonify({'error': f'Error in {filename}: {str(e)}'}), 500
    
    conn.close()
    
    return jsonify({
        'success': True,
        'added': added_count,
        'stats': get_stats()
    })

@app.route('/api/clients/add', methods=['POST'])
def add_client():
    data = request.json
    if not data or 'business_name' not in data:
        return jsonify({'error': 'Business Name is required'}), 400
    
    business_name = data.get('business_name')
    location = normalize_city(data.get('location', ''))
    phone = data.get('phone', 'אין')
    anydesk = data.get('anydesk', 'אין')
    
    # Store data as extra_data json as well
    extra = json.dumps(data, ensure_ascii=False)
    
    conn = get_db_connection()
    conn.execute('INSERT INTO clients (business_name, location, phone, anydesk, source_file, extra_data) VALUES (?, ?, ?, ?, ?, ?)',
                 (business_name, location, phone, anydesk, 'Manual Entry', extra))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    conn = get_db_connection()
    # Safe SQL search
    clients = conn.execute("SELECT * FROM clients WHERE business_name LIKE ? LIMIT 20", ('%' + query + '%',)).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in clients])

@app.route('/api/clients')
def get_clients_by_location():
    location = request.args.get('location', '').strip()
    conn = get_db_connection()
    if not location:
        clients = []
    else:
        clients = conn.execute("SELECT * FROM clients WHERE location = ?", (location,)).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in clients])

@app.route('/api/clients/all')
def get_all_clients():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('limit', 50))
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        rows = conn.execute("SELECT * FROM clients ORDER BY id DESC LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
        
        results = []
        for row in rows:
            client = dict(row)
            # Merge extra_data if available
            if client.get('extra_data'):
                try:
                    extra = json.loads(client['extra_data'])
                    if isinstance(extra, dict):
                        client.update(extra)
                except:
                    pass
            results.append(client)
            
        return jsonify({
            'total': total,
            'page': page,
            'per_page': per_page,
            'data': results
        })
    finally:
        conn.close()

def get_stats():
    conn = get_db_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        unique_locs = conn.execute("SELECT COUNT(DISTINCT location) FROM clients").fetchone()[0]
        
        # Top 10 locations
        top_locs = conn.execute("SELECT location, COUNT(*) as count FROM clients GROUP BY location ORDER BY count DESC LIMIT 10").fetchall()
    except:
        return {'total': 0, 'unique_locations': 0, 'top_location': 'N/A', 'locations': []}
    finally:
        conn.close()
    
    locations = [
        {
            'name': row['location'],
            'count': row['count'],
            'percentage': round((row['count'] / total) * 100, 1) if total > 0 else 0
        }
        for row in top_locs
    ]
    
    return {
        'total': total,
        'unique_locations': unique_locs,
        'top_location': locations[0]['name'] if locations else 'N/A',
        'locations': locations
    }

@app.route('/api/analytics')
def analytics():
    return jsonify(get_stats())

if __name__ == '__main__':
    app.run(debug=True, port=5000)
