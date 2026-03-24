import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from PIL import Image, ImageTk
from pathlib import Path
import os
from database import (
    get_product_by_id, update_product, get_unique_categories,
    get_unique_manufacturers, get_unique_suppliers
)
from styles import COLOR_MAIN_BG, COLOR_ACCENT_BG, COLOR_ACTION, FONT_FAMILY, FONT_SIZE

class EditProductWindow:
    def __init__(self, root, user, product_id, resources_path, on_close=None):
        self.root = root
        self.user = user
        self.product_id = product_id
        self.resources_path = resources_path
        self.on_close = on_close
        
        # Проверка прав
        if user["role"] != "admin":
            messagebox.showerror(
                "Ошибка доступа",
                "Только администратор может редактировать товары!",
                icon=messagebox.ERROR
            )
            root.destroy()
            return
        
        print(f"\n=== ОТКРЫТИЕ РЕДАКТИРОВАНИЯ ===")
        print(f"Product ID: {product_id}")
        
        # Загружаем данные товара
        self.product = get_product_by_id(product_id)
        
        print(f"Результат get_product_by_id: {self.product}")
        
        if not self.product:
            messagebox.showerror(
                "Ошибка",
                f"Товар №{product_id} не найден в базе данных!\n\n"
                "Возможно, он был удалён другим пользователем.",
                icon=messagebox.ERROR
            )
            root.destroy()
            return
        
        # Распаковываем данные для проверки
        (_, article, name, unit, price, supplier, manufacturer,
         category, discount, stock_quantity, description, image_path) = self.product
        
        print(f"Товар: {article} - {name}")
        print(f"Цена: {price}, Склад: {stock_quantity}")
        
        self.root.title(f"Редактирование товара №{product_id} - ООО «Обувь»")
        self.root.geometry("700x780")
        self.root.configure(bg=COLOR_MAIN_BG)
        
        # Переменные для валидации
        self.price_var = tk.StringVar()
        self.quantity_var = tk.StringVar()
        self.discount_var = tk.StringVar()
        self.selected_image_path = None
        self.original_image_path = None
        
        # ✅ === ДОБАВЛЕНА ПРОКРУТКА ===
        # Создаём canvas для прокрутки формы
        self.canvas = tk.Canvas(root, bg=COLOR_MAIN_BG, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        v_scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        v_scrollbar.pack(side="right", fill="y")
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        
        # Основной контейнер внутри canvas
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLOR_MAIN_BG)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        
        # Привязываем прокрутку к колесу мыши
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        # === === КОНЕЦ БЛОКА ПРОКРУТКИ ===
        
        # Заголовок
        header = tk.Frame(self.scrollable_frame, bg=COLOR_ACCENT_BG)  # ← Изменено: self.scrollable_frame
        header.pack(fill=tk.X)
        
        (_, article, name, unit, price, supplier, manufacturer,
         category, discount, stock_quantity, description, image_path) = self.product
        
        tk.Label(
            header,
            text=f"✏️ Редактирование: {article} | {user['full_name']}",
            font=(FONT_FAMILY, FONT_SIZE + 2, "bold"),
            bg=COLOR_ACCENT_BG
        ).pack(padx=10, pady=10)
        
        # Форма (теперь создаётся внутри scrollable_frame)
        self.create_form()
        
        # Обработчик закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    
    def create_form(self):
        """Создать форму редактирования"""
        form_frame = tk.Frame(self.scrollable_frame, bg=COLOR_MAIN_BG)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        self.fields = {}
        
        # === ОТЛАДКА: проверяем данные ===
        print(f"\n=== СОЗДАНИЕ ФОРМЫ РЕДАКТИРОВАНИЯ ===")
        print(f"Данные товара: {self.product}")
        print(f"Тип: {type(self.product)}")
        print(f"Длина кортежа: {len(self.product) if self.product else 0}")
        
        if not self.product or len(self.product) < 12:
            messagebox.showerror(
                "Ошибка",
                f"Некорректные данные товара!\n\n"
                f"Получено: {self.product}\n"
                f"Ожидается кортеж из 12 элементов.",
                icon=messagebox.ERROR
            )
            self.root.destroy()
            return
        
        # Распаковываем данные
        (prod_id, article, name, unit, price, supplier, manufacturer,
         category, discount, stock_quantity, description, image_path) = self.product
        
        print(f"Распаковано:")
        print(f"  ID: {prod_id}")
        print(f"  Артикул: {article}")
        print(f"  Название: {name}")
        print(f"  Ед.изм.: {unit}")
        print(f"  Цена: {price}")
        print(f"  Поставщик: {supplier}")
        print(f"  Производитель: {manufacturer}")
        print(f"  Категория: {category}")
        print(f"  Скидка: {discount}")
        print(f"  Склад: {stock_quantity}")
        print(f"  Описание: {description[:50] if description else '—'}...")
        print(f"  Фото: {image_path}")
        
        # Сохраняем оригинальный путь к фото
        self.original_image_path = image_path if image_path else None
        
        # === ID (только для чтения) ===
        id_frame = tk.Frame(form_frame, bg=COLOR_MAIN_BG)
        id_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            id_frame,
            text=f"ID товара: {prod_id}",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=COLOR_MAIN_BG,
            fg="gray"
        ).pack(anchor="w")
        
        tk.Label(
            id_frame,
            text="💡 ID нельзя изменить. Он назначается автоматически при создании.",
            font=(FONT_FAMILY, FONT_SIZE - 2),
            bg=COLOR_MAIN_BG,
            fg="gray"
        ).pack(anchor="w")
        
        # === ФОТО ТОВАРА ===
        photo_frame = tk.Frame(form_frame, bg=COLOR_MAIN_BG)
        photo_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            photo_frame,
            text="Фото товара:",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg=COLOR_MAIN_BG
        ).pack(anchor="w")
        
        # Контейнер для фото
        self.photo_container = tk.Frame(
            photo_frame,
            bg="#F0F0F0",
            relief="solid",
            bd=2,
            width=300,
            height=200
        )
        self.photo_container.pack(pady=5)
        self.photo_container.pack_propagate(False)
        
        # Загружаем текущее фото или заглушку
        self.load_current_image(image_path)
        
        # Кнопки для фото
        btn_frame = tk.Frame(photo_frame, bg=COLOR_MAIN_BG)
        btn_frame.pack(pady=5)
        
        upload_btn = tk.Button(
            btn_frame,
            text="📁 Загрузить новое фото",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_ACTION,
            command=self.upload_photo
        )
        upload_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(
            btn_frame,
            text="❌ Удалить фото",
            font=(FONT_FAMILY, FONT_SIZE),
            command=self.clear_photo
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Label(
            photo_frame,
            text="💡 При загрузке нового фото старое будет удалено из папки resources.\n"
                 "   Рекомендуемый размер: 300x200 пикселей (JPG, PNG).",
            font=(FONT_FAMILY, FONT_SIZE - 2),
            bg=COLOR_MAIN_BG,
            fg="gray",
            justify=tk.LEFT
        ).pack(anchor="w", pady=5)
        
        # === Наименование ===
        self._create_field(
            form_frame, "name", "Наименование товара *:",
            width=50, required=True, default=name if name else "",
            tooltip="Обязательное поле."
        )
        
        # === Артикул ===
        self._create_field(
            form_frame, "article", "Артикул *:",
            width=20, required=True, default=article if article else "",
            tooltip="Уникальный идентификатор."
        )
        
        # === Категория (выпадающий список) ===
        tk.Label(
            form_frame,
            text="Категория *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG
        ).pack(anchor="w", pady=(10, 5))
        
        categories = get_unique_categories()
        print(f"  Доступные категории: {categories}")
        
        self.fields["category"] = ttk.Combobox(
            form_frame,
            values=categories if categories else [],
            font=(FONT_FAMILY, FONT_SIZE),
            width=20,
            state="normal"
        )
        self.fields["category"].set(category if category else "")
        print(f"  Установлена категория: '{category}'")
        self.fields["category"].pack(anchor="w")
        
        tk.Label(
            form_frame,
            text="💡 Введите существующую категорию или добавьте новую",
            font=(FONT_FAMILY, FONT_SIZE - 2),
            bg=COLOR_MAIN_BG,
            fg="gray"
        ).pack(anchor="w")
        
        # === Производитель ===
        tk.Label(
            form_frame,
            text="Производитель *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG
        ).pack(anchor="w", pady=(10, 5))
        
        manufacturers = get_unique_manufacturers()
        print(f"  Доступные производители: {manufacturers}")
        
        self.fields["manufacturer"] = ttk.Combobox(
            form_frame,
            values=manufacturers if manufacturers else [],
            font=(FONT_FAMILY, FONT_SIZE),
            width=30,
            state="normal"
        )
        self.fields["manufacturer"].set(manufacturer if manufacturer else "")
        print(f"  Установлен производитель: '{manufacturer}'")
        self.fields["manufacturer"].pack(anchor="w")
        
        # === Поставщик ===
        tk.Label(
            form_frame,
            text="Поставщик *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG
        ).pack(anchor="w", pady=(10, 5))
        
        suppliers = get_unique_suppliers()
        print(f"  Доступные поставщики: {suppliers}")
        
        self.fields["supplier"] = ttk.Combobox(
            form_frame,
            values=suppliers if suppliers else [],
            font=(FONT_FAMILY, FONT_SIZE),
            width=30,
            state="normal"
        )
        self.fields["supplier"].set(supplier if supplier else "")
        print(f"  Установлен поставщик: '{supplier}'")
        self.fields["supplier"].pack(anchor="w")
        
        # === Единица измерения ===
        self._create_field(
            form_frame, "unit", "Единица измерения *:",
            width=15, required=True, default=unit if unit else "",
            tooltip="Например: шт., кг, м, пара."
        )
        
        # === Цена ===
        tk.Label(
            form_frame,
            text="Цена (руб.) *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG
        ).pack(anchor="w", pady=(10, 5))
        
        self.price_var = tk.StringVar()
        self.price_var.set(str(price) if price is not None else "0")
        print(f"  Установлена цена: '{price}'")
        
        self.fields["price"] = tk.Entry(
            form_frame,
            textvariable=self.price_var,
            font=(FONT_FAMILY, FONT_SIZE),
            width=15
        )
        self.fields["price"].pack(anchor="w")
        
        tk.Label(
            form_frame,
            text="💡 Положительное число (например, 199.99)",
            font=(FONT_FAMILY, FONT_SIZE - 2),
            bg=COLOR_MAIN_BG,
            fg="gray"
        ).pack(anchor="w")
        
        # === Количество на складе ===
        tk.Label(
            form_frame,
            text="Количество на складе *:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG
        ).pack(anchor="w", pady=(10, 5))
        
        self.quantity_var = tk.StringVar()
        self.quantity_var.set(str(stock_quantity) if stock_quantity is not None else "0")
        print(f"  Установлено количество: '{stock_quantity}'")
        
        self.fields["stock_quantity"] = tk.Entry(
            form_frame,
            textvariable=self.quantity_var,
            font=(FONT_FAMILY, FONT_SIZE),
            width=15
        )
        self.fields["stock_quantity"].pack(anchor="w")
        
        tk.Label(
            form_frame,
            text="💡 Целое неотрицательное число",
            font=(FONT_FAMILY, FONT_SIZE - 2),
            bg=COLOR_MAIN_BG,
            fg="gray"
        ).pack(anchor="w")
        
        # === Скидка ===
        tk.Label(
            form_frame,
            text="Действующая скидка (%):",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG
        ).pack(anchor="w", pady=(10, 5))
        
        self.discount_var = tk.StringVar()
        self.discount_var.set(str(discount) if discount is not None else "0")
        
        self.fields["discount"] = tk.Entry(
            form_frame,
            textvariable=self.discount_var,
            font=(FONT_FAMILY, FONT_SIZE),
            width=15
        )
        self.fields["discount"].pack(anchor="w")
        
        tk.Label(
            form_frame,
            text="💡 Число от 0 до 100",
            font=(FONT_FAMILY, FONT_SIZE - 2),
            bg=COLOR_MAIN_BG,
            fg="gray"
        ).pack(anchor="w")
        
        # === Описание ===
        tk.Label(
            form_frame,
            text="Описание товара:",
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG
        ).pack(anchor="w", pady=(10, 5))
        
        self.fields["description"] = tk.Text(
            form_frame,
            font=(FONT_FAMILY, FONT_SIZE),
            height=4,
            width=50
        )
        if description:
            self.fields["description"].insert("1.0", description)
        self.fields["description"].pack(fill=tk.X)
        
        # === Кнопки ===
        btn_frame = tk.Frame(form_frame, bg=COLOR_MAIN_BG)
        btn_frame.pack(pady=20)
        
        save_btn = tk.Button(
            btn_frame,
            text="💾 Сохранить изменения",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.save_changes
        )
        save_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="Отмена",
            font=(FONT_FAMILY, FONT_SIZE),
            command=self.on_closing
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        print("\n✅ Форма создана")


    def load_current_image(self, image_path):
        """Загрузить текущее изображение товара"""
        try:
            if image_path:
                img_path = self.resources_path / image_path
                if img_path.exists():
                    img = Image.open(img_path)
                    img = img.resize((300, 200), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    self.photo_label = tk.Label(
                        self.photo_container,
                        image=photo,
                        bg="#F0F0F0"
                    )
                    self.photo_label.image = photo
                    self.photo_label.pack(fill=tk.BOTH, expand=True)
                    
                    self.selected_image_path = image_path
                    return
            
            # Если фото нет или ошибка — показываем заглушку
            self.photo_label = tk.Label(
                self.photo_container,
                text="Нет фото\n(будет использована заглушка)",
                font=(FONT_FAMILY, FONT_SIZE - 1),
                bg="#F0F0F0",
                fg="gray",
                justify=tk.CENTER
            )
            self.photo_label.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            print(f"Ошибка загрузки фото: {e}")
            self.photo_label = tk.Label(
                self.photo_container,
                text="Ошибка загрузки фото",
                font=(FONT_FAMILY, FONT_SIZE - 1),
                bg="#F0F0F0",
                fg="red",
                justify=tk.CENTER
            )
            self.photo_label.pack(fill=tk.BOTH, expand=True)
    
    def upload_photo(self):
        """Загрузить новое фото (удалить старое)"""
        file_path = filedialog.askopenfilename(
            title="Выберите новое фото товара",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png"),
                ("Все файлы", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # Открываем и изменяем размер
            img = Image.open(file_path)
            img = img.resize((300, 200), Image.Resampling.LANCZOS)
            
            # Генерируем имя файла (оставляем тот же ID)
            ext = Path(file_path).suffix.lower()
            new_filename = f"{self.product_id}{ext}"
            save_path = self.resources_path / new_filename
            
            # Удаляем старое фото, если оно есть и отличается
            if self.original_image_path:
                old_path = self.resources_path / self.original_image_path
                if old_path.exists() and old_path != save_path:
                    try:
                        os.remove(old_path)
                        print(f"✅ Старое фото удалено: {old_path}")
                    except Exception as e:
                        print(f"⚠️ Не удалось удалить старое фото: {e}")
            
            # Сохраняем новое
            img.save(save_path)
            
            # Отображаем
            photo = ImageTk.PhotoImage(img)
            
            # Очищаем контейнер
            for widget in self.photo_container.winfo_children():
                widget.destroy()
            
            self.photo_label = tk.Label(
                self.photo_container,
                image=photo,
                bg="#F0F0F0"
            )
            self.photo_label.image = photo
            self.photo_label.pack(fill=tk.BOTH, expand=True)
            
            self.selected_image_path = new_filename
            self.original_image_path = new_filename  # Обновляем оригинал
            
            messagebox.showinfo(
                "Фото обновлено",
                f"Фото успешно заменено на:\n{new_filename}\n\n"
                f"Старое фото удалено.\n"
                f"Размер изменён на 300x200 пикселей.",
                icon=messagebox.INFO
            )
            
        except Exception as e:
            messagebox.showerror(
                "Ошибка загрузки фото",
                f"Не удалось загрузить фото:\n{str(e)}\n\n"
                "Проверьте формат файла (JPG, PNG) и повторите попытку.",
                icon=messagebox.ERROR
            )
    
    def clear_photo(self):
        """Удалить фото"""
        if messagebox.askyesno(
            "Удаление фото",
            "Удалить фото товара?\n\n"
            "При сохранении изменений фото будет удалено из базы и папки.",
            icon=messagebox.QUESTION
        ):
            # Удаляем файл
            if self.original_image_path:
                old_path = self.resources_path / self.original_image_path
                if old_path.exists():
                    try:
                        os.remove(old_path)
                        print(f"✅ Фото удалено: {old_path}")
                    except Exception as e:
                        print(f"⚠️ Не удалось удалить файл: {e}")
            
            # Очищаем отображение
            for widget in self.photo_container.winfo_children():
                widget.destroy()
            
            self.photo_label = tk.Label(
                self.photo_container,
                text="Нет фото\n(будет использована заглушка)",
                font=(FONT_FAMILY, FONT_SIZE - 1),
                bg="#F0F0F0",
                fg="gray",
                justify=tk.CENTER
            )
            self.photo_label.pack(fill=tk.BOTH, expand=True)
            
            self.selected_image_path = ""
            self.original_image_path = None
    
    def _create_field(self, parent, field_name, label_text, width=20, required=False, default="", tooltip=""):
        """Создать поле ввода"""
        tk.Label(
            parent,
            text=label_text,
            font=(FONT_FAMILY, FONT_SIZE),
            bg=COLOR_MAIN_BG
        ).pack(anchor="w", pady=(10, 5))
        
        entry = tk.Entry(parent, font=(FONT_FAMILY, FONT_SIZE), width=width)
        entry.pack(anchor="w")
        
        if default:
            entry.insert(0, str(default))
        
        self.fields[field_name] = entry
        
        if tooltip:
            tk.Label(
                parent,
                text="💡 " + tooltip,
                font=(FONT_FAMILY, FONT_SIZE - 2),
                bg=COLOR_MAIN_BG,
                fg="gray"
            ).pack(anchor="w")
    
    def validate_form(self):
        """Проверить корректность данных"""
        errors = []
        
        # Наименование
        name = self.fields["name"].get().strip()
        if not name:
            errors.append("❌ Наименование товара обязательно.")
        
        # Артикул
        article = self.fields["article"].get().strip()
        if not article:
            errors.append("❌ Артикул обязателен.")
        
        # Категория
        category = self.fields["category"].get().strip()
        if not category:
            errors.append("❌ Категория обязательна.")
        
        # Производитель
        manufacturer = self.fields["manufacturer"].get().strip()
        if not manufacturer:
            errors.append("❌ Производитель обязателен.")
        
        # Поставщик
        supplier = self.fields["supplier"].get().strip()
        if not supplier:
            errors.append("❌ Поставщик обязателен.")
        
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
            errors.append("❌ Цена должна быть числом.")
        
        # Количество
        try:
            quantity = int(self.quantity_var.get().strip())
            if quantity < 0:
                errors.append("❌ Количество не может быть отрицательным!")
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
            error_text = "Обнаружены ошибки:\n\n" + "\n".join(errors) + "\n\n" \
                        "Исправьте ошибки и попробуйте снова."
            messagebox.showerror("Ошибка валидации", error_text, icon=messagebox.ERROR)
            return False
        
        return True
    
    def save_changes(self):
        """Сохранить изменения"""
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
                "image_path": self.selected_image_path if self.selected_image_path is not None else self.original_image_path or ""
            }
            
            # Обновляем в БД
            update_product(self.product_id, data)
            
            messagebox.showinfo(
                "Успех",
                f"Товар '{data['name']}' успешно обновлён!\n\n"
                f"Артикул: {data['article']}",
                icon=messagebox.INFO
            )
            
            self.root.destroy()
            
            if self.on_close:
                self.on_close()
                
        except Exception as e:
            messagebox.showerror(
                "Ошибка при сохранении",
                f"Не удалось сохранить изменения:\n{str(e)}\n\n"
                "Проверьте данные и повторите попытку.",
                icon=messagebox.ERROR
            )
    
    def on_closing(self):
        """Обработчик закрытия"""
        if messagebox.askyesno(
            "Отмена редактирования",
            "Отменить редактирование?\n\nВсе несохранённые изменения будут потеряны.",
            icon=messagebox.QUESTION
        ):
            self.root.destroy()
            if self.on_close:
                self.on_close()

    def on_mousewheel(self, event):
        """Прокрутка там, где находится курсор мыши"""
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        
        if widget and widget.winfo_toplevel() == self.root:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
