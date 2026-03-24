import sqlite3
from pathlib import Path


# Путь к базе данных
DB_PATH = Path(__file__).parent.parent / "database" / "obuv.db"
DB_PATH.parent.mkdir(exist_ok=True)


# Подключение к БД (создастся автоматически)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# Включаем поддержку внешних ключей
cursor.execute("PRAGMA foreign_keys = ON;")


# 1. Таблица пользователей
cursor.execute("""
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    login TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'client'))
);
""")


# 2. Таблица категорий
cursor.execute("""
CREATE TABLE IF NOT EXISTS Categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL
);
""")


# 3. Таблица поставщиков
cursor.execute("""
CREATE TABLE IF NOT EXISTS Suppliers (
    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT UNIQUE NOT NULL
);
""")


# 4. Таблица производителей
cursor.execute("""
CREATE TABLE IF NOT EXISTS Manufacturers (
    manufacturer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer_name TEXT UNIQUE NOT NULL
);
""")


# 5. Таблица товаров
cursor.execute("""
CREATE TABLE IF NOT EXISTS Products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    article TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    price REAL NOT NULL CHECK(price >= 0),
    supplier_id INTEGER,
    manufacturer_id INTEGER,
    category_id INTEGER,
    discount INTEGER DEFAULT 0 CHECK(discount >= 0 AND discount <= 100),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK(stock_quantity >= 0),
    description TEXT,
    image_path TEXT,
    FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (manufacturer_id) REFERENCES Manufacturers(manufacturer_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON UPDATE CASCADE ON DELETE RESTRICT
);
""")


# 6. Таблица пунктов выдачи
cursor.execute("""
CREATE TABLE IF NOT EXISTS PickupPoints (
    point_id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT NOT NULL
);
""")


# 7. Таблица заказов (ДОБАВЛЕНО ПОЛЕ status)
cursor.execute("""
CREATE TABLE IF NOT EXISTS Orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_date DATE NOT NULL,
    delivery_date DATE,
    pickup_point_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    pickup_code INTEGER NOT NULL,
    status TEXT DEFAULT 'В обработке',
    FOREIGN KEY (pickup_point_id) REFERENCES PickupPoints(point_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (client_id) REFERENCES Users(user_id) ON UPDATE CASCADE ON DELETE RESTRICT
);
""")


# 8. Таблица позиций заказа (связь заказ-товар)
cursor.execute("""
CREATE TABLE IF NOT EXISTS OrderItems (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Products(product_id) ON UPDATE CASCADE ON DELETE RESTRICT
);
""")


# Сохраняем изменения
conn.commit()
conn.close()


print("✅ База данных успешно создана:", DB_PATH)
