import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from PIL import Image, ImageTk
from pathlib import Path
from database import (
    add_product,
    get_unique_categories,
    get_unique_manufacturers,
    get_unique_suppliers,
    get_next_product_id,
)
from styles import COLOR_MAIN_BG, COLOR_ACCENT_BG, COLOR_ACTION, FONT_FAMILY, FONT_SIZE


class AddProductWindow:
    def __init__(self, root, user, resources_path, on_close=None):
        self.root = root
        self.user = user
        self.resources_path = resources_path
        self.on_close = on_close

        # Проверка прав
        if user["role"] != "admin":
            messagebox.showerror(
                "Ошибка доступа",
                "Только администратор может добавлять товары!\n\n"
                "Обратитесь к администратору системы для получения доступа.",
                icon=messagebox.ERROR,
            )
            root.destroy()
            return

        self.root.title("Добавление товара - ООО «Обувь»")
        self.root.geometry("700x750")
        self.root.configure(bg=COLOR_MAIN_BG)
        # self.root.resizable(False, False)  # ← Закомментируйте, чтобы можно было менять размер

        # Путь для сохранения фото
        self.photos_path = self.resources_path

        # Переменные для валидации
        self.price_var = tk.StringVar()
        self.quantity_var = tk.StringVar()
        self.discount_var = tk.StringVar(value="0")
        self.selected_image_path = None

        # ✅ === ДОБАВЛЕНА ПРОКРУТКА ===
        self.canvas = tk.Canvas(root, bg=COLOR_MAIN_BG, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        v_scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        v_scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=v_scrollbar.set)

        self.scrollable_frame = tk.Frame(self.canvas, bg=COLOR_MAIN_BG)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width),
        )

        # Привязка к колесу мыши
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        # === === КОНЕЦ БЛОКА ПРОКРУТКИ ===

        # Заголовок ВНУТРИ scrollable_frame
        header = tk.Frame(self.scrollable_frame, bg=COLOR_ACCENT_BG)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text=f"➕ Добавление товара | {user['full_name']}",
            font=(FONT_FAMILY, FONT_SIZE + 2, "bold"),
            bg=COLOR_ACCENT_BG,
        ).pack(padx=10, pady=10)

        # Форма ВНУТРИ scrollable_frame
        self.create_form()

        # Обработчик закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_mousewheel(self, event):
        """Прокрутка там, где находится курсор мыши"""
        widget = self.root.winfo_containing(event.x_root, event.y_root)

        if widget and widget.winfo_toplevel() == self.root:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_form(self):
        """Создать форму добавления товара"""
        # ✅ Теперь создаём поля ВНУТРИ self.scrollable_frame
        self._create_form_fields()

    def _create_form_fields(self):
        """Создать форму добавления товара"""
        form_frame = tk.Frame(self.scrollable_frame, bg=COLOR_MAIN_BG)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        self.fields = {}

        # === ФОТО ТОВАРА ===
        photo_frame = tk.Frame(form_frame, bg=COLOR_MAIN_BG)
        photo_frame.pack(fill=tk.X, pady=10)

        tk.Label(
            photo_frame,
            text="Фото товара:",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w")

        # Контейнер для фото
        self.photo_container = tk.Frame(
            photo_frame, bg="#F0F0F0", relief="solid", bd=2, width=300, height=200
        )
        self.photo_container.pack(pady=5)
        self.photo_container.pack_propagate(False)

        # Заглушка
        self.photo_label = tk.Label(
            self.photo_container,
            text="Нет фото\n(будет использована заглушка)",
            font=(FONT_FAMILY, FONT_SIZE - 1),
            bg="#F0F0F0",
            fg="gray",
            justify=tk.CENTER,
        )
        self.photo_label.pack(fill=tk.BOTH, expand=True)

        # Кнопки для фото
        btn_frame = tk.Frame(photo_frame, bg=COLOR_MAIN_BG)
        btn_frame.pack(pady=5)

        upload_btn = tk.Button(
            btn_frame,
            text="📁 Загрузить фото",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_ACTION,
            command=self.upload_photo,
        )
        upload_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(
            btn_frame,
            text="❌ Удалить фото",
            font=(FONT_FAMILY, FONT_SIZE),
            command=self.clear_photo,
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        tk.Label(
            photo_frame,
            text="💡 Подсказка: Рекомендуемый размер фото 300x200 пикселей.\n"
            "   Поддерживаемые форматы: JPG, PNG. Макс. размер файла не ограничен.",
            font=(FONT_FAMILY, FONT_SIZE - 2),
            bg=COLOR_MAIN_BG,
            fg="gray",
            justify=tk.LEFT,
        ).pack(anchor="w", pady=5)

        # === Наименование ===
        self._create_field(
            form_frame,
            "name",
            "Наименование товара *:",
            width=50,
            required=True,
            tooltip="Обязательное поле. Введите полное название товара.",
        )

        # === Артикул ===
        self._create_field(
            form_frame,
            "article",
            "Артикул *:",
            width=20,
            required=True,
            tooltip="Обязательное поле. Уникальный идентификатор товара (например, ART-001).",
        )

        # === Категория (выпадающий список) ===
        tk.Label(
            form_frame,
            text="Категория *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w", pady=(10, 5))

        categories = get_unique_categories()
        self.fields["category"] = ttk.Combobox(
            form_frame,
            values=categories,
            font=(FONT_FAMILY, FONT_SIZE),
            width=20,
            state="normal",
        )
        self.fields["category"].pack(anchor="w")

        tk.Label(
            form_frame,
            text="💡 Введите существующую категорию или добавьте новую",
            font=(FONT_FAMILY, FONT_SIZE - 2),
            bg=COLOR_MAIN_BG,
            fg="gray",
        ).pack(anchor="w")

        # === Производитель (выпадающий список) ===
        tk.Label(
            form_frame,
            text="Производитель *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w", pady=(10, 5))

        manufacturers = get_unique_manufacturers()
        self.fields["manufacturer"] = ttk.Combobox(
            form_frame,
            values=manufacturers,
            font=(FONT_FAMILY, FONT_SIZE),
            width=30,
            state="normal",
        )
        self.fields["manufacturer"].pack(anchor="w")

        # === Поставщик (выпадающий список) ===
        tk.Label(
            form_frame,
            text="Поставщик *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w", pady=(10, 5))

        suppliers = get_unique_suppliers()
        self.fields["supplier"] = ttk.Combobox(
            form_frame,
            values=suppliers,
            font=(FONT_FAMILY, FONT_SIZE),
            width=30,
            state="normal",
        )
        self.fields["supplier"].pack(anchor="w")

        # === Единица измерения ===
        self._create_field(
            form_frame,
            "unit",
            "Единица измерения *:",
            width=15,
            required=True,
            default="шт.",
            tooltip="Например: шт., кг, м, пара.",
        )

        # === Цена ===
        tk.Label(
            form_frame,
            text="Цена (руб.) *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w", pady=(10, 5))

        self.fields["price"] = tk.Entry(
            form_frame,
            textvariable=self.price_var,
            font=(FONT_FAMILY, FONT_SIZE),
            width=15,
        )
        self.fields["price"].pack(anchor="w")

        tk.Label(
            form_frame,
            text="💡 Положительное число, могут быть сотые доли (например, 199.99)",
            font=(FONT_FAMILY, FONT_SIZE - 2),
            bg=COLOR_MAIN_BG,
            fg="gray",
        ).pack(anchor="w")

        # === Количество на складе ===
        tk.Label(
            form_frame,
            text="Количество на складе *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w", pady=(10, 5))

        self.fields["stock_quantity"] = tk.Entry(
            form_frame,
            textvariable=self.quantity_var,
            font=(FONT_FAMILY, FONT_SIZE),
            width=15,
        )
        self.fields["stock_quantity"].pack(anchor="w")

        tk.Label(
            form_frame,
            text="💡 Целое неотрицательное число (минимум 0)",
            font=(FONT_FAMILY, FONT_SIZE - 2),
            bg=COLOR_MAIN_BG,
            fg="gray",
        ).pack(anchor="w")

        # === Скидка ===
        tk.Label(
            form_frame,
            text="Действующая скидка (%):",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w", pady=(10, 5))

        self.fields["discount"] = tk.Entry(
            form_frame,
            textvariable=self.discount_var,
            font=(FONT_FAMILY, FONT_SIZE),
            width=15,
        )
        self.fields["discount"].pack(anchor="w")

        tk.Label(
            form_frame,
            text="💡 Число от 0 до 100. По умолчанию 0.",
            font=(FONT_FAMILY, FONT_SIZE - 2),
            bg=COLOR_MAIN_BG,
            fg="gray",
        ).pack(anchor="w")

        # === Описание ===
        tk.Label(
            form_frame,
            text="Описание товара:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w", pady=(10, 5))

        self.fields["description"] = tk.Text(
            form_frame, font=(FONT_FAMILY, FONT_SIZE), height=4, width=50
        )
        self.fields["description"].pack(fill=tk.X)

        # === Кнопки ===
        btn_frame = tk.Frame(form_frame, bg=COLOR_MAIN_BG)
        btn_frame.pack(pady=20)

        save_btn = tk.Button(
            btn_frame,
            text="💾 Сохранить",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.save_product,
        )
        save_btn.pack(side=tk.LEFT, padx=10)

        cancel_btn = tk.Button(
            btn_frame,
            text="Отмена",
            font=(FONT_FAMILY, FONT_SIZE),
            command=self.on_closing,
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)

    def _create_field(
        self,
        parent,
        field_name,
        label_text,
        width=20,
        required=False,
        default="",
        tooltip="",
    ):
        """Создать поле ввода с подсказкой"""
        tk.Label(
            parent, text=label_text, font=(FONT_FAMILY, FONT_SIZE), bg=COLOR_MAIN_BG
        ).pack(anchor="w", pady=(10, 5))

        entry = tk.Entry(parent, font=(FONT_FAMILY, FONT_SIZE), width=width)
        entry.pack(anchor="w")

        if default:
            entry.insert(0, default)

        self.fields[field_name] = entry

        if tooltip:
            tk.Label(
                parent,
                text="💡 " + tooltip,
                font=(FONT_FAMILY, FONT_SIZE - 2),
                bg=COLOR_MAIN_BG,
                fg="gray",
            ).pack(anchor="w")

    def upload_photo(self):
        """Загрузить фото товара"""
        file_path = filedialog.askopenfilename(
            title="Выберите фото товара",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png"), ("Все файлы", "*.*")],
        )

        if not file_path:
            return

        try:
            # Открываем и проверяем размер
            img = Image.open(file_path)

            # Ограничиваем размер 300x200
            img = img.resize((300, 200), Image.Resampling.LANCZOS)

            # Генерируем имя файла
            next_id = get_next_product_id()
            ext = Path(file_path).suffix.lower()
            new_filename = f"{next_id}{ext}"
            save_path = self.photos_path / new_filename

            # Сохраняем
            img.save(save_path)

            # Отображаем
            photo = ImageTk.PhotoImage(img)
            self.photo_label.config(image=photo, text="", compound=tk.CENTER)
            self.photo_label.image = photo

            self.selected_image_path = new_filename

            messagebox.showinfo(
                "Фото загружено",
                f"Фото успешно загружено и сохранено как:\n{new_filename}\n\n"
                f"Размер изменён на 300x200 пикселей.",
                icon=messagebox.INFO,
            )

        except Exception as e:
            messagebox.showerror(
                "Ошибка загрузки фото",
                f"Не удалось загрузить фото:\n{str(e)}\n\n"
                "Проверьте формат файла (JPG, PNG) и повторите попытку.",
                icon=messagebox.ERROR,
            )

    def clear_photo(self):
        """Очистить фото"""
        self.photo_label.config(
            image="", text="Нет фото\n(будет использована заглушка)", compound=tk.CENTER
        )
        self.selected_image_path = None

    def validate_form(self):
        """Проверить корректность данных"""
        errors = []

        # Наименование
        name = self.fields["name"].get().strip()
        if not name:
            errors.append("❌ Наименование товара обязательно для заполнения.")

        # Артикул
        article = self.fields["article"].get().strip()
        if not article:
            errors.append("❌ Артикул обязателен для заполнения.")

        # Категория
        category = self.fields["category"].get().strip()
        if not category:
            errors.append("❌ Категория обязательна для заполнения.")

        # Производитель
        manufacturer = self.fields["manufacturer"].get().strip()
        if not manufacturer:
            errors.append("❌ Производитель обязателен для заполнения.")

        # Поставщик
        supplier = self.fields["supplier"].get().strip()
        if not supplier:
            errors.append("❌ Поставщик обязателен для заполнения.")

        # Единица измерения
        unit = self.fields["unit"].get().strip()
        if not unit:
            errors.append("❌ Единица измерения обязательна.")

        # Цена
        try:
            price = float(self.price_var.get().strip())
            if price < 0:
                errors.append("❌ Цена не может быть отрицательной!")
        except ValueError:
            errors.append("❌ Цена должна быть числом (например, 199.99).")

        # Количество
        try:
            quantity = int(self.quantity_var.get().strip())
            if quantity < 0:
                errors.append("❌ Количество на складе не может быть отрицательным!")
        except ValueError:
            errors.append("❌ Количество должно быть целым числом.")

        # Скидка
        try:
            discount = float(self.discount_var.get().strip())
            if discount < 0 or discount > 100:
                errors.append("❌ Скидка должна быть от 0 до 100%.")
        except ValueError:
            errors.append("❌ Скидка должна быть числом.")

        if errors:
            error_text = (
                "Обнаружены следующие ошибки:\n\n" + "\n".join(errors) + "\n\n"
                "Исправьте ошибки и попробуйте снова."
            )
            messagebox.showerror("Ошибка валидации", error_text, icon=messagebox.ERROR)
            return False

        return True

    def save_product(self):
        """Сохранить новый товар"""
        if not self.validate_form():
            return

        try:
            # Собираем данные
            data = {
                "article": self.fields["article"].get().strip(),
                "name": self.fields["name"].get().strip(),
                "category": self.fields["category"].get().strip(),
                "manufacturer": self.fields["manufacturer"].get().strip(),
                "supplier": self.fields["supplier"].get().strip(),
                "unit": self.fields["unit"].get().strip(),
                "price": float(self.price_var.get().strip()),
                "stock_quantity": int(self.quantity_var.get().strip()),
                "discount": float(self.discount_var.get().strip()),
                "description": self.fields["description"].get("1.0", tk.END).strip(),
                "image_path": self.selected_image_path or "",
            }

            # Добавляем в БД
            add_product(data)

            messagebox.showinfo(
                "Успех",
                f"Товар '{data['name']}' успешно добавлен!\n\n"
                f"Артикул: {data['article']}\n"
                f"ID будет назначен автоматически.",
                icon=messagebox.INFO,
            )

            # ✅ Вызываем on_close ПЕРЕД destroy()
            if self.on_close:
                self.on_close()

            self.root.destroy()

        except Exception as e:
            messagebox.showerror(
                "Ошибка при сохранении",
                f"Не удалось сохранить товар:\n{str(e)}\n\n"
                "Проверьте корректность данных и повторите попытку.\n"
                "Если ошибка повторяется, обратитесь к администратору.",
                icon=messagebox.ERROR,
            )

    def on_closing(self):
        """Обработчик закрытия окна"""
        if messagebox.askyesno(
            "Отмена добавления",
            "Отменить добавление товара?\n\nВсе несохранённые данные будут потеряны.",
            icon=messagebox.QUESTION,
        ):
            # ✅ Вызываем on_close ПЕРЕД destroy()
            if self.on_close:
                self.on_close()
            self.root.destroy()
