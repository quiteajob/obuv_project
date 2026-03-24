import tkinter as tk
from tkinter import messagebox, ttk
from database import get_all_orders, delete_order
from styles import COLOR_MAIN_BG, COLOR_ACCENT_BG, COLOR_ACTION, FONT_FAMILY, FONT_SIZE


class OrdersWindow:
    def __init__(self, root, user, on_close=None):
        self.root = root
        self.user = user
        self.on_close = on_close

        self.root.title("Заказы - ООО «Обувь»")
        self.root.geometry("1000x700")
        self.root.configure(bg=COLOR_MAIN_BG)

        # Флаг для блокировки множественного открытия окна редактирования
        self.edit_window_open = False

        # Заголовок
        header = tk.Frame(root, bg=COLOR_ACCENT_BG)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text=f"📋 Заказы | {user['full_name']}",
            font=(FONT_FAMILY, FONT_SIZE + 2, "bold"),
            bg=COLOR_ACCENT_BG,
        ).pack(padx=10, pady=10)

        # Кнопка "Добавить заказ" (только администратор)
        if user["role"] == "admin":
            add_btn = tk.Button(
                header,
                text="➕ Добавить заказ",
                font=(FONT_FAMILY, FONT_SIZE),
                bg="#4CAF50",
                fg="white",
                command=self.open_add_order,
            )
            add_btn.pack(side=tk.RIGHT, padx=10, pady=5)

        # Контейнер для карточек с прокруткой
        self.canvas = tk.Canvas(root, bg=COLOR_MAIN_BG, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)

        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        self.cards_frame = tk.Frame(self.canvas, bg=COLOR_MAIN_BG)

        self.cards_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.cards_frame, anchor="nw"
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width),
        )

        # Прокрутка колесом мыши
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        v_scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Загружаем заказы
        self.load_orders()

        # Обработчик закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_mousewheel(self, event):
        """Прокрутка там, где находится курсор мыши"""
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        if widget and widget.winfo_toplevel() == self.root:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_orders(self):
        """Загрузить все заказы"""
        orders = get_all_orders()

        for row_idx, row in enumerate(orders):
            order_id, article, status, pickup_address, order_date, delivery_date = row
            self.create_order_card(
                row_idx,
                order_id,
                article,
                status,
                pickup_address,
                order_date,
                delivery_date or "Не назначена",
            )

    def create_order_card(
        self,
        index,
        order_id,
        article,
        status,
        pickup_address,
        order_date,
        delivery_date,
    ):
        """Создать карточку заказа"""
        card = tk.Frame(self.cards_frame, bg="white", relief="solid", bd=1)
        card.grid(row=index, column=0, sticky="ew", padx=10, pady=5)
        self.cards_frame.grid_columnconfigure(0, weight=1)

        # === ЛЕВЫЙ БЛОК (70-80%) ===
        left_frame = tk.Frame(card, bg="white")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Артикул
        tk.Label(
            left_frame,
            text=f"Артикул заказа: {article}",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg="white",
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 5))

        # Статус
        tk.Label(
            left_frame,
            text=f"Статус заказа: {status}",
            font=(FONT_FAMILY, FONT_SIZE),
            bg="white",
            anchor="w",
        ).pack(fill=tk.X, pady=3)

        # Адрес пункта выдачи
        tk.Label(
            left_frame,
            text=f"Адрес пункта выдачи: {pickup_address}",
            font=(FONT_FAMILY, FONT_SIZE),
            bg="white",
            anchor="w",
            wraplength=500,
        ).pack(fill=tk.X, pady=3)

        # Дата заказа
        tk.Label(
            left_frame,
            text=f"Дата заказа: {order_date}",
            font=(FONT_FAMILY, FONT_SIZE),
            bg="white",
            anchor="w",
        ).pack(fill=tk.X, pady=3)

        # === ПРАВЫЙ БЛОК (20-30%) ===
        right_frame = tk.Frame(card, bg="#E3F2FD", relief="solid", bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 15), pady=15)

        # Дата доставки (по центру)
        tk.Label(
            right_frame,
            text="Дата доставки",
            font=(FONT_FAMILY, FONT_SIZE - 1),
            bg="#E3F2FD",
            fg="gray",
        ).pack(pady=(5, 0))

        tk.Label(
            right_frame,
            text=delivery_date,
            font=(FONT_FAMILY, FONT_SIZE + 1, "bold"),
            bg="#E3F2FD",
            justify=tk.CENTER,
        ).pack(expand=True, fill=tk.BOTH, pady=5)

        # === КНОПКИ (только администратор) ===
        if self.user["role"] == "admin":
            btn_frame = tk.Frame(card, bg="white")
            btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=15)

            edit_btn = tk.Button(
                btn_frame,
                text="✏️",
                font=(FONT_FAMILY, FONT_SIZE - 1),
                bg=COLOR_ACTION,
                width=3,
                command=lambda oid=order_id: self.open_edit_order(oid),
            )
            edit_btn.pack(fill=tk.X, pady=(0, 5))

            delete_btn = tk.Button(
                btn_frame,
                text="🗑️",
                font=(FONT_FAMILY, FONT_SIZE - 1),
                bg="#F44336",
                fg="white",
                width=3,
                command=lambda oid=order_id: self.delete_order(oid),
            )
            delete_btn.pack(fill=tk.X)

    def open_add_order(self):
        """Открыть окно добавления заказа"""
        if self.edit_window_open:
            messagebox.showwarning(
                "Предупреждение",
                "Сначала закройте окно редактирования другого заказа!",
                icon=messagebox.WARNING,
            )
            return

        add_win = tk.Toplevel(self.root)
        from order_form_window import OrderFormWindow

        def on_close():
            self.edit_window_open = False
            self.refresh_orders()
            self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        app = OrderFormWindow(add_win, self.user, order_id=None, on_close=on_close)
        self.edit_window_open = True

    def open_edit_order(self, order_id):
        """Открыть окно редактирования заказа"""
        if self.edit_window_open:
            messagebox.showwarning(
                "Предупреждение",
                "Сначала закройте окно редактирования другого заказа!",
                icon=messagebox.WARNING,
            )
            return

        edit_win = tk.Toplevel(self.root)
        from order_form_window import OrderFormWindow

        def on_close():
            self.edit_window_open = False
            self.refresh_orders()
            self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        app = OrderFormWindow(edit_win, self.user, order_id=order_id, on_close=on_close)
        self.edit_window_open = True

    def delete_order(self, order_id):
        """Удалить заказ"""
        if messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить заказ №{order_id}?\n\n"
            "Это действие необратимо!",
            icon=messagebox.WARNING,
        ):
            success, message = delete_order(order_id)
            if success:
                messagebox.showinfo("Успех", message, icon=messagebox.INFO)
                self.refresh_orders()
            else:
                messagebox.showerror("Ошибка", message, icon=messagebox.ERROR)

    def refresh_orders(self):
        """Обновить список заказов"""
        # Очищаем старые карточки
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        self.load_orders()

    def on_closing(self):
        """Обработчик закрытия окна"""
        if self.on_close:
            self.on_close()
        self.root.destroy()
