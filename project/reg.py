import os
import torch
import clip
import hashlib
from PIL import Image as PILImage

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.relativelayout import RelativeLayout
from kivy_garden.mapview import MapView, MapMarker
from kivy.uix.filechooser import FileChooserIconView

# === Загружаем CLIP-модель для анализа изображений ===
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# === Глобальная переменная текущего пользователя ===
current_user = {
    "login": None,
    "avatar": "avatar.png",  # аватарка по умолчанию
    "points": 0
}

# === Работа с пользователями (регистрация и вход) ===
def init_file():
    """Создаёт файл users.txt, если его нет"""
    if not os.path.exists('users.txt'):
        with open('users.txt', 'w'):
            pass

def add_user(login: str, password: str) -> bool:
    """Добавляет пользователя в файл"""
    with open('users.txt', 'r') as f:
        users = f.read().splitlines()

    for user in users:
        args = user.split(':')
        if login == args[0]:
            return False
    with open('users.txt', 'a') as f:
        f.write(f'{login}:{password}\n')
    return True

def get_user(login: str, password: str) -> bool:
    """Проверяет логин и пароль пользователя"""
    with open('users.txt', 'r') as f:
        users = f.read().splitlines()
    for user in users:
        args = user.split(':')
        if login == args[0] and password == args[1]:
            return True
    return False

init_file()

