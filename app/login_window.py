import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from pathlib import Path
from database import check_login
from main_window import MainWindow
from styles import COLOR_MAIN_BG, COLOR_ACTION, FONT_FAMILY, FONT_SIZE


class LoginWindow:
    def __init__(self, root):
        self.root = root

        # Путь к ресурсам
        self.resources_path = Path(__file__).parent.parent / "resources"

        # === УСТАНАВЛИВАЕМ ИКОНКУ ЧЕРЕЗ iconphoto (работает на Windows 10/11) ===
        self._set_icon(root)

        # Настройки окна
        self.root.title("Вход в систему - ООО «Обувь»")
        self.root.geometry("1400x800")
        self.root.configure(bg=COLOR_MAIN_BG)

        # === ЦЕНТРАЛЬНЫЙ КОНТЕЙНЕР ===
        center_frame = tk.Frame(root, bg=COLOR_MAIN_BG)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Логотип компании
        logo_img = self.load_logo((150, 150))
        if logo_img:
            logo_label = tk.Label(center_frame, image=logo_img, bg=COLOR_MAIN_BG)
            logo_label.image = logo_img
            logo_label.pack(pady=20)

        # Заголовок
        title = tk.Label(
            center_frame,
            text="ООО «Обувь»\nАвторизация",
            font=(FONT_FAMILY, 24, "bold"),
            bg=COLOR_MAIN_BG,
        )
        title.pack(pady=20)

        # Контейнер для полей ввода
        form_frame = tk.Frame(center_frame, bg=COLOR_MAIN_BG)
        form_frame.pack(pady=20)

        # Логин
        tk.Label(
            form_frame,
            text="Логин:",
            font=(FONT_FAMILY, FONT_SIZE + 2),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w")
        self.login_entry = tk.Entry(
            form_frame, font=(FONT_FAMILY, FONT_SIZE + 2), width=40
        )
        self.login_entry.pack(pady=5)

        self.login_entry.bind("<Key>", self.on_key_press)
        self.login_entry.bind("<Button-3>", self.show_context_menu)

        # Пароль
        tk.Label(
            form_frame,
            text="Пароль:",
            font=(FONT_FAMILY, FONT_SIZE + 2),
            bg=COLOR_MAIN_BG,
        ).pack(anchor="w", pady=(15, 5))
        self.password_entry = tk.Entry(
            form_frame, font=(FONT_FAMILY, FONT_SIZE + 2), width=40, show="*"
        )
        self.password_entry.pack(pady=5)

        self.password_entry.bind("<Key>", self.on_key_press)
        self.password_entry.bind("<Button-3>", self.show_context_menu)

        # Кнопки
        btn_frame = tk.Frame(center_frame, bg=COLOR_MAIN_BG)
        btn_frame.pack(pady=30)

        # Кнопка входа
        login_btn = tk.Button(
            btn_frame,
            text="Войти",
            font=(FONT_FAMILY, FONT_SIZE + 2, "bold"),
            background=COLOR_ACTION,
            fg="black",
            width=20,
            command=self.login,
        )
        login_btn.pack(pady=10)

        # Кнопка гостя
        guest_btn = tk.Button(
            btn_frame,
            text="Войти как гость",
            font=(FONT_FAMILY, FONT_SIZE + 2),
            width=20,
            command=self.enter_as_guest,
        )
        guest_btn.pack(pady=10)

    def _set_icon(self, root):
        """Установить иконку через iconphoto — ЕДИНСТВЕННЫЙ рабочий способ на Windows 10/11"""
        icon_path = self.resources_path / "Icon.png"

        if not icon_path.exists():
            print(f"⚠️ Иконка не найдена: {icon_path}")
            return

        try:
            img = Image.open(icon_path)
            # Важно: иконка должна быть 32x32 или 48x48 для Windows
            img = img.resize((48, 48), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)

            # Ключевой момент: устанавливаем иконку
            root.iconphoto(True, photo)

            # Сохраняем ссылку в атрибуте окна, чтобы GC не удалил!
            root._icon_photo = photo

            print(f"✅ Иконка установлена: {icon_path} (48x48)")
        except Exception as e:
            print(f"❌ Ошибка установки иконки: {e}")

    def load_logo(self, size=(150, 150)):
        """Загрузить логотип компании"""
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

    def on_key_press(self, event):
        """Перехват Ctrl+V"""
        if event.state & 0x0004 and event.keycode == 86:
            event.widget.event_generate("<<Paste>>")
            return "break"
        return None

    def show_context_menu(self, event):
        """Показать контекстное меню"""
        widget = event.widget
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(
            label="Вставить", command=lambda: widget.event_generate("<<Paste>>")
        )
        menu.add_command(label="Копировать", command=lambda: self._on_copy(widget))
        menu.add_command(
            label="Выделить всё", command=lambda: widget.event_generate("<<SelectAll>>")
        )
        menu.post(event.x_root, event.y_root)
        return "break"

    def _on_copy(self, widget):
        """Копировать выделенный текст"""
        try:
            text = widget.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)

        except Exception:
            pass

    def login(self):
        login = self.login_entry.get().strip()
        password = self.password_entry.get().strip()

        if not login or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль!")
            return

        user = check_login(login, password)

        if user:
            messagebox.showinfo("Успех", f"Добро пожаловать, {user['full_name']}!")
            self.root.destroy()
            self.open_main_window(user)
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль!")

    def enter_as_guest(self):
        guest_user = {"user_id": 0, "full_name": "Гость", "role": "guest"}
        self.root.destroy()
        self.open_main_window(guest_user)

    def open_main_window(self, user):
        """Открыть главное окно с товарами"""
        root = tk.Tk()
        root.mainloop()
