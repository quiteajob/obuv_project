import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "obuv.db"

def get_connection():
    """Получить подключение к БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    return conn

def check_login(login, password):
    """Проверить учётные данные"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, full_name, role, login, password
        FROM Users
        WHERE login = ? AND password = ?
    """, (login, password))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "user_id": result["user_id"],
            "full_name": result["full_name"],
            "role": result["role"]
        }
    return None

def get_all_products():
    """Получить все товары с названиями поставщиков, производителей, категорий"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.product_id,
            p.article,
            p.name,
            p.unit,
            p.price,
            s.supplier_name as supplier,
            m.manufacturer_name as manufacturer,
            c.category_name as category,
            p.discount,
            p.stock_quantity,
            p.description,
            p.image_path
        FROM Products p
        LEFT JOIN Suppliers s ON p.supplier_id = s.supplier_id
        LEFT JOIN Manufacturers m ON p.manufacturer_id = m.manufacturer_id
        LEFT JOIN Categories c ON p.category_id = c.category_id
        ORDER BY p.product_id ASC
    """)
    
    result = cursor.fetchall()
    conn.close()
    
    return [tuple(row) for row in result]

def get_product_by_id(product_id):
    """Получить товар по ID с названиями справочников"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            p.product_id,
            p.article,
            p.name,
            p.unit,
            p.price,
            s.supplier_name as supplier,
            m.manufacturer_name as manufacturer,
            c.category_name as category,
            p.discount,
            p.stock_quantity,
            p.description,
            p.image_path
        FROM Products p
        LEFT JOIN Suppliers s ON p.supplier_id = s.supplier_id
        LEFT JOIN Manufacturers m ON p.manufacturer_id = m.manufacturer_id
        LEFT JOIN Categories c ON p.category_id = c.category_id
        WHERE p.product_id = ?
    """, (product_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        data = tuple(result)
        print(f"✅ Товар #{product_id} найден: {data[2]}")
        return data
    else:
        print(f"❌ Товар #{product_id} НЕ найден")
        return None


def get_unique_suppliers():
    """Получить список уникальных поставщиков"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT supplier_name 
        FROM Suppliers 
        ORDER BY supplier_name
    """)
    
    result = cursor.fetchall()
    conn.close()
    
    return [row["supplier_name"] for row in result]

def get_unique_categories():
    """Получить список уникальных категорий"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT category_name 
        FROM Categories 
        ORDER BY category_name
    """)
    
    result = cursor.fetchall()
    conn.close()
    
    return [row["category_name"] for row in result]

def get_unique_manufacturers():
    """Получить список уникальных производителей"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT manufacturer_name 
        FROM Manufacturers 
        ORDER BY manufacturer_name
    """)
    
    result = cursor.fetchall()
    conn.close()
    
    return [row["manufacturer_name"] for row in result]

def get_supplier_id_by_name(supplier_name):
    """Получить ID поставщика по названию"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT supplier_id FROM Suppliers WHERE supplier_name = ?
    """, (supplier_name,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result["supplier_id"] if result else None

def get_category_id_by_name(category_name):
    """Получить ID категории по названию"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT category_id FROM Categories WHERE category_name = ?
    """, (category_name,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result["category_id"] if result else None

def get_manufacturer_id_by_name(manufacturer_name):
    """Получить ID производителя по названию"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT manufacturer_id FROM Manufacturers WHERE manufacturer_name = ?
    """, (manufacturer_name,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result["manufacturer_id"] if result else None

def add_supplier_if_not_exists(supplier_name):
    """Добавить поставщика, если не существует"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO Suppliers (supplier_name) VALUES (?)
    """, (supplier_name,))
    
    conn.commit()
    conn.close()

def add_category_if_not_exists(category_name):
    """Добавить категорию, если не существует"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO Categories (category_name) VALUES (?)
    """, (category_name,))
    
    conn.commit()
    conn.close()

def add_manufacturer_if_not_exists(manufacturer_name):
    """Добавить производителя, если не существует"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO Manufacturers (manufacturer_name) VALUES (?)
    """, (manufacturer_name,))
    
    conn.commit()
    conn.close()

def search_products(search_text, supplier_filter=None, sort_by=None, sort_order='asc'):
    """Поиск товаров по всем текстовым полям + фильтрация + сортировка"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            p.product_id,
            p.article,
            p.name,
            p.unit,
            p.price,
            s.supplier_name as supplier,
            m.manufacturer_name as manufacturer,
            c.category_name as category,
            p.discount,
            p.stock_quantity,
            p.description,
            p.image_path
        FROM Products p
        LEFT JOIN Suppliers s ON p.supplier_id = s.supplier_id
        LEFT JOIN Manufacturers m ON p.manufacturer_id = m.manufacturer_id
        LEFT JOIN Categories c ON p.category_id = c.category_id
        WHERE 1=1
    """
    
    params = []
    
    if search_text and search_text.strip():
        search_pattern = f"%{search_text.strip()}%"
        query += """
            AND (
                p.article LIKE ? OR
                p.name LIKE ? OR
                c.category_name LIKE ? OR
                m.manufacturer_name LIKE ? OR
                s.supplier_name LIKE ? OR
                p.description LIKE ? OR
                p.unit LIKE ?
            )
        """
        params.extend([search_pattern] * 7)
    
    if supplier_filter and supplier_filter != "Все поставщики":
        query += " AND s.supplier_name = ?"
        params.append(supplier_filter)
    
    if sort_by == 'stock_quantity':
        order_dir = "DESC" if sort_order == 'desc' else "ASC"
        query += f" ORDER BY p.stock_quantity {order_dir}"
    else:
        query += " ORDER BY p.product_id ASC"
    
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    
    return [tuple(row) for row in result]


def delete_product(product_id):
    """Удалить товар (если нет в заказах)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM OrderItems WHERE product_id = ?
    """, (product_id,))
    
    count = cursor.fetchone()[0]
    
    if count > 0:
        conn.close()
        return False, "Товар присутствует в заказе и не может быть удалён!"
    
    cursor.execute("DELETE FROM Products WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()
    
    return True, "Товар успешно удалён!"

def get_next_product_id():
    """Получить следующий ID для нового товара"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(product_id) FROM Products")
    result = cursor.fetchone()[0]
    conn.close()
    
    return (result or 0) + 1

