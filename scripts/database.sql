-- Создание базы данных для ООО "Обувь"

PRAGMA foreign_keys = ON;


-- Таблица пользователей
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    login TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'client'))
);


-- Таблица категорий
CREATE TABLE IF NOT EXISTS Categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL
);


-- Таблица поставщиков
CREATE TABLE IF NOT EXISTS Suppliers (
    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT UNIQUE NOT NULL
);


-- Таблица производителей
CREATE TABLE IF NOT EXISTS Manufacturers (
    manufacturer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer_name TEXT UNIQUE NOT NULL
);


-- Таблица товаров
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


-- Таблица пунктов выдачи
CREATE TABLE IF NOT EXISTS PickupPoints (
    point_id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT NOT NULL
);


-- Таблица заказов (ДОБАВЛЕНО: status, delivery_date необязательное)
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


-- Таблица позиций заказа
CREATE TABLE IF NOT EXISTS OrderItems (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Products(product_id) ON UPDATE CASCADE ON DELETE RESTRICT
);


-- Индексы для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_products_article ON Products(article);
CREATE INDEX IF NOT EXISTS idx_products_category ON Products(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_client ON Orders(client_id);
CREATE INDEX IF NOT EXISTS idx_orders_pickup ON Orders(pickup_point_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON OrderItems(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON OrderItems(product_id);
