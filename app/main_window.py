import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from pathlib import Path
from database import (
    get_all_products,
    search_products,
    get_unique_suppliers,
    delete_product,
)
from styles import (
    COLOR_MAIN_BG,
    COLOR_ACCENT_BG,
    COLOR_ACTION,
    COLOR_DISCOUNT_BG,
    COLOR_OUT_OF_STOCK,
    FONT_FAMILY,
    FONT_SIZE,
)


class MainWindow:
    def __init__(self, root, user, parent_window=None):
        self.root = root
        self.user = user
        self.parent_window = parent_window  # Для кнопки "Назад"

        # Путь к папке resources
        self.resources_path = Path(__file__).parent.parent / "resources"

        # Устанавливаем иконку
        self._set_icon(root)

        # Настройки окна
        self.root.title(f"Список товаров - ООО «Обувь» ({user['full_name']})")
        self.root.geometry("1400x800")
        self.root.configure(bg=COLOR_MAIN_BG)

        # Кэш для изображений
        self.image_cache = {}

        # Параметры поиска/фильтрации/сортировки
        self.search_text = tk.StringVar()
        self.search_text.trace("w", lambda *args: self.apply_filters())

        self.supplier_filter = tk.StringVar(value="Все поставщики")
        self.supplier_filter.trace("w", lambda *args: self.apply_filters())

        self.sort_by = None  # 'stock_quantity' или None
        self.sort_order = "asc"  # 'asc' или 'desc'

        # ✅ РАЗДЕЛЬНЫЕ флаги для разных окон
        self.edit_window_open = False  # Для окна редактирования
        self.add_window_open = False  # Для окна добавления
        self.cart_window_open = False  # Для корзины
        self.orders_window_open = False  # Для заказов

        # === ЗАГОЛОВОК ===
        header = tk.Frame(root, bg=COLOR_ACCENT_BG)
        header.pack(fill=tk.X)

        # Кнопка "Назад" (если есть родительское окно)
        if self.parent_window:
            back_btn = tk.Button(
                header,
                text="← Назад",
                font=(FONT_FAMILY, FONT_SIZE),
                bg=COLOR_ACTION,
                command=self.go_back,
            )
            back_btn.pack(side=tk.LEFT, padx=10, pady=5)

        # Логотип компании
        logo_img = self.load_logo((50, 50))
        if logo_img:
            logo_label = tk.Label(header, image=logo_img, bg=COLOR_ACCENT_BG)
            logo_label.image = logo_img
            logo_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Текст заголовка
        tk.Label(
            header,
            text=f"ООО «Обувь» | {user['full_name']} | Роль: {self.get_role_name()}",
            font=(FONT_FAMILY, FONT_SIZE + 2, "bold"),
            bg=COLOR_ACCENT_BG,
        ).pack(side=tk.LEFT, padx=10, pady=5)

        # Кнопки управления
        self.create_header_buttons(header)

        # Кнопка выхода
        logout_btn = tk.Button(
            header,
            text="Выход",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_ACTION,
            command=self.logout,
        )
        logout_btn.pack(side=tk.RIGHT, padx=10, pady=5)

        # === ПАНЕЛЬ ПОИСКА И ФИЛЬТРОВ ===
        self.create_search_filter_panel()

        # Карточки товаров с прокруткой
        self.create_scrollable_cards()

        # Загружаем начальные данные
        self.load_products()
        # ❌ УДАЛЕНО: self.populate_supplier_filter() — вызывается внутри create_search_filter_panel()

    def create_header_buttons(self, parent):
        """Создать кнопки управления в заголовке"""
        role = self.user["role"]

        # Кнопка "Добавить товар" (только администратор)
        if role == "admin":
            add_btn = tk.Button(
                parent,
                text="➕ Добавить товар",
                font=(FONT_FAMILY, FONT_SIZE),
                bg="#4CAF50",
                fg="white",
                command=self.open_add_product,
            )
            add_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        # ✅ Кнопка "Заказы" — ТОЛЬКО для admin и manager
        if role in ("admin", "manager"):
            orders_btn = tk.Button(
                parent,
                text="📋 Заказы",
                font=(FONT_FAMILY, FONT_SIZE),
                bg="#2196F3",
                fg="white",
                command=self.open_orders,
            )
            orders_btn.pack(side=tk.RIGHT, padx=5, pady=5)

    def create_search_filter_panel(self):
        """Создать панель поиска, фильтрации и сортировки"""
        role = self.user["role"]

        # Панель видна только админу и менеджеру
        if role not in ("admin", "manager"):
            return

        panel = tk.Frame(self.root, bg=COLOR_ACCENT_BG)
        panel.pack(fill=tk.X, padx=10, pady=10)

        # Поисковая строка
        tk.Label(
            panel, text="🔍 Поиск:", font=(FONT_FAMILY, FONT_SIZE), bg=COLOR_ACCENT_BG
        ).pack(side=tk.LEFT, padx=5)

        search_entry = tk.Entry(
            panel,
            textvariable=self.search_text,
            font=(FONT_FAMILY, FONT_SIZE),
            width=30,
        )
        search_entry.pack(side=tk.LEFT, padx=5)

        # Фильтр по поставщику
        tk.Label(
            panel, text="Поставщик:", font=(FONT_FAMILY, FONT_SIZE), bg=COLOR_ACCENT_BG
        ).pack(side=tk.LEFT, padx=(20, 5))

        self.supplier_combo = ttk.Combobox(
            panel,
            textvariable=self.supplier_filter,
            font=(FONT_FAMILY, FONT_SIZE),
            width=20,
            state="readonly",
        )
        self.supplier_combo.pack(side=tk.LEFT, padx=5)

        # Сортировка
        tk.Label(
            panel,
            text="Сортировка по складу:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_ACCENT_BG,
        ).pack(side=tk.LEFT, padx=(20, 5))

        sort_frame = tk.Frame(panel, bg=COLOR_ACCENT_BG)
        sort_frame.pack(side=tk.LEFT)

        self.sort_asc_var = tk.BooleanVar(value=False)
        self.sort_desc_var = tk.BooleanVar(value=False)

        asc_radio = tk.Radiobutton(
            sort_frame,
            text="↑ По возрастанию",
            variable=self.sort_asc_var,
            value=True,
            font=(FONT_FAMILY, FONT_SIZE - 1),
            bg=COLOR_ACCENT_BG,
            command=lambda: self.set_sort_order("asc"),
        )
        asc_radio.pack(side=tk.LEFT, padx=5)

        desc_radio = tk.Radiobutton(
            sort_frame,
            text="↓ По убыванию",
            variable=self.sort_desc_var,
            value=True,
            font=(FONT_FAMILY, FONT_SIZE - 1),
            bg=COLOR_ACCENT_BG,
            command=lambda: self.set_sort_order("desc"),
        )
        desc_radio.pack(side=tk.LEFT, padx=5)

        reset_btn = tk.Button(
            sort_frame,
            text="Сброс",
            font=(FONT_FAMILY, FONT_SIZE - 1),
            command=self.reset_sort,
        )
        reset_btn.pack(side=tk.LEFT, padx=5)

        # ✅ Заполняем фильтр поставщиков (теперь supplier_combo уже создан)
        self.populate_supplier_filter()

    def populate_supplier_filter(self):
        """Заполнить выпадающий список поставщиков"""
        # Проверяем, существует ли supplier_combo (для клиентов его нет)
        if not hasattr(self, "supplier_combo"):
            return

        suppliers = get_unique_suppliers()
        all_suppliers = ["Все поставщики"] + suppliers
        self.supplier_combo["values"] = all_suppliers

    def set_sort_order(self, order):
        """Установить порядок сортировки"""
        self.sort_by = "stock_quantity"
        self.sort_order = order

        if order == "asc":
            self.sort_asc_var.set(True)
            self.sort_desc_var.set(False)
        else:
            self.sort_asc_var.set(False)
            self.sort_desc_var.set(True)

        self.apply_filters()

    def reset_sort(self):
        """Сбросить сортировку"""
        self.sort_by = None
        self.sort_order = "asc"
        self.sort_asc_var.set(False)
        self.sort_desc_var.set(False)
        self.apply_filters()

    def apply_filters(self):
        """Применить поиск, фильтрацию и сортировку"""
        search_text = self.search_text.get()
        supplier = self.supplier_filter.get()

        products = search_products(
            search_text,
            supplier_filter=supplier if supplier != "Все поставщики" else None,
            sort_by=self.sort_by,
            sort_order=self.sort_order,
        )

        # Очищаем старые карточки
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        # Перерисовываем
        self.placeholder_img = self.load_image_by_name("picture.png", (200, 200))

        for row_idx, row in enumerate(products):
            (
                product_id,
                article,
                name,
                unit,
                price,
                supplier,
                manufacturer,
                category,
                discount,
                stock_quantity,
                description,
                image_path,
            ) = row

            self.create_product_card(
                row_idx,
                product_id,
                article,
                name,
                description or "",
                category,
                manufacturer,
                supplier,
                price,
                unit,
                stock_quantity,
                discount,
                image_path,
            )

    def go_back(self):
        """Вернуться к родительскому окну"""
        if self.parent_window:
            self.root.destroy()

    def open_add_product(self):
        """Открыть окно добавления товара"""
        if self.add_window_open:
            messagebox.showwarning(
                "Предупреждение",
                "Окно добавления товара уже открыто!\n\n"
                "Закройте его, чтобы открыть новое.",
                icon=messagebox.WARNING,
            )
            return

        add_win = tk.Toplevel(self.root)
        from add_product_window import AddProductWindow

        def on_add_close():
            self.add_window_open = False
            self.refresh_products()
            self.restore_mousewheel()

        app = AddProductWindow(
            add_win, self.user, self.resources_path, on_close=on_add_close
        )
        self.add_window_open = True

    def open_edit_product(self, product_id):
        """Открыть окно редактирования товара"""
        if self.edit_window_open:
            messagebox.showwarning(
                "Предупреждение",
                "Сначала закройте окно редактирования другого товара!\n\n"
                "Это ограничение предотвращает случайное изменение нескольких товаров одновременно.",
                icon=messagebox.WARNING,
            )
            return

        edit_win = tk.Toplevel(self.root)
        from edit_product_window import EditProductWindow

        def on_edit_close():
            self.edit_window_open = False
            self.refresh_products()
            self.restore_mousewheel()

        app = EditProductWindow(
            edit_win, self.user, product_id, self.resources_path, on_close=on_edit_close
        )
        self.edit_window_open = True

    def open_orders(self):
        """Открыть просмотр заказов"""
        if self.orders_window_open:
            messagebox.showwarning(
                "Предупреждение", "Окно заказов уже открыто!", icon=messagebox.WARNING
            )
            return

        orders_win = tk.Toplevel(self.root)
        from orders_window import OrdersWindow

        def on_orders_close():
            self.orders_window_open = False
            self.refresh_products()
            self.restore_mousewheel()

        self.orders_window_open = True

    def restore_mousewheel(self):
        """Восстановить прокрутку главного окна"""
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def refresh_products(self):
        """Обновить список товаров"""
        self.apply_filters()

    def get_role_name(self):
        roles = {
            "admin": "Администратор",
            "manager": "Менеджер",
            "client": "Клиент",
            "guest": "Гость",
        }
        return roles.get(self.user["role"], self.user["role"])

    def create_scrollable_cards(self):
        """Создать прокручиваемую область для карточек"""
        self.canvas = tk.Canvas(self.root, bg=COLOR_MAIN_BG, highlightthickness=0)

        v_scrollbar = ttk.Scrollbar(
            self.root, orient="vertical", command=self.canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            self.root, orient="horizontal", command=self.canvas.xview
        )

        self.canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        self.cards_frame = tk.Frame(self.canvas, bg=COLOR_MAIN_BG)

        self.cards_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.cards_frame, anchor="nw"
        )
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # ✅ Привязываем ко всему приложению
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

    def on_canvas_configure(self, event):
        """Настроить ширину canvas при изменении размера окна"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def on_mousewheel(self, event):
        """Прокрутка там, где находится курсор мыши"""
        # Получаем виджет под курсором
        widget = self.root.winfo_containing(event.x_root, event.y_root)

        # Получаем корневое окно этого виджета
        if widget:
            toplevel = widget.winfo_toplevel()

            # Если курсор НЕ над главным окном — не прокручиваем главное
            if toplevel != self.root:
                return

        # Прокручиваем главное окно
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_products(self):
        """Загрузить товары"""
        products = get_all_products()

        self.placeholder_img = self.load_image_by_name("picture.png", (200, 200))

        for row_idx, row in enumerate(products):
            (
                product_id,
                article,
                name,
                unit,
                price,
                supplier,
                manufacturer,
                category,
                discount,
                stock_quantity,
                description,
                image_path,
            ) = row

            self.create_product_card(
                row_idx,
                product_id,
                article,
                name,
                description or "",
                category,
                manufacturer,
                supplier,
                price,
                unit,
                stock_quantity,
                discount,
                image_path,
            )

    def create_product_card(
        self,
        index,
        product_id,
        article,
        name,
        description,
        category,
        manufacturer,
        supplier,
        price,
        unit,
        stock_quantity,
        discount,
        image_path,
    ):
        """Создать карточку товара"""

        # Цвет фона
        if discount > 15:
            card_bg = COLOR_DISCOUNT_BG
            text_color = "white"
            discount_block_bg = "#1E5A3E"
            discount_block_fg = "white"
        elif stock_quantity == 0:
            card_bg = COLOR_OUT_OF_STOCK
            text_color = "black"
            discount_block_bg = "#8FB8C7"
            discount_block_fg = "black"
        else:
            card_bg = "white"
            text_color = "black"
            discount_block_bg = "#EEEEEE"
            discount_block_fg = "black"

        card = tk.Frame(self.cards_frame, bg=card_bg, relief="solid", bd=1)
        card.grid(row=index, column=0, sticky="ew", padx=10, pady=5)

        self.cards_frame.grid_columnconfigure(0, weight=1)

        # Фото
        photo_frame = tk.Frame(card, bg=card_bg)
        photo_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        photo_container = tk.Frame(photo_frame, bg="#F0F0F0", relief="solid", bd=1)
        photo_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        photo_img = self.get_product_image(image_path, product_id, (200, 200))

        photo_label = tk.Label(photo_container, image=photo_img, bg="#F0F0F0")
        photo_label.image = photo_img
        photo_label.pack(fill=tk.BOTH, expand=True)

        # Информация
        info_frame = tk.Frame(card, bg=card_bg)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_separator = tk.Frame(card, bg="#CCCCCC", width=1)
        left_separator.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=10)

        header_text = f"{category} | {name}"
        header_lbl = tk.Label(
            info_frame,
            text=header_text,
            font=(FONT_FAMILY, FONT_SIZE + 2, "bold"),
            bg=card_bg,
            fg=text_color,
            anchor="w",
        )
        header_lbl.pack(fill=tk.X, pady=(0, 10))

        specs = [
            ("Описание:", description if description else "—"),
            ("Производитель:", manufacturer if manufacturer else "—"),
            ("Поставщик:", supplier if supplier else "—"),
            ("Цена:", None),
            ("Ед. изм.:", unit),
            ("На складе:", str(stock_quantity)),
        ]

        for label, value in specs:
            line_frame = tk.Frame(info_frame, bg=card_bg)
            line_frame.pack(fill=tk.X, pady=2)

            label_lbl = tk.Label(
                line_frame,
                text=label,
                font=(FONT_FAMILY, FONT_SIZE),
                bg=card_bg,
                fg=text_color,
                anchor="w",
                width=15,
            )
            label_lbl.pack(side=tk.LEFT)

            if label == "Цена:":
                if discount > 0:
                    old_price_lbl = tk.Label(
                        line_frame,
                        text=f"{price:.0f}",
                        font=(FONT_FAMILY, FONT_SIZE, "overstrike"),
                        fg="red",
                        bg=card_bg,
                    )
                    old_price_lbl.pack(side=tk.LEFT)

                    final_price = price * (1 - discount / 100)
                    new_price_lbl = tk.Label(
                        line_frame,
                        text=f" → {final_price:.0f} руб.",
                        font=(FONT_FAMILY, FONT_SIZE, "bold"),
                        fg=text_color,
                        bg=card_bg,
                    )
                    new_price_lbl.pack(side=tk.LEFT)
                else:
                    value_lbl = tk.Label(
                        line_frame,
                        text=f"{price:.0f} руб.",
                        font=(FONT_FAMILY, FONT_SIZE, "bold"),
                        fg=text_color,
                        bg=card_bg,
                        anchor="w",
                    )
                    value_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
            else:
                value_lbl = tk.Label(
                    line_frame,
                    text=value,
                    font=(FONT_FAMILY, FONT_SIZE),
                    fg=text_color,
                    bg=card_bg,
                    anchor="w",
                )
                value_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Правый блок
        right_separator = tk.Frame(card, bg="#CCCCCC", width=1)
        right_separator.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=10)

        right_frame = tk.Frame(card, bg=card_bg)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # Скидка
        if discount > 0:
            discount_text = f"Скидка\n{discount}%"
        else:
            discount_text = "Скидка\n0%"

        discount_lbl = tk.Label(
            right_frame,
            text=discount_text,
            font=(FONT_FAMILY, FONT_SIZE + 1, "bold"),
            bg=discount_block_bg,
            fg=discount_block_fg,
            justify=tk.CENTER,
            padx=10,
            pady=10,
        )
        discount_lbl.pack(fill=tk.BOTH, expand=True)

        # Кнопки (только админ)
        if self.user["role"] == "admin":
            edit_btn = tk.Button(
                right_frame,
                text="✏️",
                font=(FONT_FAMILY, FONT_SIZE - 1),
                bg=COLOR_ACTION,
                width=3,
                command=lambda pid=product_id: self.open_edit_product(pid),
            )
            edit_btn.pack(fill=tk.X, pady=(10, 5))

            delete_btn = tk.Button(
                right_frame,
                text="🗑️",
                font=(FONT_FAMILY, FONT_SIZE - 1),
                bg="#F44336",
                fg="white",
                width=3,
                command=lambda pid=product_id: self.delete_product(pid),
            )
            delete_btn.pack(fill=tk.X)

    def delete_product(self, product_id):
        """Удалить товар"""
        # Проверка на наличие в заказах
        success, message = delete_product(product_id)

        if not success:
            messagebox.showerror(
                "Ошибка удаления",
                message + "\n\n"
                "Нельзя удалить товар, который уже присутствует в заказах.",
                icon=messagebox.ERROR,
            )
            return

        # Подтверждение
        if messagebox.askyesno(
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить этот товар?\n\n" "Это действие необратимо!",
            icon=messagebox.WARNING,
        ):
            messagebox.showinfo("Успех", message, icon=messagebox.INFO)
            self.refresh_products()

    def get_product_image(self, image_path, product_id, size=(200, 200)):
        """Получить изображение товара"""
        if image_path:
            img = self.load_image_by_name(image_path, size)
            if img:
                return img

        for ext in [".jpg", ".png", ".jpeg"]:
            test_name = f"{product_id}{ext}"
            img = self.load_image_by_name(test_name, size)
            if img:
                return img

        return self.placeholder_img

    def load_image_by_name(self, filename, size=(200, 200)):
        """Загрузить изображение"""
        img_path = self.resources_path / filename

        if not img_path.exists():
            return None

        if img_path in self.image_cache:
            return self.image_cache[img_path]

        try:
            img = Image.open(img_path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.image_cache[img_path] = photo
            return photo
        except Exception as e:
            print(f"Ошибка загрузки {img_path}: {e}")
            return None

    def load_logo(self, size=(50, 50)):
        """Загрузить логотип"""
        logo_names = ["Icon.png", "Icon.JPG", "logo.jpg", "logo.png", "picture.png"]

        for name in logo_names:
            logo_path = self.resources_path / name
            if logo_path.exists():
                try:
                    img = Image.open(logo_path)
                    img = img.resize(size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    return photo
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки логотипа {logo_path}: {e}")

        return None

    def _set_icon(self, root):
        """Установить иконку"""
        icon_path = self.resources_path / "Icon.png"

        if not icon_path.exists():
            print(f"⚠️ Иконка не найдена: {icon_path}")
            return

        try:
            img = Image.open(icon_path)
            img = img.resize((48, 48), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            root.iconphoto(True, photo)
            root._icon_photo = photo
            print(f"✅ Иконка установлена: {icon_path}")
        except Exception as e:
            print(f"❌ Ошибка установки иконки: {e}")

    def logout(self):
        if messagebox.askyesno(
            "Выход из системы",
            "Вы уверены, что хотите выйти?\n\nВсе несохранённые изменения будут потеряны.",
            icon=messagebox.QUESTION,
        ):
            self.root.destroy()
            root = tk.Tk()
            from login_window import LoginWindow

            app = LoginWindow(root)
            root.mainloop()