def add_product(data):
    """Добавить новый товар"""
    conn = get_connection()
    cursor = conn.cursor()
    
    add_supplier_if_not_exists(data["supplier"])
    add_category_if_not_exists(data["category"])
    add_manufacturer_if_not_exists(data["manufacturer"])
    
    supplier_id = get_supplier_id_by_name(data["supplier"])
    category_id = get_category_id_by_name(data["category"])
    manufacturer_id = get_manufacturer_id_by_name(data["manufacturer"])
    
    query = """
    INSERT INTO Products (
        article, name, unit, price, supplier_id, manufacturer_id,
        category_id, discount, stock_quantity, description, image_path
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor.execute(query, (
        data["article"],
        data["name"],
        data["unit"],
        data["price"],
        supplier_id,
        manufacturer_id,
        category_id,
        data["discount"],
        data["stock_quantity"],
        data["description"],
        data.get("image_path", "")
    ))
    
    conn.commit()
    conn.close()

def update_product(product_id, data):
    """Обновить данные товара"""
    conn = get_connection()
    cursor = conn.cursor()
    
    add_supplier_if_not_exists(data["supplier"])
    add_category_if_not_exists(data["category"])
    add_manufacturer_if_not_exists(data["manufacturer"])
    
    supplier_id = get_supplier_id_by_name(data["supplier"])
    category_id = get_category_id_by_name(data["category"])
    manufacturer_id = get_manufacturer_id_by_name(data["manufacturer"])
    
    query = """
    UPDATE Products SET
        article = ?, name = ?, unit = ?, price = ?, supplier_id = ?,
        manufacturer_id = ?, category_id = ?, discount = ?, stock_quantity = ?,
        description = ?, image_path = ?
    WHERE product_id = ?
    """
    
    cursor.execute(query, (
        data["article"], data["name"], data["unit"], data["price"],
        supplier_id, manufacturer_id, category_id,
        data["discount"], data["stock_quantity"], data["description"],
        data.get("image_path", ""), product_id
    ))
    
    conn.commit()
    conn.close()

def get_pickup_points():
    """Получить все пункты выдачи"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT point_id, address FROM PickupPoints ORDER BY address")
    result = cursor.fetchall()
    conn.close()
    
    return [(row["point_id"], row["address"]) for row in result]


