from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, Response, send_file
import pandas as pd
import os
import sqlite3
import json
import uuid
from datetime import datetime
from io import BytesIO
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'nextis_secret_key_change_in_production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PORTFOLIO_FOLDER'] = os.path.join('static', 'portfolio_uploads')
app.config['DB_NAME'] = 'nexsis.db'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PORTFOLIO_FOLDER'], exist_ok=True)

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
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS project_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            message TEXT,
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
        if secret_code == 'Nx$!2026#Admin@Secure*Key':  # Complex admin code
            role = 'admin'
            
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        
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

@app.route('/api/projects', methods=['GET', 'POST'])
def handle_projects():
    conn = get_db_connection()
    if request.method == 'POST':
        if 'role' not in session or session['role'] != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
            
        title = request.form.get('title')
        description = request.form.get('description')
        image_files = request.files.getlist('image')
        
        if not title or not description or not image_files:
            return jsonify({'error': 'Missing data'}), 400
            
        # Create project
        cursor = conn.execute('INSERT INTO projects (title, description, image_url) VALUES (?, ?, ?)',
                     (title, description, ""))
        project_id = cursor.lastrowid
        
        first_image_url = ""
        for i, image_file in enumerate(image_files):
            if not image_file: continue
            filename = secure_filename(f"{uuid.uuid4()}_{image_file.filename}")
            image_path = os.path.join(app.config['PORTFOLIO_FOLDER'], filename)
            image_file.save(image_path)
            
            # relative path for web access
            image_url = f"/static/portfolio_uploads/{filename}"
            if i == 0: first_image_url = image_url
            
            conn.execute('INSERT INTO project_images (project_id, image_url) VALUES (?, ?)',
                         (project_id, image_url))
        
        # Update project with cover image
        conn.execute('UPDATE projects SET image_url = ? WHERE id = ?', (first_image_url, project_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    projects_rows = conn.execute('SELECT * FROM projects ORDER BY id DESC').fetchall()
    projects = []
    for p in projects_rows:
        project = dict(p)
        images = conn.execute('SELECT * FROM project_images WHERE project_id = ?', (project['id'],)).fetchall()
        project['images'] = [dict(img) for img in images]
        projects.append(project)
        
    conn.close()
    return jsonify(projects)

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    images = conn.execute('SELECT image_url FROM project_images WHERE project_id = ?', (project_id,)).fetchall()
    
    for img in images:
        try:
            filename = img['image_url'].split('/')[-1]
            os.remove(os.path.join(app.config['PORTFOLIO_FOLDER'], filename))
        except:
            pass
            
    conn.execute('DELETE FROM project_images WHERE project_id = ?', (project_id,))
    conn.execute('DELETE FROM projects WHERE id = ?', (project_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/projects/<int:project_id>', methods=['POST'])
def update_project(project_id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    title = request.form.get('title')
    description = request.form.get('description')
    image_files = request.files.getlist('image')
    
    conn = get_db_connection()
    
    if title and description:
        conn.execute('UPDATE projects SET title = ?, description = ? WHERE id = ?', (title, description, project_id))
    
    if image_files:
        for image_file in image_files:
            if not image_file or image_file.filename == '': continue
            filename = secure_filename(f"{uuid.uuid4()}_{image_file.filename}")
            image_path = os.path.join(app.config['PORTFOLIO_FOLDER'], filename)
            image_file.save(image_path)
            
            image_url = f"/static/portfolio_uploads/{filename}"
            conn.execute('INSERT INTO project_images (project_id, image_url) VALUES (?, ?)', (project_id, image_url))
            
            # If the project had no cover image, set this one as cover
            project = conn.execute('SELECT image_url FROM projects WHERE id = ?', (project_id,)).fetchone()
            if not project['image_url']:
                conn.execute('UPDATE projects SET image_url = ? WHERE id = ?', (image_url, project_id))

    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/portfolio/images/<int:image_id>', methods=['DELETE'])
def delete_portfolio_image(image_id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    img = conn.execute('SELECT * FROM project_images WHERE id = ?', (image_id,)).fetchone()
    if img:
        try:
            filename = img['image_url'].split('/')[-1]
            os.remove(os.path.join(app.config['PORTFOLIO_FOLDER'], filename))
        except:
            pass
        
        project_id = img['project_id']
        conn.execute('DELETE FROM project_images WHERE id = ?', (image_id,))
        
        # Update project cover if this was the cover
        project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
        if project and project['image_url'] == img['image_url']:
            next_img = conn.execute('SELECT image_url FROM project_images WHERE project_id = ? LIMIT 1', (project_id,)).fetchone()
            new_cover = next_img['image_url'] if next_img else ""
            conn.execute('UPDATE projects SET image_url = ? WHERE id = ?', (new_cover, project_id))
            
        conn.commit()
    conn.close()
    return jsonify({'success': True})

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

@app.route('/api/files/list')
def list_uploaded_files():
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        files = []
        upload_folder = app.config['UPLOAD_FOLDER']
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                filepath = os.path.join(upload_folder, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        'name': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                    })
        
        files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/delete', methods=['POST'])
def delete_uploaded_file():
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    filename = data.get('filename')
    
    try:
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid filename'}), 400

        upload_folder = app.config['UPLOAD_FOLDER']
        filepath = os.path.join(upload_folder, filename)
        abs_filepath = os.path.abspath(filepath)
        abs_upload_folder = os.path.abspath(upload_folder)
        
        # Security Check
        if not abs_filepath.startswith(abs_upload_folder):
            return jsonify({'error': 'Invalid file path security check'}), 400
        
        # 1. Delete associated data from DB
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM clients WHERE source_file = ?", (filename,))
            conn.commit()
        except Exception as db_e:
            print(f"Error deleting from DB: {db_e}")
            # Continue to delete file even if DB fail (or maybe not? prioritize cleanup)
        finally:
            conn.close()

        # 2. Delete file from disk
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'success': True, 'message': f'File and data deleted'})
        else:
            return jsonify({'error': 'File not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/clients/update/<int:client_id>', methods=['POST'])
def update_client(client_id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    business_name = data.get('business_name')
    location = normalize_city(data.get('location', ''))
    phone = data.get('phone', 'אין')
    anydesk = data.get('anydesk', 'אין')
    
    # Update the core fields
    conn = get_db_connection()
    try:
        # Also update extra_data JSON to keep it in sync if needed
        # We'll merge with existing extra_data
        client = conn.execute('SELECT extra_data FROM clients WHERE id = ?', (client_id,)).fetchone()
        extra = {}
        if client and client['extra_data']:
            try:
                extra = json.loads(client['extra_data'])
            except:
                pass
        
        # Update extra dict with new values
        extra.update(data)
        extra_json = json.dumps(extra, ensure_ascii=False)
        
        conn.execute('''
            UPDATE clients 
            SET business_name = ?, location = ?, phone = ?, anydesk = ?, extra_data = ?
            WHERE id = ?
        ''', (business_name, location, phone, anydesk, extra_json, client_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/clients/delete/<int:client_id>', methods=['POST', 'DELETE'])
def delete_client(client_id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    try:
        # Check if client exists
        client = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Delete the client
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Client deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/clients/details/<int:client_id>')
def get_client_details(client_id):
    conn = get_db_connection()
    try:
        # Fetch the clicked client first to identify the business
        targ_client = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if not targ_client:
            return jsonify({'error': 'Client not found'}), 404
        
        business_name = targ_client['business_name']
        
        # Now fetch ALL records for this business name to aggregate data
        # Using case-insensitive match just in case
        all_records = conn.execute("SELECT * FROM clients WHERE business_name = ? COLLATE NOCASE", (business_name,)).fetchall()
        
        merged_data = {}
        source_files = set()
        
        # Iterate over all related records and merge data
        for record in all_records:
            # 1. Start with core fields from this record (in case extra_data is partial)
            # 2. Parse extra_data
            row_data = {}
            if record['extra_data']:
                try:
                    row_data = json.loads(record['extra_data'])
                except:
                    pass
            
            # 3. Always merge core fields from the record as fallback/primary if not in extra_data
            for field in ['location', 'phone', 'anydesk', 'business_name']:
                 val = record[field]
                 if val and val != 'אין' and field not in row_data:
                      row_data[field] = val

            # 4. Merge into main dict
            merged_data.update(row_data)
            
            # 5. Collect source file
            if record['source_file']:
                source_files.add(record['source_file'])
        
        # Ensure business_name is consistently set
        merged_data['business_name'] = business_name
        
        # Consolidate source files
        if source_files:
            merged_data['source_file'] = ', '.join(sorted(list(source_files)))
        
        # Use Pandas for display formatting
        df = pd.DataFrame([merged_data])
        
        # Transpose
        df_transposed = df.transpose().reset_index()
        df_transposed.columns = ['Field', 'Value']
        
        df_transposed = df_transposed.fillna('')
        
        result = df_transposed.to_dict('records')
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in details: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


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
        rows = conn.execute("SELECT * FROM clients WHERE location = ?", (location,)).fetchall()
        clients = []
        for row in rows:
            client = {}
            # Start with base fields
            for key in row.keys():
                if key not in ['extra_data', 'created_at']:
                    client[key] = row[key]
            
            # Merge ALL extra_data fields
            if row['extra_data']:
                try:
                    extra = json.loads(row['extra_data'])
                    if isinstance(extra, dict):
                        for key, value in extra.items():
                            if key not in ['id', 'created_at', 'extra_data']:
                                client[key] = value
                except Exception as e:
                    print(f"Error parsing extra_data: {e}")
            
            clients.append(client)
    
    conn.close()
    
    return jsonify(clients)

@app.route('/api/clients/all')
def get_all_clients():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('limit', 100))
    offset = (page - 1) * per_page
    
    # Check if admin wants to see all columns (expanded view)
    expanded_view = request.args.get('expanded', 'false').lower() == 'true'
    
    conn = get_db_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        rows = conn.execute("SELECT * FROM clients ORDER BY id DESC LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
        
        results = []
        all_fields = set()  # To collect all unique field names
        
        for row in rows:
            client = {
                'id': row['id'],
                'business_name': row['business_name'],
                'location': row['location'],
                'phone': row['phone'],
                'anydesk': row['anydesk'],
                'source_file': row['source_file'],
                'created_at': row['created_at']
            }
            
            # Parse extra_data which contains ALL Excel columns
            if row['extra_data']:
                try:
                    extra = json.loads(row['extra_data'])
                    if isinstance(extra, dict):
                        if expanded_view:
                            # In expanded view, add ALL fields as top-level properties
                            for key, value in extra.items():
                                client[key] = value
                                all_fields.add(key)
                        else:
                            # In compact view, keep extra_data as separate object
                            client['extra_data'] = extra
                except Exception as e:
                    print(f"Error parsing extra_data for client {row['id']}: {e}")
                    client['extra_data'] = {}
            
            results.append(client)
            
        response = {
            'total': total,
            'page': page,
            'per_page': per_page,
            'data': results
        }
        
        # If expanded view, also return all unique fields for table headers
        if expanded_view:
            response['all_fields'] = sorted(list(all_fields))
            
        return jsonify(response)
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

@app.route('/api/clients/full/<int:client_id>')
def get_client_full_details(client_id):
    """Get complete client data with ALL Excel columns"""
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    try:
        client = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if not client:
            return jsonify({'error': 'Client not found'}), 404
            
        result = {
            'id': client['id'],
            'business_name': client['business_name'],
            'location': client['location'],
            'phone': client['phone'],
            'anydesk': client['anydesk'],
            'source_file': client['source_file'],
            'created_at': client['created_at']
        }
        
        # Parse and add ALL extra_data fields
        if client['extra_data']:
            try:
                extra = json.loads(client['extra_data'])
                if isinstance(extra, dict):
                    for key, value in extra.items():
                        result[key] = value
            except:
                result['extra_data'] = client['extra_data']
        
        # Format as array for easy display
        formatted_data = []
        for key, value in result.items():
            if key not in ['id', 'created_at']:  # Skip internal fields
                formatted_data.append({
                    'field': key,
                    'value': value if value else 'אין'
                })
        
        return jsonify(formatted_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/clients/fields')
def get_all_fields():
    """Get all unique field names from all clients' extra_data"""
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    try:
        clients = conn.execute("SELECT extra_data FROM clients WHERE extra_data IS NOT NULL AND extra_data != ''").fetchall()
        
        all_fields = set(['business_name', 'location', 'phone', 'anydesk', 'source_file'])
        
        for client in clients:
            try:
                extra = json.loads(client['extra_data'])
                if isinstance(extra, dict):
                    all_fields.update(extra.keys())
            except:
                continue
        
        return jsonify({
            'fields': sorted(list(all_fields)),
            'count': len(all_fields)
        })
    finally:
        conn.close()

@app.route('/admin/full')
def admin_full_view():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_full_view.html', username=session['username'])

@app.route('/api/clients/export')
def export_clients():
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    export_format = request.args.get('format', 'excel')
    selected_columns = request.args.get('columns', '').split(',')
    location_filter = request.args.get('location', '')
    
    conn = get_db_connection()
    
    # Build query
    query = "SELECT * FROM clients"
    params = []
    if location_filter:
        query += " WHERE location = ?"
        params.append(location_filter)
    query += " ORDER BY id DESC"
    
    rows = conn.execute(query, params).fetchall()
    
    # Prepare data
    data = []
    for row in rows:
        client = {}
        # Always include base columns
        client['id'] = row['id']
        client['business_name'] = row['business_name']
        client['location'] = row['location']
        client['phone'] = row['phone']
        client['anydesk'] = row['anydesk']
        client['source_file'] = row['source_file']
        client['created_at'] = row['created_at']
        
        # Add extra_data fields
        if row['extra_data']:
            try:
                extra = json.loads(row['extra_data'])
                if isinstance(extra, dict):
                    for key, value in extra.items():
                        client[key] = value
            except:
                pass
        
        data.append(client)
    
    conn.close()
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Filter columns if specified
    if selected_columns and selected_columns[0]:
        available_columns = [col for col in selected_columns if col in df.columns]
        df = df[available_columns]
    
    # Export based on format
    if export_format == 'csv':
        csv_data = df.to_csv(index=False, encoding='utf-8-sig')
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=clients_export.csv"}
        )
    else:
        # Excel export
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Clients')
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='clients_export.xlsx'
        )
@app.route('/api/contact', methods=['GET', 'POST'])
def handle_contact():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.json
        conn.execute('INSERT INTO contact_messages (name, phone, message) VALUES (?, ?, ?)',
                     (data.get('name'), data.get('phone'), data.get('message')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    # GET - Admin only
    if 'role' not in session or session['role'] != 'admin':
         conn.close()
         return jsonify({'error': 'Unauthorized'}), 403

    messages = conn.execute('SELECT * FROM contact_messages ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(m) for m in messages])

@app.route('/api/contact/<int:message_id>', methods=['DELETE'])
def delete_contact_message(message_id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM contact_messages WHERE id = ?', (message_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
