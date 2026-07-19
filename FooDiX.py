#-----Systems analysis and design----
# _______________________________________________ FooDiX ___________________________________________________
# Morteza Motahar , AmirAli Keshavarzi
import sys
import os
import sqlite3
import random
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

# -------------------------------
# تعیین مسیر مطلق برای دیتابیس (کنار کد)
# -------------------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "food_planner.db")


try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTableWidget, QTableWidgetItem, QLabel, QLineEdit,
        QComboBox, QSpinBox, QDoubleSpinBox, QMessageBox, QTabWidget,
        QGroupBox, QFormLayout, QHeaderView, QListWidget, QListWidgetItem,
        QDialog, QDialogButtonBox, QTextEdit, QDateEdit, QProgressBar,
        QSplitter, QFrame, QGridLayout, QMenuBar, QMenu
    )
    from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal
    from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QAction
    
    import matplotlib
    import matplotlib.pyplot as plt
    matplotlib.use('QtAgg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d import Axes3D
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
except ImportError as e:
    print(f"خطا در وارد کردن کتابخانه‌ها: {e}")
    print("لطفاً دستورات زیر را اجرا کنید:")
    print("pip install PyQt6 matplotlib numpy scikit-learn")
    sys.exit(1)

# -------------------------------
# مدیریت پایگاه داده SQLite
# -------------------------------
class DatabaseManager:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # جدول غذاها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS foods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                ingredients TEXT NOT NULL,
                cost REAL NOT NULL,
                calories INTEGER NOT NULL,
                category TEXT NOT NULL,
                food_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # جدول بودجه
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                daily_budget REAL NOT NULL,
                weekly_budget REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute("SELECT COUNT(*) FROM budget")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO budget (id, daily_budget, weekly_budget)
                VALUES (1, 150000, 1000000)
            ''')
        
        # جدول تاریخچه مصرف
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consumption_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                food_id INTEGER NOT NULL,
                consumption_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
            )
        ''')
        
        # جدول امتیازات غذا
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS food_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                food_id INTEGER NOT NULL,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
            )
        ''')
        
        # جدول کاربران (فقط ادمین)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin'))
            )
        ''')
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                           ("Morteza", "1190389916M", "admin"))
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                           ("AmirAli", "AK2006", "admin"))
        
        # جدول پیشنهادات غذا
        cursor.execute('''
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
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def authenticate_admin(self, username: str, password: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
        row = cursor.fetchone()
        conn.close()
        return row is not None and row[0] == 'admin'
    
    def add_food(self, name: str, ingredients: List[str], cost: float, 
                 calories: int, category: str, food_type: str) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            ingredients_str = ", ".join(ingredients)
            cursor.execute('''
                INSERT INTO foods (name, ingredients, cost, calories, category, food_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, ingredients_str, cost, calories, category, food_type))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_food(self, food_id: int, name: str, ingredients: List[str], 
                   cost: float, calories: int, category: str, food_type: str) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            ingredients_str = ", ".join(ingredients)
            cursor.execute('''
                UPDATE foods 
                SET name = ?, ingredients = ?, cost = ?, calories = ?, 
                    category = ?, food_type = ?
                WHERE id = ?
            ''', (name, ingredients_str, cost, calories, category, food_type, food_id))
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
    
    def delete_food(self, food_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM foods WHERE id = ?", (food_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    def get_all_foods(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.*, COALESCE(AVG(r.rating), 0) as avg_rating
            FROM foods f
            LEFT JOIN food_ratings r ON f.id = r.food_id
            GROUP BY f.id
            ORDER BY f.category, f.name
        ''')
        foods = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return foods
    
    def get_food_by_id(self, food_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM foods WHERE id = ?", (food_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def search_foods(self, search_term: str = "", category: str = "", max_cost: float = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        query = '''
            SELECT f.*, COALESCE(AVG(r.rating), 0) as avg_rating
            FROM foods f
            LEFT JOIN food_ratings r ON f.id = r.food_id
            WHERE 1=1
        '''
        params = []
        if search_term:
            query += " AND (f.name LIKE ? OR f.ingredients LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        if category and category != "همه":
            query += " AND f.category = ?"
            params.append(category)
        if max_cost:
            query += " AND f.cost <= ?"
            params.append(max_cost)
        query += " GROUP BY f.id ORDER BY f.cost ASC"
        cursor.execute(query, params)
        foods = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return foods
    
    def get_budget(self) -> Dict[str, float]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT daily_budget, weekly_budget FROM budget WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        return {"daily": row[0], "weekly": row[1]} if row else {"daily": 150000, "weekly": 1000000}
    
    def update_budget(self, daily: float, weekly: float) -> bool:
        daily = max(0, daily)
        weekly = max(0, weekly)
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE budget 
            SET daily_budget = ?, weekly_budget = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        ''', (daily, weekly))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    def add_consumption(self, food_id: int, date: str = None) -> bool:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO consumption_history (food_id, consumption_date)
            VALUES (?, ?)
        ''', (food_id, date))
        conn.commit()
        conn.close()
        return True
    
    def get_today_consumption(self) -> List[Dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT h.*, f.name, f.cost, f.calories, f.category
            FROM consumption_history h
            JOIN foods f ON h.food_id = f.id
            WHERE h.consumption_date = ?
            ORDER BY h.created_at DESC
        ''', (today,))
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return history
    
    def get_today_total_cost(self) -> float:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(f.cost), 0) as total
            FROM consumption_history h
            JOIN foods f ON h.food_id = f.id
            WHERE h.consumption_date = ?
        ''', (today,))
        total = cursor.fetchone()[0]
        conn.close()
        return total
    
    def get_all_history(self, limit: int = 50) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT h.*, f.name, f.cost, f.calories
            FROM consumption_history h
            JOIN foods f ON h.food_id = f.id
            ORDER BY h.consumption_date DESC, h.created_at DESC
            LIMIT ?
        ''', (limit,))
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return history
    
    def delete_history_entry(self, history_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM consumption_history WHERE id = ?", (history_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    def rate_food(self, food_id: int, rating: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO food_ratings (food_id, rating)
            VALUES (?, ?)
        ''', (food_id, rating))
        conn.commit()
        conn.close()
        return True
    
    def add_suggestion(self, name: str, ingredients: List[str], cost: float, calories: int,
                       category: str, food_type: str, submitted_by: str = "کاربر") -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM foods WHERE name = ?", (name,))
        if cursor.fetchone():
            conn.close()
            return False
        cursor.execute("SELECT id FROM food_suggestions WHERE name = ? AND status = 'pending'", (name,))
        if cursor.fetchone():
            conn.close()
            return False
        ingredients_str = ", ".join(ingredients)
        cursor.execute('''
            INSERT INTO food_suggestions (name, ingredients, cost, calories, category, food_type, submitted_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, ingredients_str, cost, calories, category, food_type, submitted_by))
        conn.commit()
        conn.close()
        return True
    
    def get_pending_suggestions(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM food_suggestions
            WHERE status = 'pending'
            ORDER BY created_at DESC
        ''')
        suggestions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return suggestions
    
    def approve_suggestion(self, suggestion_id: int) -> bool:
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM food_suggestions WHERE id = ?", (suggestion_id,))
            sugg = cursor.fetchone()
            if not sugg:
                return False
            cursor.execute("SELECT id FROM foods WHERE name = ?", (sugg['name'],))
            if cursor.fetchone():
                return False
            ingredients_list = sugg['ingredients'].split(", ")
            success = self.add_food(sugg['name'], ingredients_list, sugg['cost'],
                                    sugg['calories'], sugg['category'], sugg['food_type'])
            if success:
                cursor.execute("UPDATE food_suggestions SET status = 'approved' WHERE id = ?", (suggestion_id,))
                conn.commit()
            return success
        except Exception as e:
            print(f"Error in approve_suggestion: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def reject_suggestion(self, suggestion_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE food_suggestions SET status = 'rejected' WHERE id = ?", (suggestion_id,))
        conn.commit()
        conn.close()
        return True
    
    def get_food_stats(self) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM foods")
        total_foods = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM consumption_history")
        total_consumptions = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(cost) FROM foods")
        row = cursor.fetchone()
        avg_cost = row[0] if row[0] is not None else 0.0
        conn.close()
        return {
            "total_foods": total_foods,
            "total_consumptions": total_consumptions,
            "avg_cost": avg_cost
        }
    
    def get_unrated_foods(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.*, COALESCE(AVG(r.rating), 0) as avg_rating
            FROM foods f
            LEFT JOIN food_ratings r ON f.id = r.food_id
            GROUP BY f.id
            HAVING AVG(r.rating) IS NULL
        ''')
        foods = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return foods