# ============================================================================
# === УПРАВЛЕНИЕ ЗАКАЗАМИ (Orders + OrderItems + PickupPoints) ===
# ============================================================================

def _build_order_article(order_id):
    """
    Построить строку артикулов заказа в формате:
    "А112Т4 (2), F635R4 (1), B500X2 (3)"
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.article, oi.quantity
        FROM OrderItems oi
        JOIN Products p ON oi.product_id = p.product_id
        WHERE oi.order_id = ?
        ORDER BY p.article
    """, (order_id,))
    
    items = cursor.fetchall()
    conn.close()
    
    if not items:
        return "Нет товаров"
    
    parts = [f"{row[0]} ({row[1]})" for row in items]
    return ", ".join(parts)

def get_all_orders():
    """
    Получить все заказы:
    order_id, article (список артикул с количеством), status, pickup_address, order_date, delivery_date
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            o.order_id,
            o.order_date,
            o.delivery_date,
            o.status,
            pp.address as pickup_address
        FROM Orders o
        LEFT JOIN PickupPoints pp ON o.pickup_point_id = pp.point_id
        ORDER BY o.order_date DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    # Формируем результат с артикулами
    result = []
    for row in rows:
        order_id = row["order_id"]
        article_str = _build_order_article(order_id)
        status = row["status"] or "В обработке"
        result.append((
            order_id,
            article_str,
            status,
            row["pickup_address"] or "Не указан",
            row["order_date"],
            row["delivery_date"]
        ))
    
    return result

def get_order_by_id(order_id):
    """Получить заказ по ID с полной информацией"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            o.order_id,
            o.order_date,
            o.delivery_date,
            o.status,
            pp.address as pickup_address
        FROM Orders o
        LEFT JOIN PickupPoints pp ON o.pickup_point_id = pp.point_id
        WHERE o.order_id = ?
    """, (order_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    article_str = _build_order_article(order_id)
    status = row["status"] or "В обработке"
    
    return (
        row["order_id"],
        article_str,
        status,
        row["pickup_address"] or "Не указан",
        row["order_date"],
        row["delivery_date"]
    )

def get_all_product_articles():
    """Получить список всех артикулов товаров в формате: 'А112Т4 — Кроссовки Nike'"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT article, name 
        FROM Products 
        ORDER BY article
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [f"{row['article']} — {row['name']}" for row in rows]

def get_article_by_display(display_text):
    """Получить чистый артикул из отображаемого текста 'А112Т4 — Кроссовки Nike' → 'А112Т4'"""
    if not display_text:
        return None
    return display_text.split(" — ")[0].strip()


def get_order_details(order_id):
    """
    Получить полную информацию о заказе для редактирования.
    Возвращает: (order_id, order_date, delivery_date, status, pickup_point_id, pickup_address, items)
    где items = [(article, quantity), ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            o.order_id,
            o.order_date,
            o.delivery_date,
            o.status,
            o.pickup_point_id,
            pp.address as pickup_address
        FROM Orders o
        LEFT JOIN PickupPoints pp ON o.pickup_point_id = pp.point_id
        WHERE o.order_id = ?
    """, (order_id,))
    
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    # Получаем товары заказа
    cursor.execute("""
        SELECT p.article, oi.quantity
        FROM OrderItems oi
        JOIN Products p ON oi.product_id = p.product_id
        WHERE oi.order_id = ?
    """, (order_id,))
    
    items = [(r["article"], r["quantity"]) for r in cursor.fetchall()]
    conn.close()
    
    return (
        row["order_id"],
        row["order_date"],
        row["delivery_date"],
        row["status"] or "В обработке",
        row["pickup_point_id"],
        row["pickup_address"],
        items
    )

