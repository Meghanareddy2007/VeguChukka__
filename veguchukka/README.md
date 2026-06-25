# వేగుచుక్క దినపత్రిక — Setup Guide

## 📁 Project Structure
```
veguchukka/
├── app.py                   ← Flask application
├── requirements.txt         ← Python dependencies
├── setup_db.sql             ← Database setup
├── templates/
│   ├── base.html            ← Master layout
│   ├── index.html           ← Homepage (like Sakshi)
│   ├── article.html         ← Article detail page
│   ├── category.html        ← Category listing
│   ├── login.html           ← Login page (3 roles)
│   ├── register.html        ← Registration
│   ├── reporter_dashboard.html
│   ├── submit_article.html  ← Rich text editor
│   ├── editor_dashboard.html
│   └── review_article.html  ← Accept/Deny interface
├── static/
│   ├── css/style.css
│   └── js/main.js
└── uploads/                 ← Image uploads folder
```

---

## 🚀 Step-by-Step Setup

### 1. Start XAMPP
- Open XAMPP Control Panel
- Start **Apache** and **MySQL**
- Open **phpMyAdmin** → http://localhost/phpmyadmin

### 2. Create Database
In phpMyAdmin:
- Click **"New"** → Name it `veguchukka` → Click Create
- Click the `veguchukka` database
- Go to **SQL** tab → paste contents of `setup_db.sql` → Click Go

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Flask App
```bash
cd veguchukka
python app.py
```

Visit: **http://localhost:5000**

---

## 👤 Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Editor (సంపాదకుడు) | `editor` | `Editor@123` |
| Reporter (రిపోర్టర్) | `reporter1` | `Reporter@123` |

> ⚠️ Change these passwords after first login!

---

## 🔄 Workflow

### Reporter Flow:
1. Login → Reporter Dashboard
2. Click **"కొత్త వార్త పంపండి"** → Write article
3. OR use external link: https://meghanareddy2007.github.io/Veguchukka/
   - Get API token from dashboard
   - Submit via the GitHub Pages form

### Editor Flow:
1. Login → Editor Dashboard
2. See **pending articles** tab
3. Click **"సమీక్షించండి"** → Edit title/content if needed
4. Click **"ఆమోదించి ప్రచురించండి"** → Goes live instantly
   OR Click **"తిరస్కరించండి"** → Reporter notified

---

## 🌐 External Reporter Portal (GitHub Pages)
The link https://meghanareddy2007.github.io/Veguchukka/ should send a POST request to:
```
POST http://localhost:5000/api/submit
Content-Type: application/json

{
  "token": "REPORTER_API_TOKEN",
  "title": "వార్త శీర్షిక",
  "content": "వార్త వివరాలు...",
  "summary": "సారాంశం",
  "category": "రాజకీయాలు"
}
```

Reporter gets their API token from: Dashboard → "API టోకెన్ పొందండి"

---

## 🗂️ Categories
- రాజకీయాలు (Politics)
- అంతర్జాతీయం (International)  
- క్రీడలు (Sports)
- వ్యాపారం (Business)
- వినోదం (Entertainment)
- సాంకేతికత (Technology)
- ఆరోగ్యం (Health)

---

## ⚙️ Configuration (app.py)
```python
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''      # XAMPP default
app.config['MYSQL_DB'] = 'veguchukka'
```

---

## 🔐 Role Permissions
| Feature | User | Reporter | Editor |
|---------|------|----------|--------|
| Read news | ✅ | ✅ | ✅ |
| Submit articles | ❌ | ✅ | ❌ |
| Approve/Reject | ❌ | ❌ | ✅ |
| Edit articles | ❌ | ❌ | ✅ |
| Delete articles | ❌ | ❌ | ✅ |
