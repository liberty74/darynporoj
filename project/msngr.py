import os
import hashlib
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

# === Работа с пользователями ===
def init_file():
    if not os.path.exists('users.txt'):
        with open('users.txt', 'w'):
            pass

def add_user(login: str, password: str) -> bool:
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
    with open('users.txt', 'r') as f:
        users = f.read().splitlines()
    for user in users:
        args = user.split(':')
        if login == args[0] and password == args[1]:
            return True
    return False

init_file()

# === Хранилище текущего пользователя ===
class UserData:
    login = None

# === Экран авторизации ===
class AuthScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text="Вход / Регистрация", font_size=26))
        
        self.login_input = TextInput(hint_text="Логин", multiline=False, size_hint=(1, None), height=40)
        self.password_input = TextInput(hint_text="Пароль", multiline=False, password=True, size_hint=(1, None), height=40)
        layout.add_widget(self.login_input)
        layout.add_widget(self.password_input)

        btns = BoxLayout(size_hint=(1, None), height=50, spacing=10)
        login_btn = Button(text="Войти", background_color=(0.2, 0.6, 0.2, 1))
        reg_btn = Button(text="Регистрация", background_color=(0.2, 0.6, 0.8, 1))
        login_btn.bind(on_press=self.login)
        reg_btn.bind(on_press=self.register)
        btns.add_widget(login_btn)
        btns.add_widget(reg_btn)
        layout.add_widget(btns)

        self.message = Label(text="", font_size=16)
        layout.add_widget(self.message)

        self.add_widget(layout)

    def login(self, instance):
        login = self.login_input.text.strip()
        password = hashlib.sha256(self.password_input.text.strip().encode()).hexdigest()
        if get_user(login, password):
            UserData.login = login
            self.manager.current = "chat"
        else:
            self.message.text = "Неверный логин или пароль!"

    def register(self, instance):
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

# === Экран чата ===
class ChatScreen(Screen):
    messages = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.scroll = ScrollView(size_hint=(1, 0.8))
        self.chat_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.chat_box.bind(minimum_height=self.chat_box.setter('height'))
        self.scroll.add_widget(self.chat_box)
        self.layout.add_widget(self.scroll)

        self.input_box = BoxLayout(size_hint=(1, 0.1), spacing=10)
        self.msg_input = TextInput(multiline=False)
        self.send_btn = Button(text="Отправить", size_hint=(0.2, 1))
        self.send_btn.bind(on_press=self.send_message)
        self.input_box.add_widget(self.msg_input)
        self.input_box.add_widget(self.send_btn)
        self.layout.add_widget(self.input_box)

        self.logout_btn = Button(text="Выйти", size_hint=(1, 0.1), background_color=(0.6, 0.2, 0.2, 1))
        self.logout_btn.bind(on_press=self.logout)
        self.layout.add_widget(self.logout_btn)

        self.add_widget(self.layout)

    def send_message(self, instance):
        msg = self.msg_input.text.strip()
        if msg:
            full_msg = f"{UserData.login}: {msg}"
            ChatScreen.messages.append(full_msg)
            self.update_chat()
            self.msg_input.text = ""

    def update_chat(self):
        self.chat_box.clear_widgets()
        for msg in ChatScreen.messages:
            self.chat_box.add_widget(Label(text=msg, size_hint_y=None, height=30))

    def logout(self, instance):
        UserData.login = None
        self.manager.current = "auth"

# === Запуск приложения ===
class MessengerApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(AuthScreen(name="auth"))
        sm.add_widget(ChatScreen(name="chat"))
        sm.current = "auth"
        return sm

if __name__ == "__main__":
    MessengerApp().run()