def add_order(data):
    """
    Добавить новый заказ
    data: dict с ключами:
        - items: [(article, quantity), ...]
        - status: str
        - pickup_point_id: int
        - order_date: str
        - delivery_date: str or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем товары и собираем product_id
    product_items = []
    for article, quantity in data["items"]:
        cursor.execute("SELECT product_id FROM Products WHERE article = ?", (article,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            raise ValueError(f"Товар с артикулом '{article}' не найден!")
        product_items.append((result["product_id"], quantity))
    
    # Проверяем пункт выдачи
    cursor.execute("SELECT point_id FROM PickupPoints WHERE point_id = ?", (data["pickup_point_id"],))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Пункт выдачи не найден!")
    
    # Получаем ID клиента (первый пользователь с ролью client)
    cursor.execute("SELECT user_id FROM Users WHERE role = 'client' LIMIT 1")
    client_result = cursor.fetchone()
    client_id = client_result[0] if client_result else 1
    
    # Генерируем код выдачи
    import random
    pickup_code = random.randint(100000, 999999)
    
    # Создаём заказ
    cursor.execute("""
        INSERT INTO Orders (order_date, delivery_date, pickup_point_id, client_id, pickup_code, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["order_date"],
        data["delivery_date"] or None,
        data["pickup_point_id"],
        client_id,
        pickup_code,
        data["status"]
    ))
    
    order_id = cursor.lastrowid
    
    # Добавляем позиции заказа
    for product_id, quantity in product_items:
        cursor.execute("""
            INSERT INTO OrderItems (order_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (order_id, product_id, quantity))
    
    conn.commit()
    conn.close()
    
    return order_id

def update_order(order_id, data):
    """
    Обновить существующий заказ
    data: dict с ключами:
        - items: [(article, quantity), ...]
        - status: str
        - pickup_point_id: int
        - order_date: str
        - delivery_date: str or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем товары
    product_items = []
    for article, quantity in data["items"]:
        cursor.execute("SELECT product_id FROM Products WHERE article = ?", (article,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            raise ValueError(f"Товар с артикулом '{article}' не найден!")
        product_items.append((result["product_id"], quantity))
    
    # Проверяем пункт выдачи
    cursor.execute("SELECT point_id FROM PickupPoints WHERE point_id = ?", (data["pickup_point_id"],))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Пункт выдачи не найден!")
    
    # Обновляем заказ
    cursor.execute("""
        UPDATE Orders
        SET order_date = ?, delivery_date = ?, pickup_point_id = ?, status = ?
        WHERE order_id = ?
    """, (
        data["order_date"],
        data["delivery_date"] or None,
        data["pickup_point_id"],
        data["status"],
        order_id
    ))
    
    # Удаляем старые позиции и добавляем новые
    cursor.execute("DELETE FROM OrderItems WHERE order_id = ?", (order_id,))
    
    for product_id, quantity in product_items:
        cursor.execute("""
            INSERT INTO OrderItems (order_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (order_id, product_id, quantity))
    
    conn.commit()
    conn.close()

def delete_order(order_id):
    """
    Удалить заказ по ID
    Возвращает (success: bool, message: str)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT order_id FROM Orders WHERE order_id = ?", (order_id,))
    if not cursor.fetchone():
        conn.close()
        return False, "Заказ не найден в базе данных."
    
    # Сначала удаляем позиции заказа
    cursor.execute("DELETE FROM OrderItems WHERE order_id = ?", (order_id,))
    
    # Затем удаляем сам заказ
    cursor.execute("DELETE FROM Orders WHERE order_id = ?", (order_id,))
    
    conn.commit()
    conn.close()
    
    return True, f"Заказ №{order_id} успешно удалён."

def get_unique_order_statuses():
    """Получить уникальные статусы заказов"""
    return ["Новый", "В обработке", "Собран", "В пути", "Готов к выдаче", "Выдан", "Отменён"]
