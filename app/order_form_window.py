import tkinter as tk
from tkinter import messagebox, ttk
from database import (
    get_order_details,
    add_order,
    update_order,
    get_unique_order_statuses,
    get_pickup_points,
    get_all_product_articles,
    get_article_by_display,
)
from styles import COLOR_MAIN_BG, FONT_FAMILY, FONT_SIZE
from datetime import datetime


class OrderFormWindow:
    def __init__(self, root, user, order_id=None, on_close=None):
        self.root = root
        self.user = user
        self.order_id = order_id
        self.on_close = on_close

        if user["role"] != "admin":
            messagebox.showerror(
                "Ошибка доступа",
                "Только администратор может управлять заказами!",
                icon=messagebox.ERROR,
            )
            root.destroy()
            return

        title = (
            "Добавление заказа"
            if order_id is None
            else f"Редактирование заказа №{order_id}"
        )
        self.root.title(f"{title} - ООО «Обувь»")
        self.root.geometry("750x700")
        self.root.configure(bg=COLOR_MAIN_BG)

        self.fields = {}
        self.items_listbox = None
        self.items = []
        self.product_articles = []  # Список для отображения

        self.create_form()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_form(self):
        """Создать форму"""
        form_frame = tk.Frame(self.root, bg=COLOR_MAIN_BG)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Загружаем данные для редактирования
        if self.order_id:
            order = get_order_details(self.order_id)
            if not order:
                messagebox.showerror(
                    "Ошибка", "Заказ не найден!", icon=messagebox.ERROR
                )
                self.root.destroy()
                return
            (
                _,
                order_date,
                delivery_date,
                status,
                pickup_point_id,
                pickup_address,
                items,
            ) = order
        else:
            order_date = datetime.now().strftime("%Y-%m-%d")
            delivery_date = ""
            status = "Новый"
            pickup_point_id = None
            items = []

        # === Дата заказа ===
        self._create_field(
            form_frame, "order_date", "Дата заказа *:", width=20, default=order_date
        )

        # === Дата доставки ===
        self._create_field(
            form_frame,
            "delivery_date",
            "Дата доставки:",
            width=20,
            default=delivery_date or "",
        )

        # === Статус (выпадающий список) ===
        tk.Label(
            form_frame,
            text="Статус заказа *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w", pady=(10, 5))

        statuses = get_unique_order_statuses()
        self.fields["status"] = ttk.Combobox(
            form_frame,
            values=statuses,
            font=(FONT_FAMILY, FONT_SIZE),
            width=30,
            state="readonly",
        )
        self.fields["status"].pack(anchor="w")
        self.fields["status"].set(status if status in statuses else statuses[0])

        # === Пункт выдачи (выпадающий список) ===
        tk.Label(
            form_frame,
            text="Пункт выдачи *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w", pady=(10, 5))

        pickup_points = get_pickup_points()
        self.pickup_points = pickup_points
        pickup_addresses = [addr for (_, addr) in pickup_points]

        self.fields["pickup_point"] = ttk.Combobox(
            form_frame,
            values=pickup_addresses,
            font=(FONT_FAMILY, FONT_SIZE),
            width=50,
            state="readonly",
        )
        self.fields["pickup_point"].pack(anchor="w")

        if pickup_point_id:
            for idx, (pid, addr) in enumerate(pickup_points):
                if pid == pickup_point_id:
                    self.fields["pickup_point"].current(idx)
                    break
        elif pickup_addresses:
            self.fields["pickup_point"].current(0)

        # === Товары заказа ===
        tk.Label(
            form_frame,
            text="Товары в заказе *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w", pady=(15, 5))

        items_frame = tk.Frame(form_frame, bg=COLOR_MAIN_BG)
        items_frame.pack(fill=tk.BOTH, expand=True, anchor="w")

        # Список товаров
        list_frame = tk.Frame(items_frame, bg="white", relief="solid", bd=1)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.items_listbox = tk.Listbox(
            list_frame, font=(FONT_FAMILY, FONT_SIZE - 1), height=8
        )
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.items_listbox.yview
        )
        self.items_listbox.configure(yscrollcommand=scrollbar.set)

        self.items_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Кнопки управления товарами
        btn_frame = tk.Frame(items_frame, bg=COLOR_MAIN_BG)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        tk.Button(
            btn_frame,
            text="➕ Добавить",
            font=(FONT_FAMILY, FONT_SIZE - 1),
            command=self.add_item,
        ).pack(fill=tk.X, pady=2)
        tk.Button(
            btn_frame,
            text="✏️ Изменить",
            font=(FONT_FAMILY, FONT_SIZE - 1),
            command=self.edit_item,
        ).pack(fill=tk.X, pady=2)
        tk.Button(
            btn_frame,
            text="🗑️ Удалить",
            font=(FONT_FAMILY, FONT_SIZE - 1),
            command=self.delete_item,
        ).pack(fill=tk.X, pady=2)

        self.items = items if items else []
        self._refresh_items_list()

        tk.Label(
            form_frame,
            text="💡 Выберите товар из списка и укажите количество",
            font=(FONT_FAMILY, FONT_SIZE - 2),
            bg=COLOR_MAIN_BG,
            fg="gray",
        ).pack(anchor="w", pady=(5, 0))

        # === Кнопки ===
        btn_frame = tk.Frame(form_frame, bg=COLOR_MAIN_BG)
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame,
            text="💾 Сохранить",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.save_order,
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame,
            text="Отмена",
            font=(FONT_FAMILY, FONT_SIZE),
            command=self.on_closing,
        ).pack(side=tk.LEFT, padx=10)

    def _create_field(self, parent, field_name, label_text, width=20, default=""):
        """Создать поле ввода"""
        tk.Label(
            parent, text=label_text, font=(FONT_FAMILY, FONT_SIZE), bg=COLOR_MAIN_BG
        ).pack(anchor="w", pady=(10, 5))
        entry = tk.Entry(parent, font=(FONT_FAMILY, FONT_SIZE), width=width)
        entry.pack(anchor="w")
        if default:
            entry.insert(0, str(default))
        self.fields[field_name] = entry

    def _refresh_items_list(self):
        """Обновить список товаров"""
        self.items_listbox.delete(0, tk.END)
        for article, qty in self.items:
            self.items_listbox.insert(tk.END, f"{article} — {qty} шт.")

    def add_item(self):
        """Добавить товар"""
        # Загружаем список товаров только при открытии диалога
        if not self.product_articles:
            self.product_articles = get_all_product_articles()

        if not self.product_articles:
            messagebox.showerror(
                "Ошибка",
                "В базе нет товаров! Сначала добавьте товары.",
                icon=messagebox.ERROR,
            )
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить товар")
        dialog.geometry("500x250")
        dialog.configure(bg=COLOR_MAIN_BG)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Выберите товар *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(pady=(10, 5))

        # Выпадающий список с поиском
        article_combo = ttk.Combobox(
            dialog,
            values=self.product_articles,
            font=(FONT_FAMILY, FONT_SIZE),
            width=55,
            state="readonly",
        )
        article_combo.pack(pady=5)
        article_combo.current(0)

        tk.Label(
            dialog,
            text="Количество *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(pady=(10, 5))
        qty_entry = tk.Entry(dialog, font=(FONT_FAMILY, FONT_SIZE), width=10)
        qty_entry.pack(pady=5)
        qty_entry.insert(0, "1")

        def on_confirm():
            display_text = article_combo.get().strip()
            try:
                qty = int(qty_entry.get().strip())
                if qty <= 0:
                    raise ValueError()
            except:
                messagebox.showerror(
                    "Ошибка",
                    "Количество должно быть положительным числом!",
                    parent=dialog,
                )
                return

            article = get_article_by_display(display_text)
            if not article:
                messagebox.showerror("Ошибка", "Товар не выбран!", parent=dialog)
                return

            self.items.append((article, qty))
            self._refresh_items_list()
            dialog.destroy()

        tk.Button(
            dialog,
            text="Добавить",
            font=(FONT_FAMILY, FONT_SIZE),
            bg="#4CAF50",
            fg="white",
            command=on_confirm,
        ).pack(pady=10)
        tk.Button(
            dialog, text="Отмена", font=(FONT_FAMILY, FONT_SIZE), command=dialog.destroy
        ).pack()

    def edit_item(self):
        """Изменить товар"""
        sel = self.items_listbox.curselection()
        if not sel:
            messagebox.showwarning(
                "Предупреждение", "Выберите товар для редактирования!"
            )
            return

        idx = sel[0]
        article, qty = self.items[idx]

        # Загружаем список товаров только при открытии диалога
        if not self.product_articles:
            self.product_articles = get_all_product_articles()

        if not self.product_articles:
            messagebox.showerror("Ошибка", "В базе нет товаров!", icon=messagebox.ERROR)
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Изменить товар")
        dialog.geometry("500x250")
        dialog.configure(bg=COLOR_MAIN_BG)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Выберите товар *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(pady=(10, 5))

        article_combo = ttk.Combobox(
            dialog,
            values=self.product_articles,
            font=(FONT_FAMILY, FONT_SIZE),
            width=55,
            state="readonly",
        )
        article_combo.pack(pady=5)

        # Находим текущий товар в списке
        current_display = f"{article} — "
        for i, display in enumerate(self.product_articles):
            if display.startswith(current_display):
                article_combo.current(i)
                break

        tk.Label(
            dialog,
            text="Количество *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(pady=(10, 5))
        qty_entry = tk.Entry(dialog, font=(FONT_FAMILY, FONT_SIZE), width=10)
        qty_entry.insert(0, str(qty))
        qty_entry.pack(pady=5)

        def on_confirm():
            display_text = article_combo.get().strip()
            try:
                new_qty = int(qty_entry.get().strip())
                if new_qty <= 0:
                    raise ValueError()
            except:
                messagebox.showerror(
                    "Ошибка",
                    "Количество должно быть положительным числом!",
                    parent=dialog,
                )
                return

            new_article = get_article_by_display(display_text)
            if not new_article:
                messagebox.showerror("Ошибка", "Товар не выбран!", parent=dialog)
                return

            self.items[idx] = (new_article, new_qty)
            self._refresh_items_list()
            dialog.destroy()

        tk.Button(
            dialog,
            text="Сохранить",
            font=(FONT_FAMILY, FONT_SIZE),
            bg="#4CAF50",
            fg="white",
            command=on_confirm,
        ).pack(pady=10)
        tk.Button(
            dialog, text="Отмена", font=(FONT_FAMILY, FONT_SIZE), command=dialog.destroy
        ).pack()

    def delete_item(self):
        """Удалить товар"""
        sel = self.items_listbox.curselection()
        if not sel:
            messagebox.showwarning("Предупреждение", "Выберите товар для удаления!")
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранный товар из заказа?"):
            idx = sel[0]
            del self.items[idx]
            self._refresh_items_list()

    def validate_form(self):
        """Проверить форму"""
        errors = []

        # Дата заказа
        order_date = self.fields["order_date"].get().strip()
        if not order_date:
            errors.append("❌ Дата заказа обязательна.")
        else:
            try:
                datetime.strptime(order_date, "%Y-%m-%d")
            except:
                errors.append("❌ Дата заказа должна быть в формате ГГГГ-ММ-ДД.")

        # Дата доставки (необязательна)
        delivery_date = self.fields["delivery_date"].get().strip()
        if delivery_date:
            try:
                datetime.strptime(delivery_date, "%Y-%m-%d")
            except:
                errors.append("❌ Дата доставки должна быть в формате ГГГГ-ММ-ДД.")

        # Статус
        status = self.fields["status"].get().strip()
        if not status:
            errors.append("❌ Статус обязателен.")

        # Пункт выдачи
        if (
            not self.fields.get("pickup_point")
            or not self.fields["pickup_point"].get().strip()
        ):
            errors.append("❌ Выберите пункт выдачи.")

        # Товары
        if not self.items:
            errors.append("❌ Добавьте хотя бы один товар в заказ.")

        if errors:
            messagebox.showerror("Ошибка", "\n".join(errors))
            return False

        return True

    def save_order(self):
        """Сохранить заказ"""
        if not self.validate_form():
            return

        # Получаем выбранный пункт выдачи
        selected_address = self.fields["pickup_point"].get().strip()
        pickup_point_id = None
        for pid, addr in self.pickup_points:
            if addr == selected_address:
                pickup_point_id = pid
                break

        if not pickup_point_id:
            messagebox.showerror("Ошибка", "Пункт выдачи не найден!")
            return

        data = {
            "items": self.items,
            "status": self.fields["status"].get().strip(),
            "pickup_point_id": pickup_point_id,
            "order_date": self.fields["order_date"].get().strip(),
            "delivery_date": self.fields["delivery_date"].get().strip() or None,
        }

        try:
            if self.order_id:
                update_order(self.order_id, data)
                messagebox.showinfo(
                    "Успех", f"Заказ №{self.order_id} обновлён!", icon=messagebox.INFO
                )
            else:
                add_order(data)
                messagebox.showinfo("Успех", "Заказ добавлен!", icon=messagebox.INFO)

            if self.on_close:
                self.on_close()
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить заказ:\n{str(e)}")

    def on_closing(self):
        """Закрытие"""
        if messagebox.askyesno("Отмена", "Отменить изменения?"):
            if self.on_close:
                self.on_close()
            self.root.destroy()
