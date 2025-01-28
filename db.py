# Ce fichier n'est plus utilisé. Vous pouvez le supprimer ou le conserver pour référence.
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

def get_db():
    db = sqlite3.connect('educinfo.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    with db:
        # Création des tables
        db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifiant TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
        ''')
        
        db.execute('''
        CREATE TABLE IF NOT EXISTS absences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professeur TEXT NOT NULL,
            lundi BOOLEAN DEFAULT 0,
            mardi BOOLEAN DEFAULT 0,
            mercredi BOOLEAN DEFAULT 0,
            jeudi BOOLEAN DEFAULT 0,
            vendredi BOOLEAN DEFAULT 0
        )
        ''')
        
        db.execute('''
        CREATE TABLE IF NOT EXISTS widget_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            show_weather BOOLEAN DEFAULT 1,
            show_transport BOOLEAN DEFAULT 0,
            show_menu_cantine BOOLEAN DEFAULT 0,
            menu_cantine TEXT DEFAULT 'Menu non configuré'
        )
        ''')

        db.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date DATE NOT NULL,
            description TEXT DEFAULT ''
        )
        ''')

def create_admin():
    db = get_db()
    with db:
        admin_exists = db.execute('SELECT id FROM users WHERE identifiant = ?', ('admin',)).fetchone()
        if not admin_exists:
            db.execute('''
            INSERT INTO users (identifiant, password, role)
            VALUES (?, ?, ?)
            ''', ('admin', generate_password_hash('admin123'), 'admin'))

def get_user_by_id(user_id):
    db = get_db()
    return db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

def get_user_by_identifiant(identifiant):
    db = get_db()
    return db.execute('SELECT * FROM users WHERE identifiant = ?', (identifiant,)).fetchone()

def update_password(user_id, new_password):
    db = get_db()
    with db:
        db.execute('''
        UPDATE users 
        SET password = ?
        WHERE id = ?
        ''', (generate_password_hash(new_password), user_id))

def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)

# Fonctions pour les absences
def get_absences():
    db = get_db()
    return db.execute('SELECT * FROM absences').fetchall()

def update_absence(professeur, jours):
    db = get_db()
    with db:
        existing = db.execute('SELECT id FROM absences WHERE professeur = ?', (professeur,)).fetchone()
        if existing:
            db.execute('''
            UPDATE absences 
            SET lundi = ?, mardi = ?, mercredi = ?, jeudi = ?, vendredi = ?
            WHERE professeur = ?
            ''', (
                'lundi' in jours,
                'mardi' in jours,
                'mercredi' in jours,
                'jeudi' in jours,
                'vendredi' in jours,
                professeur
            ))
        else:
            db.execute('''
            INSERT INTO absences (professeur, lundi, mardi, mercredi, jeudi, vendredi)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                professeur,
                'lundi' in jours,
                'mardi' in jours,
                'mercredi' in jours,
                'jeudi' in jours,
                'vendredi' in jours
            ))

# Fonctions pour les événements
def get_upcoming_events():
    db = get_db()
    today = date.today()
    return db.execute('''
        SELECT * FROM events 
        WHERE date >= ? 
        ORDER BY date ASC
    ''', (today,)).fetchall()

def add_event(title, event_date, description):
    db = get_db()
    with db:
        db.execute('''
        INSERT INTO events (title, date, description)
        VALUES (?, ?, ?)
        ''', (title, event_date, description))

def delete_event(event_id):
    db = get_db()
    with db:
        db.execute('DELETE FROM events WHERE id = ?', (event_id,))
