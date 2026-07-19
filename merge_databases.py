import os
import glob
import sqlite3
from collections import defaultdict

# ---------- تنظیم مسیرها نسبت به محل این فایل ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_DB = os.path.join(BASE_DIR, "food_planner.db")
CLIENT_DB_FOLDER = os.path.join(BASE_DIR, "client_dbs")

def merge_all():
    # بررسی وجود پوشه مشتریان
    if not os.path.exists(CLIENT_DB_FOLDER):
        print(f"❌ پوشه '{CLIENT_DB_FOLDER}' پیدا نشد.")
        print(f"✅ لطفاً پوشه را در این مسیر بسازید:\n   {CLIENT_DB_FOLDER}")
        print("   سپس فایل‌های دیتابیس مشتریان (با پسوند .db) را داخل آن قرار دهید.")
        return

    # اتصال به دیتابیس اصلی
    main_conn = sqlite3.connect(MAIN_DB)
    main_cursor = main_conn.cursor()

    # ایجاد جداول در صورت نبود (ساختار مطابق برنامه اصلی)
    main_cursor.executescript('''
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            ingredients TEXT NOT NULL,
            cost REAL NOT NULL,
            calories INTEGER NOT NULL,
            category TEXT NOT NULL,
            food_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS budget (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            daily_budget REAL NOT NULL,
            weekly_budget REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS consumption_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_id INTEGER NOT NULL,
            consumption_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS food_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_id INTEGER NOT NULL,
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE,
            UNIQUE(food_id)
        );
        CREATE TABLE IF NOT EXISTS food_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            cost REAL NOT NULL,
            calories INTEGER NOT NULL,
            category TEXT NOT NULL,
            food_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            submitted_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    main_cursor.execute("SELECT COUNT(*) FROM budget")
    if main_cursor.fetchone()[0] == 0:
        main_cursor.execute("INSERT INTO budget (id, daily_budget, weekly_budget) VALUES (1, 150000, 1000000)")

    rating_accumulator = defaultdict(list)

    # پیدا کردن همه فایل‌های دیتابیس داخل پوشه client_dbs
    db_files = glob.glob(os.path.join(CLIENT_DB_FOLDER, "*.db"))
    if not db_files:
        print("⚠️ هیچ فایل دیتابیسی با پسوند .db در پوشه client_dbs یافت نشد.")
        main_conn.close()
        return

    print(f"🔍 تعداد فایل‌های دیتابیس مشتری برای ادغام: {len(db_files)}")

    for db_file in db_files:
        print(f"\n📂 در حال پردازش: {db_file}")
        client_conn = sqlite3.connect(db_file)
        client_cursor = client_conn.cursor()

        # نگاشت آیدی قدیمی به جدید برای این فایل
        id_map = {}

        # غذاها
        client_cursor.execute("SELECT id, name, ingredients, cost, calories, category, food_type FROM foods")
        for row in client_cursor.fetchall():
            old_id, name, ingredients, cost, calories, category, food_type = row
            # بررسی وجود غذا در دیتابیس اصلی
            main_cursor.execute("SELECT id FROM foods WHERE name = ?", (name,))
            existing = main_cursor.fetchone()
            if existing:
                new_food_id = existing[0]
            else:
                main_cursor.execute('''
                    INSERT INTO foods (name, ingredients, cost, calories, category, food_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, ingredients, cost, calories, category, food_type))
                new_food_id = main_cursor.lastrowid
                print(f"   ✅ غذای جدید اضافه شد: {name}")
            id_map[old_id] = new_food_id

        # امتیازها
        client_cursor.execute("SELECT food_id, rating FROM food_ratings")
        for old_food_id, rating in client_cursor.fetchall():
            new_food_id = id_map.get(old_food_id)
            if new_food_id:
                main_cursor.execute("SELECT name FROM foods WHERE id = ?", (new_food_id,))
                name_row = main_cursor.fetchone()
                if name_row:
                    rating_accumulator[name_row[0]].append(rating)

        # تاریخچه مصرف 
        client_cursor.execute("SELECT food_id, consumption_date, created_at FROM consumption_history")
        for old_food_id, cons_date, created_at in client_cursor.fetchall():
            new_food_id = id_map.get(old_food_id)
            if new_food_id:
                main_cursor.execute('''
                    INSERT INTO consumption_history (food_id, consumption_date, created_at)
                    VALUES (?, ?, ?)
                ''', (new_food_id, cons_date, created_at))

        # پیشنهادات غذا 
        client_cursor.execute('''
            SELECT name, ingredients, cost, calories, category, food_type, submitted_by, created_at
            FROM food_suggestions WHERE status = 'pending'
        ''')
        for sugg in client_cursor.fetchall():
            name, ingredients, cost, calories, category, food_type, submitted_by, created_at = sugg
            main_cursor.execute('''
                INSERT INTO food_suggestions (name, ingredients, cost, calories, category, food_type, status, submitted_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            ''', (name, ingredients, cost, calories, category, food_type, submitted_by, created_at))

        client_conn.close()
        print(f"   ✔️ پردازش این فایل تمام شد.")

    # ----- به‌روزرسانی امتیازها در دیتابیس اصلی با میانگین -----
    print("\n⭐ در حال بروزرسانی امتیازهای نهایی...")
    for food_name, ratings in rating_accumulator.items():
        avg_rating = sum(ratings) / len(ratings)
        final_rating = int(round(avg_rating))
        final_rating = max(1, min(5, final_rating))
        main_cursor.execute("SELECT id FROM foods WHERE name = ?", (food_name,))
        row = main_cursor.fetchone()
        if row:
            food_id = row[0]
            main_cursor.execute('''
                INSERT OR REPLACE INTO food_ratings (food_id, rating)
                VALUES (?, ?)
            ''', (food_id, final_rating))
            print(f"   {food_name} -> {final_rating} ستاره (بر اساس {len(ratings)} نظر)")

    main_conn.commit()
    main_conn.close()
    print("\n🎉 ادغام کامل شد! حالا می‌توانید برنامه اصلی را اجرا کنید.")

if __name__ == "__main__":
    merge_all()