# -------------------------------
# کلاس Food (مدل داده)
# -------------------------------
class Food:
    def __init__(self, id: int, name: str, ingredients: List[str], cost: float, 
                 calories: int, category: str, food_type: str, avg_rating: float = 0):
        self.id = id
        self.name = name
        self.ingredients = ingredients
        self.cost = cost
        self.calories = calories
        self.category = category
        self.food_type = food_type
        self.avg_rating = avg_rating
        self.cluster_label = -1
    
    @staticmethod
    def from_dict(data: Dict) -> 'Food':
        ingredients = data['ingredients'].split(", ") if data['ingredients'] else []
        return Food(
            id=data['id'],
            name=data['name'],
            ingredients=ingredients,
            cost=data['cost'],
            calories=data['calories'],
            category=data['category'],
            food_type=data['food_type'],
            avg_rating=data.get('avg_rating', 0)
        )

# -------------------------------
# بخش هوشمند ML
# -------------------------------
class SmartRecommender:
    def __init__(self, foods: List[Food]):
        self.foods = foods
        self.model = None
        self.scaler = StandardScaler()
        self.labels = None
        
    def prepare_features(self, foods_subset: List[Food] = None) -> np.ndarray:
        if foods_subset is None:
            foods_subset = [f for f in self.foods if f.avg_rating > 0]
        if not foods_subset:
            return np.array([])
        features = []
        for food in foods_subset:
            features.append([food.cost, food.calories, food.avg_rating * 10000])
        return np.array(features)
    
    def cluster_foods(self, n_clusters: int = 4) -> bool:
        rated_foods = [f for f in self.foods if f.avg_rating > 0]
        if len(rated_foods) < n_clusters:
            return False
        X = self.prepare_features(rated_foods)
        if len(X) == 0:
            return False
        X_scaled = self.scaler.fit_transform(X)
        self.model = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        self.labels = self.model.fit_predict(X_scaled)
        label_idx = 0
        for food in self.foods:
            if food.avg_rating > 0:
                food.cluster_label = int(self.labels[label_idx])
                label_idx += 1
            else:
                food.cluster_label = -1
        return True
    
    def get_cluster_stats(self) -> Dict[int, Dict[str, float]]:
        if self.labels is None:
            return {}
        rated_foods = [f for f in self.foods if f.avg_rating > 0]
        stats = {}
        for label in set(self.labels):
            cluster_foods = [rated_foods[i] for i in range(len(rated_foods)) if self.labels[i] == label]
            if cluster_foods:
                stats[label] = {
                    "avg_cost": np.mean([f.cost for f in cluster_foods]),
                    "avg_cal": np.mean([f.calories for f in cluster_foods]),
                    "avg_rating": np.mean([f.avg_rating for f in cluster_foods]),
                    "count": len(cluster_foods)
                }
        return stats
    
    def get_balanced_cluster_label(self) -> int:
        rated_foods = [f for f in self.foods if f.avg_rating > 0]
        if not rated_foods or self.labels is None:
            return -1
        X = self.prepare_features(rated_foods)
        X_scaled = self.scaler.transform(X)
        global_center = np.mean(X_scaled, axis=0)
        centers = self.model.cluster_centers_
        distances = [np.linalg.norm(center - global_center) for center in centers]
        return int(np.argmin(distances))

# -------------------------------
# دیالوگ‌های مختلف
# -------------------------------
class FoodDialog(QDialog):
    def __init__(self, food: Optional[Food] = None, parent=None):
        super().__init__(parent)
        self.food = food
        self.setWindowTitle("ویرایش غذا" if food else "افزودن غذای جدید")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setup_ui()
        if food:
            self.load_food_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("مثال: عدس پلو")
        self.ingredients_edit = QTextEdit()
        self.ingredients_edit.setPlaceholderText("هر ماده را در یک خط بنویسید\nمثال:\nبرنج\nعدس\nکشمش")
        self.ingredients_edit.setMaximumHeight(100)
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 1000000)
        self.cost_spin.setSuffix(" تومان")
        self.cost_spin.setSingleStep(5000)
        self.calories_spin = QSpinBox()
        self.calories_spin.setRange(0, 2000)
        self.calories_spin.setSuffix(" کالری")
        self.calories_spin.setSingleStep(50)
        self.category_combo = QComboBox()
        self.category_combo.addItems(["صبحانه", "ناهار", "شام", "میان‌وعده","ناهار و شام"])
        self.type_combo = QComboBox()
        self.type_combo.addItems(["گیاهی", "گوشتی"])
        form_layout.addRow("نام غذا:", self.name_edit)
        form_layout.addRow("مواد اولیه:", self.ingredients_edit)
        form_layout.addRow("هزینه تقریبی:", self.cost_spin)
        form_layout.addRow("کالری تقریبی:", self.calories_spin)
        form_layout.addRow("دسته‌بندی:", self.category_combo)
        form_layout.addRow("نوع غذا:", self.type_combo)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addLayout(form_layout)
        layout.addWidget(buttons)
        self.setLayout(layout)
    
    def load_food_data(self):
        self.name_edit.setText(self.food.name)
        self.ingredients_edit.setPlainText("\n".join(self.food.ingredients))
        self.cost_spin.setValue(self.food.cost)
        self.calories_spin.setValue(self.food.calories)
        self.category_combo.setCurrentText(self.food.category)
        self.type_combo.setCurrentText(self.food.food_type)
    
    def get_food_data(self) -> Tuple[str, List[str], float, int, str, str]:
        name = self.name_edit.text().strip()
        ingredients = [line.strip() for line in self.ingredients_edit.toPlainText().split('\n') if line.strip()]
        cost = self.cost_spin.value()
        calories = self.calories_spin.value()
        category = self.category_combo.currentText()
        food_type = self.type_combo.currentText()
        return name, ingredients, cost, calories, category, food_type

class SuggestFoodDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("پیشنهاد غذای جدید")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("نام غذا")
        self.ingredients_edit = QTextEdit()
        self.ingredients_edit.setPlaceholderText("هر ماده در یک خط")
        self.ingredients_edit.setMaximumHeight(100)
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 1000000)
        self.cost_spin.setSuffix(" تومان")
        self.calories_spin = QSpinBox()
        self.calories_spin.setRange(0, 2000)
        self.calories_spin.setSuffix(" کالری")
        self.category_combo = QComboBox()
        self.category_combo.addItems(["صبحانه", "ناهار", "شام", "میان‌وعده","ناهار و شام"])
        self.type_combo = QComboBox()
        self.type_combo.addItems(["گیاهی", "گوشتی"])
        form_layout.addRow("نام غذا:", self.name_edit)
        form_layout.addRow("مواد اولیه:", self.ingredients_edit)
        form_layout.addRow("هزینه تقریبی:", self.cost_spin)
        form_layout.addRow("کالری تقریبی:", self.calories_spin)
        form_layout.addRow("دسته‌بندی:", self.category_combo)
        form_layout.addRow("نوع غذا:", self.type_combo)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addLayout(form_layout)
        layout.addWidget(buttons)
        self.setLayout(layout)
    
    def get_suggestion_data(self) -> Tuple[str, List[str], float, int, str, str]:
        name = self.name_edit.text().strip()
        ingredients = [line.strip() for line in self.ingredients_edit.toPlainText().split('\n') if line.strip()]
        cost = self.cost_spin.value()
        calories = self.calories_spin.value()
        category = self.category_combo.currentText()
        food_type = self.type_combo.currentText()
        return name, ingredients, cost, calories, category, food_type

class RatingDialog(QDialog):
    def __init__(self, food_name: str, current_rating: int = 0, parent=None):
        super().__init__(parent)
        self.food_name = food_name
        self.rating = current_rating
        self.setWindowTitle(f"امتیازدهی به {food_name}")
        self.setModal(True)
        self.setFixedSize(300, 150)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"لطفاً به غذای '{self.food_name}' امتیاز دهید:"))
        self.rating_spin = QSpinBox()
        self.rating_spin.setRange(1, 5)
        self.rating_spin.setValue(self.rating if self.rating > 0 else 3)
        self.rating_spin.setSuffix(" ستاره")
        layout.addWidget(self.rating_spin)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
    
    def get_rating(self) -> int:
        return self.rating_spin.value()

class AdminLoginDialog(QDialog):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("ورود ادمین")
        self.setModal(True)
        self.setFixedSize(350, 200)
        self.setup_ui()
        self.success = False
    
    def setup_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("نام کاربری")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("رمز عبور")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("نام کاربری:", self.username_edit)
        form_layout.addRow("رمز عبور:", self.password_edit)
        layout.addLayout(form_layout)
        btn_login = QPushButton("ورود")
        btn_login.clicked.connect(self.do_login)
        btn_cancel = QPushButton("انصراف")
        btn_cancel.clicked.connect(self.reject)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_login)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def do_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        if self.db.authenticate_admin(username, password):
            self.success = True
            self.accept()
        else:
            QMessageBox.warning(self, "خطا", "نام کاربری یا رمز عبور نادرست است.")

# -------------------------------
# ویجت نمودار سه‌بعدی
# -------------------------------
class MplCanvas3D(FigureCanvas):
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111, projection='3d')
    
    def plot_clusters(self, foods: List[Food], labels: np.ndarray):
        self.ax.clear()
        if not foods:
            self.draw()
            return
        
        rated_foods = [f for f in foods if f.avg_rating > 0]
        unrated_foods = [f for f in foods if f.avg_rating == 0]
        
        if rated_foods:
            clusters = {}
            for food in rated_foods:
                if food.cluster_label != -1:
                    clusters.setdefault(food.cluster_label, []).append(food)
            
            num_clusters = len(clusters)
            colors = plt.cm.tab10(np.linspace(0, 1, num_clusters))
            
            for i, (label, cluster_foods) in enumerate(clusters.items()):
                x = [f.cost for f in cluster_foods]
                y = [f.calories for f in cluster_foods]
                z = [f.avg_rating for f in cluster_foods]
                self.ax.scatter(
                    x, y, z,
                    c=[colors[i]],
                    s=50,
                    label=f'Cluster {label}',
                    alpha=0.7,
                    edgecolors='k'
                )
        
        if unrated_foods:
            ux = [f.cost for f in unrated_foods]
            uy = [f.calories for f in unrated_foods]
            uz = [0] * len(unrated_foods)
            self.ax.scatter(ux, uy, uz, c='gray',label ='No Points', s=40, alpha=0.6, edgecolors='gray')
        
        self.ax.legend(loc='best', fontsize=8)
        
        self.ax.set_xlabel('Cost (Toman)', fontsize=10)
        self.ax.set_ylabel('Calories', fontsize=10)
        self.ax.set_zlabel('Rating', fontsize=10)
        self.ax.set_title('3D Food Clustering', fontsize=12, fontweight='bold')
        self.fig.tight_layout()
        self.draw()

