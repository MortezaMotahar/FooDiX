import sqlite3
import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, session, flash


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("pip install python-dotenv")

app = Flask(__name__)


if os.environ.get('SECRET_KEY'):
    app.secret_key = os.environ['SECRET_KEY']
else:
    app.secret_key = secrets.token_hex(32)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'feedback.db')
print(f"Database path: {DATABASE_PATH}")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'registered',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.close()
    print("Database initialized (table created if not exists)")

init_db()

ADMIN_USER = os.environ.get('ADMIN_USER', 'BlackHole')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'Tesla369')

def is_logged_in():
    return session.get('logged_in', False)


@app.route('/', methods=['GET', 'POST'])
def submit_feedback():
    if request.method == 'POST':
        title = request.form['title']
        message = request.form['message']
        if not title or not message:
            flash('عنوان و پیام هر دو الزامی هستند', 'danger')
        else:
            conn = None
            try:
                conn = get_db_connection()
                conn.execute(
                    "INSERT INTO feedbacks (title, message) VALUES (?, ?)",
                    (title, message)
                )
                conn.commit()
                flash('فیدبک شما با موفقیت ثبت شد', 'success')
                return redirect(url_for('submit_feedback'))
            except Exception as e:
                flash(f'خطا در ثبت فیدبک: {str(e)}', 'danger')
                print(f"Error inserting: {e}")
            finally:
                if conn:
                    conn.close()
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است', 'danger')
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    feedbacks = conn.execute("SELECT * FROM feedbacks ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('dashboard.html', feedbacks=feedbacks)

@app.route('/admin/update/<int:feedback_id>', methods=['POST'])
def update_status(feedback_id):
    if not is_logged_in():
        return redirect(url_for('admin_login'))
    new_status = request.form['status']
    conn = get_db_connection()
    conn.execute("UPDATE feedbacks SET status = ? WHERE id = ?", (new_status, feedback_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)