# === Базовый экран с фоном ===
class BaseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = RelativeLayout()

        # Фон
        self.bg = Image(source="background.jpg", allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.bg)

        # Контейнер
        self.content = BoxLayout(
            orientation='vertical',
            padding=20,
            spacing=15,
            size_hint=(0.9, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.layout.add_widget(self.content)
        self.add_widget(self.layout)

# === Экран авторизации ===
class AuthScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.content.add_widget(Label(text="Вход / Регистрация",
                                      font_size=26, bold=True, color=(1, 1, 1, 1)))

        self.login_input = TextInput(hint_text="Логин", multiline=False,
                                     size_hint=(1, None), height=40)
        self.password_input = TextInput(hint_text="Пароль", multiline=False,
                                        password=True, size_hint=(1, None), height=40)
        self.content.add_widget(self.login_input)
        self.content.add_widget(self.password_input)

        btns = BoxLayout(size_hint=(1, None), height=50, spacing=10)
        login_btn = Button(text="Войти", background_color=(0.2, 0.6, 0.2, 1))
        reg_btn = Button(text="Регистрация", background_color=(0.2, 0.6, 0.8, 1))
        login_btn.bind(on_press=self.login)
        reg_btn.bind(on_press=self.register)
        btns.add_widget(login_btn)
        btns.add_widget(reg_btn)
        self.content.add_widget(btns)

        self.message = Label(text="", color=(1, 1, 1, 1), font_size=16)
        self.content.add_widget(self.message)

    def login(self, instance):
        """Вход"""
        login = self.login_input.text.strip()
        password = hashlib.sha256(self.password_input.text.strip().encode()).hexdigest()

        if get_user(login, password):
            global current_user
            current_user["login"] = login
            current_user["points"] = 0
            self.manager.current = "main"
        else:
            self.message.text = "Неверный логин или пароль!"

    def register(self, instance):
        """Регистрация"""
        login = self.login_input.text.strip()
        password = self.password_input.text.strip()

        if not login or not password:
            self.message.text = "Введите логин и пароль!"
            return

        password_hashed = hashlib.sha256(password.encode()).hexdigest()
        if add_user(login, password_hashed):
            self.message.text = "Регистрация успешна! Теперь войдите."
        else:
            self.message.text = "Пользователь уже существует!"

# === Главный экран ===
class MainScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Заголовок
        self.content.add_widget(Label(text="Миска добра - добро начинается с вас!",
                                      font_size=30, bold=True, color=(1, 1, 1, 1)))

        # Блок профиля в правом верхнем углу
        self.profile_layout = BoxLayout(orientation="horizontal", spacing=10,
                                        size_hint=(None, None), height=60, width=250,
                                        pos_hint={"right": 0.98, "top": 0.98})
        self.avatar = Image(source=current_user["avatar"], size_hint=(None, None), size=(50, 50))
        self.user_info = Label(text=f"{current_user['login']}\nБаллы: {current_user['points']}",
                               color=(1, 1, 1, 1), font_size=14, halign="left", valign="middle")
        self.profile_layout.add_widget(self.avatar)
        self.profile_layout.add_widget(self.user_info)
        self.layout.add_widget(self.profile_layout)

        # Кнопки
        buttons = [
            ("Карта контейнеров", self.go_to_map),
            ("Проверка еды", self.go_to_food),
        ]
        for text, action in buttons:
            btn = Button(text=text, background_color=(0.2, 0.6, 0.2, 1),
                         color=(1, 1, 1, 1), font_size=18, size_hint=(1, None), height=50)
            btn.bind(on_press=action)
            self.content.add_widget(btn)

    def on_pre_enter(self, *args):
        """Обновляем данные профиля при заходе на экран"""
        self.user_info.text = f"{current_user['login']}\nБаллы: {current_user['points']}"
        self.avatar.source = current_user["avatar"]

    def go_to_map(self, instance):
        self.manager.current = "map"

    def go_to_food(self, instance):
        self.manager.current = "food"

# === Экран карты ===
class MapScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.content.add_widget(Label(text="Карта контейнеров", font_size=22, bold=True))

        self.map_view = MapView(zoom=14, lat=53.2835, lon=69.3969)
        self.content.add_widget(self.map_view)
        self.add_markers()

        self.content.add_widget(Button(text="Назад", background_color=(0.2, 0.6, 0.2, 1),
                                       on_press=self.go_back))

    def add_markers(self):
        locations = [
            {"lat": 53.2835, "lon": 69.3969, "icon": "cache/eco_bin_icon.jpg"},
            {"lat": 53.2821, "lon": 69.3897, "icon": "cache/eco_bin_icon.jpg"},
            {"lat": 53.2940, "lon": 69.4048, "icon": "cache/eco_bin_icon.jpg"},
        ]
        for loc in locations:
            marker = MapMarker(lat=loc["lat"], lon=loc["lon"], source=loc["icon"])
            self.map_view.add_widget(marker)

    def go_back(self, instance):
        self.manager.current = "main"

# === Экран проверки еды ===
class FoodScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.header = Label(text="Проверка еды", font_size=22, bold=True)
        self.content.add_widget(self.header)

        self.upload_btn = Button(text="Загрузить фото", background_color=(0.2, 0.6, 0.8, 1),
                                 font_size=18, size_hint=(1, None), height=50)
        self.upload_btn.bind(on_press=self.open_filechooser)
        self.content.add_widget(self.upload_btn)

        self.food_img = Image(size_hint=(1, 0.6))
        self.content.add_widget(self.food_img)

        self.result_label = Label(text="Здесь появится результат", font_size=18, color=(1, 1, 1, 1))
        self.content.add_widget(self.result_label)

        self.back_btn = Button(text="Назад", background_color=(0.2, 0.6, 0.2, 1), on_press=self.go_back)
        self.content.add_widget(self.back_btn)

    def open_filechooser(self, instance):
        self.content.clear_widgets()
        self.content.add_widget(Label(text="Выберите фото", font_size=20, bold=True))

        self.filechooser = FileChooserIconView(path=".", filters=["*.png", "*.jpg", "*.jpeg"], size_hint=(1, 0.8))
        self.filechooser.bind(on_submit=self.selected_file)
        self.content.add_widget(self.filechooser)

        controls = BoxLayout(size_hint=(1, None), height=50, spacing=10)
        open_btn = Button(text="Открыть", background_color=(0.2, 0.6, 0.8, 1))
        open_btn.bind(on_press=lambda x: self.selected_file(None, self.filechooser.selection, None))
        cancel_btn = Button(text="Отмена", background_color=(0.6, 0.2, 0.2, 1))
        cancel_btn.bind(on_press=lambda x: self.reset_ui())
        controls.add_widget(open_btn)
        controls.add_widget(cancel_btn)
        self.content.add_widget(controls)

    def selected_file(self, filechooser, selection, touch):
        if selection:
            file_path = selection[0]
            self.food_img.source = file_path
            self.analyze_image(file_path)
            self.reset_ui()

    def reset_ui(self):
        self.content.clear_widgets()
        self.content.add_widget(self.header)
        self.content.add_widget(self.upload_btn)
        self.content.add_widget(self.food_img)
        self.content.add_widget(self.result_label)
        self.content.add_widget(self.back_btn)

    def analyze_image(self, file_path):
        image = preprocess(PILImage.open(file_path)).unsqueeze(0).to(device)
        text_descriptions = ["not food", "fresh food", "edible food", "tasty food", "rotten food", "food with mold"]
        text_tokens = clip.tokenize(text_descriptions).to(device)

        with torch.no_grad():
            image_features = model.encode_image(image)
            text_features = model.encode_text(text_tokens)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            similarity = (image_features @ text_features.T).squeeze(0)

        best_idx = similarity.argmax().item()
        best_label = text_descriptions[best_idx]

        if "fresh" in best_label or "edible" in best_label or "tasty" in best_label:
            result_text = "Эту еду можно есть!"
        elif "rotten" in best_label or "mold" in best_label:
            result_text = "Эту еду есть нельзя!"
        else:
            result_text = "Это не еда!"

        self.result_label.text = f"CLIP считает: {best_label}\n\n{result_text}"

    def go_back(self, instance):
        self.manager.current = "main"

# === Запуск приложения ===
class EcoCityApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(AuthScreen(name="auth"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(MapScreen(name="map"))
        sm.add_widget(FoodScreen(name="food"))
        sm.current = "auth"
        return sm

if __name__ == "__main__":
    EcoCityApp().run()
