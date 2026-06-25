from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'veguchukka_local_dev_only_key')

# ── CORS for GitHub Pages reporter portal ──────────────────────────────────
@app.after_request
def add_cors_headers(response):
    # Only add CORS to /api/* routes
    if request.path.startswith('/api/'):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response


# # MySQL Configuration (XAMPP defaults)
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''  # XAMPP default is empty
# app.config['MYSQL_DB'] = 'veguchukka'
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# MySQL Configuration
# Reads from environment variables when set (Render + TiDB Cloud in production).
# Falls back to XAMPP defaults so this still runs unchanged on your local machine.
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'veguchukka')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', 3306))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
if os.environ.get('MYSQL_USE_SSL') == '1':
    app.config['MYSQL_SSL'] = True
    app.config['MYSQL_SSL_VERIFY_CERT'] = True
    app.config['MYSQL_SSL_CA'] = os.environ.get('MYSQL_SSL_CA', '/etc/ssl/certs/ca-certificates.crt')

# File upload config
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

mysql = MySQL(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('దయచేసి లాగిన్ అవండి.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') not in roles:
                flash('మీకు ఈ పేజీని యాక్సెస్ చేసే అనుమతి లేదు.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# ─── PUBLIC ROUTES ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    # Breaking news
    cur.execute("SELECT * FROM articles WHERE status='approved' ORDER BY published_at DESC LIMIT 1")
    breaking = cur.fetchone()
    # Top stories
    cur.execute("SELECT a.*, u.username as reporter_name FROM articles a JOIN users u ON a.reporter_id=u.id WHERE a.status='approved' ORDER BY a.published_at DESC LIMIT 6")
    top_stories = cur.fetchall()
    # By category
    categories = ['రాజకీయాలు', 'క్రీడలు', 'వ్యాపారం', 'వినోదం', 'అంతర్జాతీయం', 'సాంకేతికత']
    cat_news = {}
    for cat in categories:
        cur.execute("SELECT * FROM articles WHERE status='approved' AND category=%s ORDER BY published_at DESC LIMIT 4", (cat,))
        cat_news[cat] = cur.fetchall()
    cur.close()
    return render_template('index.html', breaking=breaking, top_stories=top_stories, cat_news=cat_news, categories=categories)

@app.route('/article/<int:article_id>')
def article(article_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT a.*, u.username as reporter_name FROM articles a JOIN users u ON a.reporter_id=u.id WHERE a.id=%s AND a.status='approved'", (article_id,))
    article = cur.fetchone()
    if not article:
        flash('వార్త కనుగొనబడలేదు.', 'danger')
        return redirect(url_for('index'))
    cur.execute("UPDATE articles SET views=views+1 WHERE id=%s", (article_id,))
    mysql.connection.commit()
    cur.execute("SELECT * FROM articles WHERE status='approved' AND category=%s AND id!=%s ORDER BY published_at DESC LIMIT 5", (article['category'], article_id))
    related = cur.fetchall()
    cur.close()
    return render_template('article.html', article=article, related=related)

@app.route('/category/<cat_name>')
def category(cat_name):
    cur = mysql.connection.cursor()
    cur.execute("SELECT a.*, u.username as reporter_name FROM articles a JOIN users u ON a.reporter_id=u.id WHERE a.status='approved' AND a.category=%s ORDER BY a.published_at DESC", (cat_name,))
    articles = cur.fetchall()
    cur.close()
    return render_template('category.html', articles=articles, category=cat_name)

# ─── AUTH ROUTES ─────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f'స్వాగతం, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('తప్పుడు వినియోగదారు పేరు లేదా పాస్‌వర్డ్.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('విజయవంతంగా లాగ్అవుట్ అయ్యారు.', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form.get('role', 'user')
        if role == 'editor':
            flash('సంపాదకుడు అకౌంట్ నేరుగా సృష్టించడం అనుమతించబడదు.', 'danger')
            return redirect(url_for('register'))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s,%s,%s,%s)", (username, email, password, role))
        mysql.connection.commit()
        cur.close()
        flash('నమోదు విజయవంతమైంది! దయచేసి లాగిన్ అవండి.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    role = session['role']
    if role == 'editor':
        return redirect(url_for('editor_dashboard'))
    elif role == 'reporter':
        return redirect(url_for('reporter_dashboard'))
    else:
        return redirect(url_for('index'))

# ─── REPORTER ROUTES ─────────────────────────────────────────────────────────

@app.route('/reporter')
@login_required
@role_required('reporter')
def reporter_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM articles WHERE reporter_id=%s ORDER BY created_at DESC", (session['user_id'],))
    articles = cur.fetchall()
    cur.close()
    stats = {'pending': sum(1 for a in articles if a['status']=='pending'),
             'approved': sum(1 for a in articles if a['status']=='approved'),
             'rejected': sum(1 for a in articles if a['status']=='rejected')}
    return render_template('reporter_dashboard.html', articles=articles, stats=stats)

@app.route('/reporter/submit', methods=['GET', 'POST'])
@login_required
@role_required('reporter')
def submit_article():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        summary = request.form['summary']
        image_url = ''
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = f'/uploads/{filename}'
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles (title,content,summary,category,image_url,reporter_id,status) VALUES (%s,%s,%s,%s,%s,%s,'pending')",
                    (title, content, summary, category, image_url, session['user_id']))
        mysql.connection.commit()
        cur.close()
        flash('వార్త విజయవంతంగా సమర్పించబడింది! సంపాదకుని ఆమోదం కోసం వేచి ఉంది.', 'success')
        return redirect(url_for('reporter_dashboard'))
    return render_template('submit_article.html')

# ─── EDITOR ROUTES ───────────────────────────────────────────────────────────

@app.route('/editor')
@login_required
@role_required('editor')
def editor_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT a.*, u.username as reporter_name FROM articles a JOIN users u ON a.reporter_id=u.id ORDER BY a.created_at DESC")
    all_articles = cur.fetchall()
    pending = [a for a in all_articles if a['status'] == 'pending']
    approved = [a for a in all_articles if a['status'] == 'approved']
    rejected = [a for a in all_articles if a['status'] == 'rejected']
    cur.close()
    return render_template('editor_dashboard.html', pending=pending, approved=approved, rejected=rejected)

@app.route('/editor/review/<int:article_id>', methods=['GET', 'POST'])
@login_required
@role_required('editor')
def review_article(article_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        action = request.form['action']
        editor_note = request.form.get('editor_note', '')
        edited_title = request.form.get('title', '')
        edited_content = request.form.get('content', '')
        edited_summary = request.form.get('summary', '')
        if action == 'approve':
            cur.execute("""UPDATE articles SET status='approved', editor_note=%s, 
                           title=%s, content=%s, summary=%s, published_at=NOW() WHERE id=%s""",
                        (editor_note, edited_title, edited_content, edited_summary, article_id))
            flash('వార్త ఆమోదించబడింది మరియు ప్రచురించబడింది!', 'success')
        elif action == 'reject':
            cur.execute("UPDATE articles SET status='rejected', editor_note=%s WHERE id=%s", (editor_note, article_id))
            flash('వార్త తిరస్కరించబడింది.', 'warning')
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('editor_dashboard'))
    cur.execute("SELECT a.*, u.username as reporter_name, u.email as reporter_email FROM articles a JOIN users u ON a.reporter_id=u.id WHERE a.id=%s", (article_id,))
    article = cur.fetchone()
    cur.close()
    return render_template('review_article.html', article=article)

@app.route('/editor/delete/<int:article_id>', methods=['POST'])
@login_required
@role_required('editor')
def delete_article(article_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM articles WHERE id=%s", (article_id,))
    mysql.connection.commit()
    cur.close()
    flash('వార్త తొలగించబడింది.', 'success')
    return redirect(url_for('editor_dashboard'))

# ─── API for external reporter link ──────────────────────────────────────────

@app.route('/api/submit', methods=['POST', 'OPTIONS'])
def api_submit():
    """External reporter submission — supports base64 image upload"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        resp = app.make_default_options_response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return resp

    data = request.json
    if not data:
        return jsonify({'error': 'No data'}), 400

    cur = mysql.connection.cursor()
    reporter_name = (data.get('reporter_name') or '').strip()
    if not reporter_name:
        cur.close()
        return jsonify({'error': 'Reporter name is required'}), 400

    cur.execute("SELECT * FROM users WHERE username=%s AND role='reporter'", (reporter_name,))
    reporter = cur.fetchone()
    if not reporter:
        cur.close()
        return jsonify({'error': 'Reporter not found. Use your exact registered username.'}), 401

    # Handle base64 image (from standalone reporter editor)
    image_url = data.get('image_url', '')
    image_data = data.get('image_data', '')
    if image_data and image_data.startswith('data:image'):
        try:
            import base64, re as _re
            # Strip the data:image/xxx;base64, prefix
            match = _re.match(r'data:image/(\w+);base64,(.+)', image_data)
            if match:
                ext = match.group(1)
                raw = base64.b64decode(match.group(2))
                fname = secure_filename(f"post_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{ext}")
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                with open(os.path.join(app.config['UPLOAD_FOLDER'], fname), 'wb') as imgf:
                    imgf.write(raw)
                image_url = f'/uploads/{fname}'
        except Exception as e:
            print(f"Image save error: {e}")
            image_url = ''

    cur.execute(
        "INSERT INTO articles (title,content,summary,category,image_url,reporter_id,status) VALUES (%s,%s,%s,%s,%s,%s,'pending')",
        (data.get('title'), data.get('content'), data.get('summary', ''),
         data.get('category', 'సాధారణం'), image_url, reporter['id'])
    )
    mysql.connection.commit()
    cur.close()

    resp = jsonify({'success': True, 'message': 'Article submitted for review'})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/reporter/quick-post', methods=['POST'])
@login_required
@role_required('reporter')
def quick_post():
    """Direct post from reporter dashboard (session-authenticated, multipart form)"""
    title    = request.form.get('title', '').strip()
    content  = request.form.get('content', '').strip()
    category = request.form.get('category', 'సాధారణం')
    summary  = request.form.get('summary', '').strip()

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    image_url = ''
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f'/uploads/{filename}'

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO articles (title,content,summary,category,image_url,reporter_id,status) VALUES (%s,%s,%s,%s,%s,%s,'pending')",
        (title, content, summary, category, image_url, session['user_id'])
    )
    mysql.connection.commit()
    cur.close()
    return jsonify({'success': True, 'message': 'Article submitted for review'})


@login_required
@role_required('reporter')
def get_token():
    import secrets
    token = secrets.token_hex(16)
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET api_token=%s WHERE id=%s", (token, session['user_id']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'token': token, 'submit_url': request.host_url + 'api/submit'})

from flask import send_from_directory
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
