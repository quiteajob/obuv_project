import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "obuv.db"
DATA_PATH = Path(__file__).parent.parent / "data_import"

# Подключение к БД
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

# ========== 1. Импорт пользователей ==========
df_users = pd.read_excel(DATA_PATH / "user_import.xlsx")
for _, row in df_users.iterrows():
    role_map = {
        "Администратор": "admin",
        "Менеджер": "manager",
        "Авторизованный клиент": "client"
    }
    role = role_map.get(row["Роль сотрудника"], "client")
    cursor.execute(
        "INSERT OR IGNORE INTO Users (full_name, login, password, role) VALUES (?, ?, ?, ?)",
        (row["ФИО"], row["Логин"], row["Пароль"], role)
    )

# ========== 2. Импорт справочников (извлечём из товаров) ==========
df_tovar = pd.read_excel(DATA_PATH / "Tovar.xlsx")

# Категории
for cat in df_tovar["Категория товара"].unique():
    cursor.execute("INSERT OR IGNORE INTO Categories (category_name) VALUES (?)", (cat,))

# Поставщики
for sup in df_tovar["Поставщик"].unique():
    cursor.execute("INSERT OR IGNORE INTO Suppliers (supplier_name) VALUES (?)", (sup,))

# Производители
for mfr in df_tovar["Производитель"].unique():
    cursor.execute("INSERT OR IGNORE INTO Manufacturers (manufacturer_name) VALUES (?)", (mfr,))

# ========== 3. Импорт пунктов выдачи ==========
df_points = pd.read_excel(DATA_PATH / "Punkty_vydachi_import.xlsx", header=None)
for addr in df_points[0].tolist():
    cursor.execute("INSERT OR IGNORE INTO PickupPoints (address) VALUES (?)", (addr,))

conn.commit()

# ========== 4. Вспомогательная функция для получения ID ==========
def get_id(table, id_col, name_col, value):
    """Получить ID из справочника или создать новую запись"""
    cursor.execute(f"SELECT {id_col} FROM {table} WHERE {name_col} = ?", (value,))
    result = cursor.fetchone()
    if result is None:
        cursor.execute(f"INSERT INTO {table} ({name_col}) VALUES (?)", (value,))
        conn.commit()
        return cursor.lastrowid
    return result[0]

# ========== 5. Импорт товаров ==========
for _, row in df_tovar.iterrows():
    supplier_id = get_id("Suppliers", "supplier_id", "supplier_name", row["Поставщик"])
    manufacturer_id = get_id("Manufacturers", "manufacturer_id", "manufacturer_name", row["Производитель"])
    category_id = get_id("Categories", "category_id", "category_name", row["Категория товара"])
    
    # Обработка пути к изображению
    if pd.notna(row["Фото"]) and row["Фото"] != "":
        image_path = f"resources/{row['Фото']}"
    else:
        image_path = "resources/picture.png"
    
    cursor.execute("""
        INSERT INTO Products (article, name, unit, price, supplier_id, manufacturer_id, 
                              category_id, discount, stock_quantity, description, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row["Артикул"], row["Наименование товара"], row["Единица измерения"],
        float(row["Цена"]), supplier_id, manufacturer_id, category_id,
        int(row["Действующая скидка"]), int(row["Кол-во на складе"]),
        row["Описание товара"], image_path
    ))


# ========== 6. Импорт заказов ==========
df_orders = pd.read_excel(DATA_PATH / "Zakaz_import.xlsx")

# Функция для получения client_id по ФИО
def get_client_id(full_name):
    cursor.execute("SELECT user_id FROM Users WHERE full_name = ?", (full_name,))
    res = cursor.fetchone()
    return res[0] if res else 1  # если не найден — берём первого пользователя

for _, row in df_orders.iterrows():
    # Преобразуем даты в строки формата YYYY-MM-DD
    order_date = row["Дата заказа"]
    delivery_date = row["Дата доставки"]
    
    # Если это Timestamp — конвертируем в строку
    if hasattr(order_date, 'strftime'):
        order_date = order_date.strftime('%Y-%m-%d')
    if hasattr(delivery_date, 'strftime'):
        delivery_date = delivery_date.strftime('%Y-%m-%d')
    
    # pickup_point_id: в задании номер адреса (1, 2, 3...), но у нас ID начинается с 1
    pickup_point_id = int(row["Адрес пункта выдачи"])
    
    # Статус заказа: если дата доставки есть и прошла — "Готов к выдаче", иначе "В обработке"
    status = "В обработке"
    if delivery_date:
        from datetime import date
        try:
            delivery = pd.to_datetime(delivery_date).date()
            if delivery <= date.today():
                status = "Готов к выдаче"
            else:
                status = "В пути"
        except:
            status = "В обработке"
    
    cursor.execute("""
        INSERT INTO Orders (order_date, delivery_date, pickup_point_id, client_id, pickup_code, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        order_date, delivery_date,
        pickup_point_id, get_client_id(row["ФИО авторизированного клиента"]),
        int(row["Код для получения"]), status
    ))
    
    order_id = cursor.lastrowid
    
    # Разбираем строку "А112Т4, 2, F635R4, 2" → [(article, qty), ...]
    items_str = str(row["Артикул заказа"])
    items = items_str.split(", ")
    for i in range(0, len(items), 2):
        article = items[i]
        qty = int(items[i+1])
        
        cursor.execute("SELECT product_id FROM Products WHERE article = ?", (article,))
        product_res = cursor.fetchone()
        if product_res:
            product_id = product_res[0]
            cursor.execute("""
                INSERT INTO OrderItems (order_id, product_id, quantity)
                VALUES (?, ?, ?)
            """, (order_id, product_id, qty))

conn.commit()
conn.close()

print("✅ Данные успешно импортированы из .xlsx файлов!")