# -------------------------------
# پنجره اصلی برنامه
# -------------------------------
class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.user_role = 'user'
        self.load_data()
        
        self.setWindowTitle("🍲 سیستم هوشمند تغذیه دانشجویی")
        self.setMinimumSize(1100, 750)
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #cccccc; 
                border-radius: 8px; 
                margin-top: 12px; 
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 15px; 
                padding: 0 8px;
                color: #2c3e50;
            }
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                border: none; 
                padding: 8px 15px; 
                border-radius: 5px; 
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton#delete_btn { background-color: #e74c3c; }
            QPushButton#delete_btn:hover { background-color: #c0392b; }
            QPushButton#success_btn { background-color: #27ae60; }
            QPushButton#success_btn:hover { background-color: #229954; }
            QTableWidget { 
                gridline-color: #d0d0d0; 
                selection-background-color: #a6d5fa;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section { 
                background-color: #2c3e50; 
                color: white;
                padding: 6px; 
                border: 1px solid #1a2632;
                font-weight: bold;
                border-radius: 8px;
            }
            QTabWidget::pane { border: 1px solid #cccccc; background: white; }
            QTabBar::tab { 
                background: #ecf0f1; 
                padding: 8px 15px; 
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected { background: #3498db; color: white; }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
        """)
        
        self.setup_menu()
        self.setup_ui()
        self.refresh_all()
    
    def setup_menu(self):
        menubar = self.menuBar()
        help_menu = menubar.addMenu("راهنما")
        help_action = QAction("📖 راهنما", self)
        help_action.triggered.connect(self.show_help_tab)
        help_menu.addAction(help_action)
        
        self.admin_menu_action = QAction("🔐 ورود ادمین", self)
        self.admin_menu_action.triggered.connect(self.toggle_admin_mode)
        menubar.addAction(self.admin_menu_action)
    
    def show_help_tab(self):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "📖 راهنما":
                self.tab_widget.setCurrentIndex(i)
                break
    
    def load_data(self):
        foods_data = self.db.get_all_foods()
        self.foods = [Food.from_dict(f) for f in foods_data]
        self.budget = self.db.get_budget()
        self.recommender = SmartRecommender(self.foods)
    
    def refresh_all(self):
        self.load_data()
        self.refresh_recommender()
        self.update_status_bar()
        self.load_foods_table()
        self.load_history()
        if self.user_role == 'admin':
            self.load_pending_suggestions()
            self.update_stats_display()
    
    def refresh_recommender(self):
        self.recommender.foods = self.foods
        rated_count = len([f for f in self.foods if f.avg_rating > 0])
        if rated_count >= 4:
            self.recommender.cluster_foods(n_clusters=4)
        elif rated_count >= 3:
            self.recommender.cluster_foods(n_clusters=3)
        elif rated_count >= 2:
            self.recommender.cluster_foods(n_clusters=2)
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        self.setup_header(main_layout)
        
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        self.setup_foods_tab()
        self.setup_recommend_tab()
        self.setup_budget_tab()
        self.setup_history_tab()
        self.setup_help_tab()
        
        if self.user_role == 'admin':
            self.setup_analysis_tab()
            self.setup_stats_tab()
            self.setup_suggestions_tab()
    
    def setup_header(self, parent_layout):
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        header_layout = QGridLayout(header_frame)
        
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        
        header_layout.addWidget(self.status_label, 0, 0, 1, 2)
        header_layout.addWidget(self.stats_label, 1, 0, 1, 2)
        
        parent_layout.addWidget(header_frame)
    
    def toggle_admin_mode(self):
        if self.user_role == 'admin':
            self.user_role = 'user'
            self.admin_menu_action.setText("🔐 ورود ادمین")
            self.rebuild_ui_for_role()
            QMessageBox.information(self, "خروج", "از حالت ادمین خارج شدید.")
        else:
            login_dlg = AdminLoginDialog(self.db, self)
            if login_dlg.exec() == QDialog.DialogCode.Accepted and login_dlg.success:
                self.user_role = 'admin'
                self.admin_menu_action.setText("🚪 خروج از حالت ادمین")
                self.rebuild_ui_for_role()
                QMessageBox.information(self, "ورود", "به حالت ادمین وارد شدید.")
    
    def rebuild_ui_for_role(self):
        self.tab_widget.clear()
        self.setup_foods_tab()
        self.setup_recommend_tab()
        self.setup_budget_tab()
        self.setup_history_tab()
        self.setup_help_tab()
        if self.user_role == 'admin':
            self.setup_analysis_tab()
            self.setup_stats_tab()
            self.setup_suggestions_tab()
            self.load_pending_suggestions()
            self.update_stats_display()
            self.update_cluster_plot()
        self.refresh_all()
    
    # -------------------- تب غذاها --------------------
    def setup_foods_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        control_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 جستجو در نام یا مواد اولیه...")
        self.search_edit.textChanged.connect(self.filter_foods_table)
        self.category_filter = QComboBox()
        self.category_filter.addItems(["همه", "صبحانه", "ناهار", "شام", "میان‌وعده","ناهار و شام"])
        self.category_filter.currentTextChanged.connect(self.filter_foods_table)
        control_layout.addWidget(self.search_edit, 2)
        control_layout.addWidget(self.category_filter, 1)
        
        if self.user_role == 'admin':
            add_btn = QPushButton("➕ افزودن")
            add_btn.clicked.connect(self.add_food)
            edit_btn = QPushButton("✏️ ویرایش")
            edit_btn.clicked.connect(self.edit_food)
            delete_btn = QPushButton("❌ حذف")
            delete_btn.setObjectName("delete_btn")
            delete_btn.clicked.connect(self.delete_food)
            control_layout.addWidget(add_btn)
            control_layout.addWidget(edit_btn)
            control_layout.addWidget(delete_btn)
        else:
            suggest_btn = QPushButton("➕ پیشنهاد غذای جدید")
            suggest_btn.clicked.connect(self.suggest_new_food)
            control_layout.addWidget(suggest_btn)
        
        rate_btn = QPushButton("⭐ امتیاز")
        rate_btn.setObjectName("success_btn")
        rate_btn.clicked.connect(self.rate_food)
        control_layout.addWidget(rate_btn)
        
        layout.addLayout(control_layout)
        
        self.foods_table = QTableWidget()
        self.foods_table.setColumnCount(7)
        self.foods_table.setHorizontalHeaderLabels(["ID", "نام", "دسته", "نوع", "هزینه", "کالری", "امتیاز"])
        self.foods_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.foods_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.foods_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.foods_table.setAlternatingRowColors(True)
        self.foods_table.setColumnHidden(0, True)
        layout.addWidget(self.foods_table)
        
        self.tab_widget.addTab(tab, "📋 مدیریت غذاها")
    
    # -------------------- تب پیشنهاد هوشمند --------------------
    def setup_recommend_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        recommend_group = QGroupBox("🤖 پیشنهاد هوشمند")
        recommend_layout = QVBoxLayout()
        
        # ردیف اول: سه کامبوباکس به صورت افقی با فاصله‌گذاری یکنواخت
        filter_layout = QHBoxLayout()
        
        # گروه اول: نوع پیشنهاد (چپ)
        filter_layout.addStretch(1)
        filter_layout.addWidget(QLabel("نوع پیشنهاد"))
        self.pref_combo = QComboBox()
        self.pref_combo.addItems(["متعادل", "ارزان‌ترین", "پرکالری", "بهترین امتیاز", "تنوع غذایی"])
        filter_layout.addWidget(self.pref_combo)
        filter_layout.addStretch(1)
        
        # گروه دوم: وعده غذایی (وسط)
        filter_layout.addWidget(QLabel("وعده غذایی"))
        self.recommend_category_filter = QComboBox()
        self.recommend_category_filter.addItems(["همه", "صبحانه", "ناهار", "شام", "میان‌وعده", "ناهار و شام"])
        filter_layout.addWidget(self.recommend_category_filter)
        filter_layout.addStretch(1)
        
        # گروه سوم: نوع غذا (راست)
        filter_layout.addWidget(QLabel("نوع غذا"))
        self.recommend_type_filter = QComboBox()
        self.recommend_type_filter.addItems(["همه", "گیاهی", "گوشتی"])
        filter_layout.addWidget(self.recommend_type_filter)
        filter_layout.addStretch(1)
        
        # دکمه دریافت پیشنهادات
        self.recommend_btn = QPushButton("🎯 دریافت پیشنهادات")
        self.recommend_btn.clicked.connect(self.show_recommendations)
        
        self.recommend_list = QListWidget()
        self.recommend_list.setMinimumHeight(200)
        
        button_layout = QHBoxLayout()
        self.consume_btn = QPushButton("✅ ثبت مصرف")
        self.consume_btn.clicked.connect(self.consume_selected)
        self.rate_selected_btn = QPushButton("⭐ امتیاز به غذای انتخاب شده")
        self.rate_selected_btn.clicked.connect(self.rate_selected_food)
        button_layout.addWidget(self.consume_btn)
        button_layout.addWidget(self.rate_selected_btn)
        
        recommend_layout.addLayout(filter_layout)
        recommend_layout.addWidget(self.recommend_btn)
        recommend_layout.addWidget(QLabel("🍽️ پیشنهادات:"))
        recommend_layout.addWidget(self.recommend_list)
        recommend_layout.addLayout(button_layout)
        recommend_group.setLayout(recommend_layout)
        layout.addWidget(recommend_group)
        self.tab_widget.addTab(tab, "🎯 پیشنهاد هوشمند")
    
    # -------------------- تب بودجه --------------------
    def setup_budget_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        budget_group = QGroupBox("💰 تنظیم بودجه روزانه و هفتگی")
        budget_layout = QFormLayout()
        self.daily_budget_spin = QDoubleSpinBox()
        self.daily_budget_spin.setRange(0, 1000000)
        self.daily_budget_spin.setSuffix(" تومان")
        self.daily_budget_spin.setValue(self.budget['daily'])
        self.weekly_budget_spin = QDoubleSpinBox()
        self.weekly_budget_spin.setRange(0, 10000000)
        self.weekly_budget_spin.setSuffix(" تومان")
        self.weekly_budget_spin.setValue(self.budget['weekly'])
        save_budget_btn = QPushButton("💾 ذخیره بودجه")
        save_budget_btn.clicked.connect(self.save_budget)
        budget_layout.addRow("بودجه روزانه:", self.daily_budget_spin)
        budget_layout.addRow("بودجه هفتگی:", self.weekly_budget_spin)
        budget_layout.addRow(save_budget_btn)
        budget_group.setLayout(budget_layout)
        layout.addWidget(budget_group)
        layout.addStretch()
        self.tab_widget.addTab(tab, "💰 بودجه")
    
    # -------------------- تب تحلیل خوشه‌ها (فقط ادمین) --------------------
    def setup_analysis_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        control_layout = QHBoxLayout()
        self.cluster_btn = QPushButton("🔄 بروزرسانی نمودار خوشه‌بندی")
        self.cluster_btn.clicked.connect(self.update_cluster_plot)
        self.cluster_info_label = QLabel()
        self.cluster_info_label.setStyleSheet("padding: 10px; background-color: #ecf0f1; border-radius: 5px; font-family: monospace;")
        control_layout.addWidget(self.cluster_btn)
        control_layout.addStretch()
        self.canvas = MplCanvas3D(self, width=10, height=7)
        layout.addLayout(control_layout)
        layout.addWidget(self.cluster_info_label)
        layout.addWidget(self.canvas)
        self.tab_widget.addTab(tab, "📊 تحلیل خوشه‌ها")
        if len([f for f in self.foods if f.avg_rating > 0]) >= 2:
            self.update_cluster_plot()
    
    # -------------------- تب آمار (فقط ادمین) --------------------
    def setup_stats_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        stats_group = QGroupBox("📈 آمار و گزارشات")
        stats_layout = QVBoxLayout()
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("font-family: monospace; font-size: 12px;")
        refresh_stats_btn = QPushButton("🔄 بروزرسانی آمار")
        refresh_stats_btn.clicked.connect(self.update_stats_display)
        stats_layout.addWidget(self.stats_text)
        stats_layout.addWidget(refresh_stats_btn)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        self.tab_widget.addTab(tab, "📈 آمار")
    
    # -------------------- تب پیشنهادات (فقط ادمین) --------------------
    def setup_suggestions_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        suggestions_group = QGroupBox("📝 پیشنهادات کاربران برای غذاهای جدید")
        suggestions_layout = QVBoxLayout()
        self.suggestions_list = QListWidget()
        self.suggestions_list.setAlternatingRowColors(True)
        btn_layout = QHBoxLayout()
        approve_btn = QPushButton("✅ تأیید و افزودن به لیست غذاها")
        approve_btn.clicked.connect(self.approve_suggestion)
        reject_btn = QPushButton("❌ رد پیشنهاد")
        reject_btn.setObjectName("delete_btn")
        reject_btn.clicked.connect(self.reject_suggestion)
        refresh_sugg_btn = QPushButton("🔄 بروزرسانی")
        refresh_sugg_btn.clicked.connect(self.load_pending_suggestions)
        btn_layout.addWidget(approve_btn)
        btn_layout.addWidget(reject_btn)
        btn_layout.addWidget(refresh_sugg_btn)
        suggestions_layout.addWidget(self.suggestions_list)
        suggestions_layout.addLayout(btn_layout)
        suggestions_group.setLayout(suggestions_layout)
        layout.addWidget(suggestions_group)
        self.tab_widget.addTab(tab, "📨 پیشنهادات")
    
    # -------------------- تب تاریخچه --------------------
    def setup_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.today_summary_label = QLabel()
        self.today_summary_label.setStyleSheet("""
            font-size: 14px; 
            padding: 15px; 
            background-color: #e8f5e9; 
            border-radius: 8px;
            border: 1px solid #a5d6a7;
        """)
        layout.addWidget(self.today_summary_label)
        history_group = QGroupBox("📅 تاریخچه مصرف")
        history_layout = QVBoxLayout()
        self.history_list = QListWidget()
        self.history_list.setAlternatingRowColors(True)
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.clicked.connect(self.load_history)
        delete_history_btn = QPushButton("❌ حذف مورد انتخاب شده")
        delete_history_btn.setObjectName("delete_btn")
        delete_history_btn.clicked.connect(self.delete_history_entry)
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(delete_history_btn)
        history_layout.addWidget(self.history_list)
        history_layout.addLayout(button_layout)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        self.tab_widget.addTab(tab, "📅 تاریخچه")
    
    # -------------------- تب راهنما --------------------
    def setup_help_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2 style="color:#2c3e50;">📘 راهنمای استفاده از سیستم تغذیه دانشجویی</h2>
        <p>این سیستم به شما کمک می‌کند تا با توجه به بودجه و سلیقه، غذاهای مناسب را انتخاب کنید.</p>
        <ul>
            <li><b>مدیریت غذاها:</b> می‌توانید لیست غذاها را جستجو و مشاهده کنید.</li>
            <li><b>پیشنهاد هوشمند:</b> با وارد کردن بودجه روزانه، سیستم بر اساس خوشه‌بندی هوشمند، بهترین گزینه‌ها را پیشنهاد می‌دهد.</li>
            <li><b>ثبت مصرف:</b> پس از انتخاب غذا، می‌توانید مصرف آن را ثبت کنید تا بودجه شما به‌روز شود.</li>
            <li><b>امتیازدهی:</b> به غذاهای مصرف‌شده امتیاز دهید تا پیشنهادات بعدی دقیق‌تر شوند.</li>
            <li><b>پیشنهاد غذای جدید:</b> اگر غذای مورد نظر شما در لیست نیست، می‌توانید آن را پیشنهاد دهید. پس از تأیید مدیر، به لیست اضافه می‌شود.</li>
        </ul>
        <h3 style="color:#2c3e50;">📞 ارتباط با مدیران و ادمین‌ها</h3>
        <p><b>0910 348 1754</b> - Morteza Motahar</p>
        <p><b>0901 939 1609</b> - Amirali Keshavarzi</p>
        <p> Id :<b>@BlackHole</b></p>
        <p> Id :<b>@AmirAli_keshavarzi</b></p>
        <h3 style="color:#2c3e50;">📢 کانال‌های اطلاع‌رسانی</h3>
        <p> https://t.me/Jupyter_Morteza</p>
        <p> https://t.me/BlackHole_Team</p>
        <h3 style="color:#2c3e50;"> مخزن ها </h3>
        <p> https://github.com/MortezaMotahar</p>
        """)
        layout.addWidget(help_text)
        self.tab_widget.addTab(tab, "📖 راهنما")
    
    # -------------------- توابع عملیاتی --------------------
    def load_foods_table(self):
        search_term = self.search_edit.text().strip() if hasattr(self, 'search_edit') else ""
        category = self.category_filter.currentText() if hasattr(self, 'category_filter') else "همه"
        foods_data = self.db.search_foods(search_term, category)
        self.foods = [Food.from_dict(f) for f in foods_data]
        self.foods_table.setRowCount(len(self.foods))
        for row, food in enumerate(self.foods):
            self.foods_table.setItem(row, 0, QTableWidgetItem(str(food.id)))
            self.foods_table.setItem(row, 1, QTableWidgetItem(food.name))
            self.foods_table.setItem(row, 2, QTableWidgetItem(food.category))
            self.foods_table.setItem(row, 3, QTableWidgetItem(food.food_type))
            self.foods_table.setItem(row, 4, QTableWidgetItem(f"{food.cost:,.0f}"))
            self.foods_table.setItem(row, 5, QTableWidgetItem(str(food.calories)))
            rating_item = QTableWidgetItem(f"{food.avg_rating:.1f} ⭐" if food.avg_rating > 0 else "-")
            if food.avg_rating >= 4:
                rating_item.setForeground(QColor("green"))
            elif food.avg_rating >= 2.5:
                rating_item.setForeground(QColor("orange"))
            self.foods_table.setItem(row, 6, rating_item)
    
    def filter_foods_table(self):
        self.load_foods_table()
    
    def add_food(self):
        if self.user_role != 'admin':
            return
        dialog = FoodDialog(parent=self)
        if dialog.exec():
            name, ingredients, cost, calories, category, food_type = dialog.get_food_data()
            if name:
                if self.db.add_food(name, ingredients, cost, calories, category, food_type):
                    self.refresh_all()
                    QMessageBox.information(self, "موفقیت", f"غذای '{name}' با موفقیت اضافه شد.")
                else:
                    QMessageBox.warning(self, "خطا", "غذایی با این نام قبلاً ثبت شده است.")
    
    def edit_food(self):
        if self.user_role != 'admin':
            return
        current_row = self.foods_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "اخطار", "لطفاً یک غذا را انتخاب کنید.")
            return
        food_id = int(self.foods_table.item(current_row, 0).text())
        food = next((f for f in self.foods if f.id == food_id), None)
        if food:
            dialog = FoodDialog(food, parent=self)
            if dialog.exec():
                name, ingredients, cost, calories, category, food_type = dialog.get_food_data()
                if self.db.update_food(food_id, name, ingredients, cost, calories, category, food_type):
                    self.refresh_all()
                    QMessageBox.information(self, "موفقیت", "غذا با موفقیت ویرایش شد.")
                else:
                    QMessageBox.warning(self, "خطا", "خطا در ویرایش غذا.")
    
    def delete_food(self):
        if self.user_role != 'admin':
            return
        current_row = self.foods_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "اخطار", "لطفاً یک غذا را انتخاب کنید.")
            return
        food_id = int(self.foods_table.item(current_row, 0).text())
        food_name = self.foods_table.item(current_row, 1).text()
        reply = QMessageBox.question(self, "تأیید حذف", 
                                     f"آیا از حذف '{food_name}' اطمینان دارید؟\n"
                                     "با حذف این غذا، تاریخچه مصرف و امتیازات مربوطه نیز حذف خواهند شد.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_food(food_id):
                self.refresh_all()
                QMessageBox.information(self, "موفقیت", f"غذای '{food_name}' حذف شد.")
    
    def rate_food(self):
        current_row = self.foods_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "اخطار", "لطفاً یک غذا را انتخاب کنید.")
            return
        food_id = int(self.foods_table.item(current_row, 0).text())
        food_name = self.foods_table.item(current_row, 1).text()
        dialog = RatingDialog(food_name, parent=self)
        if dialog.exec():
            rating = dialog.get_rating()
            if self.db.rate_food(food_id, rating):
                self.refresh_all()
                QMessageBox.information(self, "موفقیت", f"امتیاز {rating} برای '{food_name}' ثبت شد (میانگین به‌روز شد).")
    
    def suggest_new_food(self):
        dialog = SuggestFoodDialog(parent=self)
        if dialog.exec():
            name, ingredients, cost, calories, category, food_type = dialog.get_suggestion_data()
            if name:
                if self.db.add_suggestion(name, ingredients, cost, calories, category, food_type):
                    QMessageBox.information(self, "موفقیت", "پیشنهاد شما با موفقیت ثبت شد. پس از تأیید مدیر، اضافه خواهد شد.")
                else:
                    QMessageBox.warning(self, "خطا", "این غذا قبلاً در لیست غذاها یا به عنوان پیشنهاد تکراری ثبت شده است.")
    
    def save_budget(self):
        daily = self.daily_budget_spin.value()
        weekly = self.weekly_budget_spin.value()
        if self.db.update_budget(daily, weekly):
            self.budget = {"daily": daily, "weekly": weekly}
            self.update_status_bar()
            QMessageBox.information(self, "موفقیت", "بودجه با موفقیت ذخیره شد.")
    
    def show_recommendations(self):
        pref_text = self.pref_combo.currentText()
        selected_category = self.recommend_category_filter.currentText()
        selected_type = self.recommend_type_filter.currentText()
        
        # فیلتر غذاها بر اساس وعده و نوع
        filtered_foods = self.foods
        if selected_category != "همه":
            filtered_foods = [f for f in filtered_foods if f.category == selected_category]
        if selected_type != "همه":
            filtered_foods = [f for f in filtered_foods if f.food_type == selected_type]
        
        # گزینه تنوع غذایی (بدون امتیاز)
        if pref_text == "تنوع غذایی":
            unrated = [f for f in filtered_foods if f.avg_rating == 0]
            if not unrated:
                type_str = f" و نوع '{selected_type}'" if selected_type != "همه" else ""
                QMessageBox.information(self, "اطلاع", f"هیچ غذای بدون امتیازی در دسته '{selected_category}'{type_str} وجود ندارد.")
                return
            selected = random.sample(unrated, min(5, len(unrated)))
            self.recommend_list.clear()
            for food in selected:
                item_text = f"{food.name} - {food.cost:,.0f} تومان - {food.calories} کالری (بدون امتیاز)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, food.id)
                self.recommend_list.addItem(item)
            return
        
        # غذاهای دارای امتیاز در دسته انتخاب شده
        rated_foods = [f for f in filtered_foods if f.avg_rating > 0]
        if not rated_foods:
            type_str = f" و نوع '{selected_type}'" if selected_type != "همه" else ""
            QMessageBox.warning(self, "اخطار", 
                f"هیچ غذایی با امتیاز در دسته '{selected_category}'{type_str} وجود ندارد.\n"
                "لطفاً ابتدا از گزینه 'تنوع غذایی' استفاده کنید یا به غذاهای این دسته امتیاز دهید.")
            return
        
        spent = self.db.get_today_total_cost()
        remaining = max(0, self.budget['daily'] - spent)
        recommendations = []
        
        if pref_text == "ارزان‌ترین":
            candidates = [f for f in rated_foods if f.cost <= remaining]
            if not candidates:
                candidates = sorted(rated_foods, key=lambda x: x.cost)
            else:
                candidates.sort(key=lambda x: x.cost)
            recommendations = candidates[:5]
        
        elif pref_text == "پرکالری":
            candidates = [f for f in rated_foods if f.cost <= remaining * 1.2]
            if not candidates:
                candidates = rated_foods
            candidates.sort(key=lambda x: x.calories, reverse=True)
            recommendations = candidates[:5]
        
        elif pref_text == "بهترین امتیاز":
            candidates = [f for f in rated_foods if f.cost <= remaining]
            if not candidates:
                candidates = rated_foods
            candidates.sort(key=lambda x: x.avg_rating, reverse=True)
            recommendations = candidates[:5]
        
        elif pref_text == "متعادل":
            if len(rated_foods) >= 3:
                # خوشه‌بندی فقط روی غذاهای فیلتر شده
                temp_recommender = SmartRecommender(rated_foods)
                n_clusters = min(4, len(rated_foods))
                temp_recommender.cluster_foods(n_clusters=n_clusters)
                balanced_label = temp_recommender.get_balanced_cluster_label()
                if balanced_label != -1:
                    candidates = [f for f in rated_foods if f.cluster_label == balanced_label]
                    candidates.sort(key=lambda x: (x.cost > remaining, x.cost))
                    recommendations = candidates[:5]
                else:
                    median_cost = np.median([f.cost for f in rated_foods])
                    median_cal = np.median([f.calories for f in rated_foods])
                    candidates = sorted(rated_foods, key=lambda x: abs(x.cost - median_cost) + abs(x.calories - median_cal))
                    recommendations = candidates[:5]
            else:
                candidates = sorted(rated_foods, key=lambda x: abs(x.cost - remaining))
                recommendations = candidates[:5]
        
        self.recommend_list.clear()
        for food in recommendations:
            stars = "⭐" * int(food.avg_rating) if food.avg_rating > 0 else ""
            item_text = f"{food.name} - {food.cost:,.0f} تومان - {food.calories} کالری {stars}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, food.id)
            if food.cost <= remaining:
                item.setForeground(QColor("green"))
            else:
                item.setForeground(QColor("orange"))
            self.recommend_list.addItem(item)
    
    def consume_selected(self):
        current_item = self.recommend_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "اخطار", "لطفاً یک غذا را انتخاب کنید.")
            return
        food_id = current_item.data(Qt.ItemDataRole.UserRole)
        food = next((f for f in self.foods if f.id == food_id), None)
        if not food:
            return
        spent = self.db.get_today_total_cost()
        remaining = self.budget['daily'] - spent
        if food.cost > remaining:
            QMessageBox.warning(self, "خطا", f"هزینه این غذا ({food.cost:,.0f} تومان) بیشتر از بودجه باقی‌مانده ({remaining:,.0f} تومان) است.\nنمی‌توانید آن را ثبت کنید.")
            return
        if self.db.add_consumption(food_id):
            self.update_status_bar()
            self.load_history()
            QMessageBox.information(self, "موفقیت", "مصرف غذا با موفقیت ثبت شد.")
    
    def rate_selected_food(self):
        current_item = self.recommend_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "اخطار", "لطفاً یک غذا را انتخاب کنید.")
            return
        food_id = current_item.data(Qt.ItemDataRole.UserRole)
        food = next((f for f in self.foods if f.id == food_id), None)
        if food:
            dialog = RatingDialog(food.name, parent=self)
            if dialog.exec():
                rating = dialog.get_rating()
                if self.db.rate_food(food_id, rating):
                    self.refresh_all()
                    self.show_recommendations()
                    QMessageBox.information(self, "موفقیت", "امتیاز با موفقیت ثبت شد (میانگین به‌روز شد).")
    
    def update_cluster_plot(self):
        rated_foods = [f for f in self.foods if f.avg_rating > 0]
        if len(rated_foods) < 2:
            QMessageBox.warning(self, "اخطار", "حداقل ۲ غذای امتیازدار برای خوشه‌بندی نیاز است.")
            return
        self.refresh_recommender()
        if hasattr(self, 'canvas') and self.recommender.labels is not None:
            self.canvas.plot_clusters(self.foods, np.array([f.cluster_label for f in self.foods]))
            stats = self.recommender.get_cluster_stats()
            info_text = "آمار خوشه‌ها (فقط غذاهای دارای امتیاز):\n"
            for label, data in stats.items():
                info_text += f"خوشه {label}: {data['count']} غذا | "
                info_text += f"میانگین هزینه: {data['avg_cost']:.0f} تومان | "
                info_text += f"میانگین کالری: {data['avg_cal']:.0f} | "
                info_text += f"میانگین امتیاز: {data['avg_rating']:.1f}\n"
            self.cluster_info_label.setText(info_text)
        else:
            self.cluster_info_label.setText("امکان خوشه‌بندی وجود ندارد. حداقل ۲ غذای امتیازدار نیاز است.")
    
    def load_history(self):
        today_consumption = self.db.get_today_consumption()
        total_cost = sum(item['cost'] for item in today_consumption)
        total_calories = sum(item['calories'] for item in today_consumption)
        summary = f"📅 امروز: {len(today_consumption)} وعده | "
        summary += f"💰 هزینه: {total_cost:,.0f} تومان | "
        summary += f"🔥 کالری: {total_calories} | "
        summary += f"💵 بودجه روزانه: {self.budget['daily']:,.0f} تومان | "
        remaining = self.budget['daily'] - total_cost
        if remaining >= 0:
            summary += f"✅ باقی‌مانده: {remaining:,.0f} تومان"
        else:
            summary += f"⚠️ اضافه مصرف: {-remaining:,.0f} تومان"
        self.today_summary_label.setText(summary)
        
        history = self.db.get_all_history(100)
        self.history_list.clear()
        for entry in history:
            item_text = f"{entry['consumption_date']} | {entry['name']} | {entry['cost']:,.0f} تومان | {entry['calories']} کالری"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, entry['id'])
            self.history_list.addItem(item)
    
    def delete_history_entry(self):
        current_item = self.history_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "اخطار", "لطفاً یک مورد را انتخاب کنید.")
            return
        history_id = current_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "تأیید حذف", "آیا از حذف این مورد اطمینان دارید؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_history_entry(history_id):
                self.update_status_bar()
                self.load_history()
                QMessageBox.information(self, "موفقیت", "مورد با موفقیت حذف شد.")
    
    def update_stats_display(self):
        stats = self.db.get_food_stats()
        budget = self.db.get_budget()
        text = "📊 آمار کلی سیستم\n"
        text += "=" * 40 + "\n\n"
        text += f"📋 تعداد کل غذاها: {stats['total_foods']}\n"
        text += f"🍽️ تعداد کل وعده‌های ثبت شده: {stats['total_consumptions']}\n"
        text += f"💰 میانگین هزینه غذاها: {stats['avg_cost']:,.0f} تومان\n\n"
        text += f"💵 بودجه روزانه: {budget['daily']:,.0f} تومان\n"
        text += f"💶 بودجه هفتگی: {budget['weekly']:,.0f} تومان\n\n"
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.name, COUNT(*) as count, AVG(r.rating) as avg_rating
            FROM consumption_history h
            JOIN foods f ON h.food_id = f.id
            LEFT JOIN food_ratings r ON f.id = r.food_id
            GROUP BY f.id
            ORDER BY count DESC
            LIMIT 5
        ''')
        text += "🏆 پرمصرف‌ترین غذاها:\n"
        for row in cursor.fetchall():
            rating = f" (امتیاز: {row[2]:.1f})" if row[2] else ""
            text += f"  • {row[0]}: {row[1]} بار{rating}\n"
        conn.close()
        self.stats_text.setText(text)
    
    def load_pending_suggestions(self):
        if self.user_role != 'admin':
            return
        suggestions = self.db.get_pending_suggestions()
        self.suggestions_list.clear()
        for sugg in suggestions:
            item_text = f"{sugg['name']} | {sugg['category']} | {sugg['cost']:,.0f} تومان | {sugg['calories']} کالری | (ارسال‌کننده: {sugg['submitted_by']})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, sugg['id'])
            self.suggestions_list.addItem(item)
    
    def approve_suggestion(self):
        current_item = self.suggestions_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "اخطار", "لطفاً یک پیشنهاد را انتخاب کنید.")
            return
        sugg_id = current_item.data(Qt.ItemDataRole.UserRole)
        if self.db.approve_suggestion(sugg_id):
            self.refresh_all()
            self.load_pending_suggestions()
            QMessageBox.information(self, "موفقیت", "پیشنهاد تأیید و به لیست غذاها اضافه شد.")
        else:
            QMessageBox.warning(self, "خطا", "خطا در تأیید پیشنهاد. احتمالاً غذا تکراری است.")
    
    def reject_suggestion(self):
        current_item = self.suggestions_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "اخطار", "لطفاً یک پیشنهاد را انتخاب کنید.")
            return
        sugg_id = current_item.data(Qt.ItemDataRole.UserRole)
        if self.db.reject_suggestion(sugg_id):
            self.load_pending_suggestions()
            QMessageBox.information(self, "موفقیت", "پیشنهاد رد شد.")
    
    def update_status_bar(self):
        spent = self.db.get_today_total_cost()
        remaining = self.budget['daily'] - spent
        color = "green" if remaining >= 0 else "red"
        status_text = f"💰 بودجه روزانه: {self.budget['daily']:,.0f} تومان | "
        status_text += f"هزینه امروز: {spent:,.0f} تومان | "
        status_text += f"باقی‌مانده: {remaining:,.0f} تومان"
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        stats = self.db.get_food_stats()
        self.stats_label.setText(f"📊 {stats['total_foods']} غذا | {stats['total_consumptions']} وعده ثبت شده")

# -------------------------------
# ایجاد داده‌های نمونه اولیه
# -------------------------------
def create_sample_data():
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM foods")
    count = cursor.fetchone()[0]
    conn.close()
    if count == 0:
        sample_foods = [
            ("عدسی", "عدس\nپیاز\nسیب زمینی\nادویه", 35000, 250, "صبحانه", "گیاهی"),
            ("املت", "تخم مرغ\nگوجه\nروغن", 45000, 300, "صبحانه", "گوشتی"),
            ("ماکارونی ساده", "ماکارونی\nرب\nپیاز\nروغن", 55000, 450, "ناهار", "گیاهی"),
            ("عدس پلو", "برنج\nعدس\nکشمش\nپیاز داغ", 75000, 600, "ناهار", "گیاهی"),
            ("قیمه", "گوشت\nلپه\nرب\nسیب زمینی", 120000, 800, "ناهار", "گوشتی"),
            ("کوکو سیب زمینی", "سیب زمینی\nتخم مرغ\nآرد\nادویه", 40000, 350, "شام", "گیاهی"),
            ("ساندویچ تخم مرغ", "نان باگت\nتخم مرغ\nگوجه\nکاهو", 35000, 280, "شام", "گوشتی"),
            ("سالاد فصل", "کاهو\nگوجه\nخیار\nکلم\nهویج", 30000, 100, "میان‌وعده", "گیاهی"),
            ("اسموتی موز", "موز\nشیر\nعسل\nیخ", 40000, 200, "میان‌وعده", "گیاهی"),
            ("خوراک لوبیا", "لوبیا چیتی\nپیاز\nرب\nادویه", 50000, 400, "ناهار", "گیاهی"),
        ]
        for name, ingredients, cost, calories, category, food_type in sample_foods:
            ingredients_list = [i.strip() for i in ingredients.split('\n') if i.strip()]
            db.add_food(name, ingredients_list, cost, calories, category, food_type)
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM foods LIMIT 5")
        food_ids = [row[0] for row in cursor.fetchall()]
        for food_id in food_ids:
            rating = random.randint(3, 5)
            cursor.execute("INSERT INTO food_ratings (food_id, rating) VALUES (?, ?)", (food_id, rating))
        conn.commit()
        conn.close()

# -------------------------------
# اجرای برنامه
# -------------------------------
if __name__ == "__main__":
    create_sample_data()
    db = DatabaseManager()
    app = QApplication(sys.argv)
    font = QFont("Tahoma", 9)
    app.setFont(font)
    window = MainWindow(db)
    window.show()
    sys.exit(app.exec())