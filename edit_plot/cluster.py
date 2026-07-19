import sys
import sqlite3
import numpy as np
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import webbrowser
import os

DB_FILE = "food_planner.db"

def load_foods_from_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.id, f.name, f.cost, f.calories, f.category,
               COALESCE(CAST(r.total_rating AS REAL) / NULLIF(r.rating_count, 0), 0) as avg_rating
        FROM foods f
        LEFT JOIN food_ratings r ON f.id = r.food_id
        ORDER BY f.id
    ''')
    foods = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return foods

def cluster_foods(foods, n_clusters=4):
    if len(foods) < n_clusters:
        n_clusters = max(2, len(foods))
    X = np.array([[f['cost'], f['calories'], f['avg_rating'] * 10000] for f in foods])
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(X_scaled)
    return labels

def create_3d_plot(foods, labels):
    valid_symbols = ['circle', 'circle-open', 'cross', 'diamond', 
                     'diamond-open', 'square', 'square-open', 'x']
    colors = [
        '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', 
        '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', 
        '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', 
        '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080'
    ]

    unique_labels = np.unique(labels)
    traces = []
    for i, label in enumerate(unique_labels):
        idx = np.where(labels == label)
        cluster_foods = [foods[j] for j in idx[0]]
        x_vals = [f['cost'] for f in cluster_foods]
        y_vals = [f['calories'] for f in cluster_foods]
        z_vals = [f['avg_rating'] for f in cluster_foods]
        
        # انتخاب شکل با گردش در لیست مجاز
        symbol = valid_symbols[i % len(valid_symbols)]
        color = colors[i % len(colors)]
        
        trace = go.Scatter3d(
            x=x_vals, y=y_vals, z=z_vals,
            mode='markers',
            marker=dict(
                size=8,
                symbol=symbol,
                color=color,
                line=dict(width=1, color='black'),
                opacity=0.85
            ),
            name=f'خوشه {label}'
        )
        traces.append(trace)

    all_costs = [f['cost'] for f in foods]
    all_cals = [f['calories'] for f in foods]
    x_min, x_max = min(all_costs), max(all_costs)
    y_min, y_max = min(all_cals), max(all_cals)
    x_range = x_max - x_min if x_max != x_min else 1
    y_range = y_max - y_min if y_max != y_min else 1

    layout = go.Layout(
        title=dict(text='نمودار خوشه‌بندی سه‌بعدی غذاها', font=dict(size=16)),
        scene=dict(
            xaxis=dict(title=dict(text='هزینه (تومان)', font=dict(size=12)),
                       range=[x_min - 0.15*x_range, x_max + 0.15*x_range]),
            yaxis=dict(title=dict(text='کالری', font=dict(size=12)),
                       range=[y_min - 0.15*y_range, y_max + 0.15*y_range]),
            zaxis=dict(title=dict(text='امتیاز (۰-۵)', font=dict(size=12)), range=[0, 5]),
            bgcolor='#f8f9fa'
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        legend=dict(x=0.8, y=0.9, font=dict(size=10))
    )
    fig = go.Figure(data=traces, layout=layout)
    return fig

def main():
    foods = load_foods_from_db()
    if len(foods) < 2:
        print("تعداد غذاها برای خوشه‌بندی کافی نیست (حداقل ۲ غذا نیاز است).")
        return

    try:
        n_clusters = int(input("تعداد خوشه‌های مورد نظر (پیش‌فرض ۴): ") or 4)
        n_clusters = max(2, min(20, n_clusters)) 
    except:
        n_clusters = 4

    labels = cluster_foods(foods, n_clusters)
    fig = create_3d_plot(foods, labels)
    html_file = "cluster_plot.html"
    fig.write_html(html_file)
    webbrowser.open(f"file://{os.path.abspath(html_file)}")
    print(f"نمودار با {n_clusters} خوشه در فایل {html_file} ذخیره و در مرورگر باز شد.")

if __name__ == "__main__":
    main()