import os
import torch
import clip
from PIL import Image as PILImage

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy_garden.mapview import MapView, MapMarker
from kivy.uix.filechooser import FileChooserIconView, FileChooserListView
from kivy.uix.dropdown import DropDown

# === CLIP загрузка ===
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)


class BaseScreen(Screen):
    """Базовый экран с фоном"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = RelativeLayout()

        # Фон
        self.bg = Image(source="background.jpg", allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.bg)

        self.content = BoxLayout(
            orientation='vertical',
            padding=20,
            spacing=15,
            size_hint=(0.9, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.layout.add_widget(self.content)
        self.add_widget(self.layout)


class MainScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.content.add_widget(Label(
            text="Миска добра-добро начинается с вас!",
            font_size=30,
            bold=True,
            color=(1, 1, 1, 1)
        ))

        buttons = [
            ("Карта контейнеров", self.go_to_map),
            ("Проверка еды", self.go_to_food),
        ]

        for text, action in buttons:
            btn = Button(
                text=text,
                background_color=(0.2, 0.6, 0.2, 1),
                color=(1, 1, 1, 1),
                font_size=18,
                size_hint=(1, None),
                height=50
            )
            btn.bind(on_press=action)
            self.content.add_widget(btn)

    def go_to_map(self, instance):
        self.manager.current = "map"

    def go_to_food(self, instance):
        self.manager.current = "food"


class MapScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.content.add_widget(Label(text="🗺 Карта контейнеров", font_size=22, bold=True))

        self.map_view = MapView(zoom=14, lat=53.2835, lon=69.3969)
        self.content.add_widget(self.map_view)

        self.add_markers()

        self.content.add_widget(Button(
            text="⬅ Назад",
            background_color=(0.2, 0.6, 0.2, 1),
            on_press=self.go_back
        ))

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


class FoodScreen(BaseScreen):
    """Экран проверки еды через CLIP"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.header = Label(text="Проверка еды", font_size=22, bold=True)
        self.content.add_widget(self.header)

        # Кнопка выбора картинки
        self.upload_btn = Button(
            text="Загрузить фото",
            background_color=(0.2, 0.6, 0.8, 1),
            font_size=18,
            size_hint=(1, None),
            height=50
        )
        self.upload_btn.bind(on_press=self.open_filechooser)
        self.content.add_widget(self.upload_btn)

        # Для вывода картинки
        self.food_img = Image(size_hint=(1, 0.6))
        self.content.add_widget(self.food_img)

        # Текст результата
        self.result_label = Label(
            text="Здесь появится результат",
            font_size=18,
            color=(1, 1, 1, 1)
        )
        self.content.add_widget(self.result_label)

        # Назад
        self.back_btn = Button(
            text="⬅ Назад",
            background_color=(0.2, 0.6, 0.2, 1),
            on_press=self.go_back
        )
        self.content.add_widget(self.back_btn)

    def open_filechooser(self, instance):
        """Открывает диалог выбора файла с доступом к Рабочему столу и Загрузкам"""
        self.content.clear_widgets()
        self.content.add_widget(Label(text="📂 Выберите фото", font_size=20, bold=True))

        user_home = os.path.expanduser("~")
        self.paths = {
            "Проект": ".",
            "Рабочий стол": os.path.join(user_home, "Desktop"),
            "Загрузки": os.path.join(user_home, "Downloads")
        }

        # Выпадающий список для выбора директории
        self.dropdown = DropDown()
        for name, path in self.paths.items():
            btn = Button(text=name, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: self.change_directory(btn.text))
            self.dropdown.add_widget(btn)

        main_button = Button(text="Выбрать папку", size_hint=(1, None), height=40)
        main_button.bind(on_release=self.dropdown.open)
        self.content.add_widget(main_button)

        # Файловый выбор
        self.filechooser = FileChooserIconView(
            path=".",
            filters=["*.png", "*.jpg", "*.jpeg"],
            size_hint=(1, 0.8)
        )
        self.filechooser.bind(on_submit=self.selected_file)
        self.content.add_widget(self.filechooser)

        # Кнопки управления
        controls = BoxLayout(size_hint=(1, None), height=50, spacing=10)
        open_btn = Button(text="Открыть", background_color=(0.2, 0.6, 0.8, 1))
        open_btn.bind(on_press=lambda x: self.selected_file(None, self.filechooser.selection, None))
        cancel_btn = Button(text="Отмена", background_color=(0.6, 0.2, 0.2, 1))
        cancel_btn.bind(on_press=lambda x: self.reset_ui())
        controls.add_widget(open_btn)
        controls.add_widget(cancel_btn)

        self.content.add_widget(controls)

    def change_directory(self, name):
        """Смена директории в файловом менеджере"""
        if name in self.paths:
            self.filechooser.path = self.paths[name]
        self.dropdown.dismiss()

    def selected_file(self, filechooser, selection, touch):
        if selection:
            file_path = selection[0]
            self.food_img.source = file_path
            self.analyze_image(file_path)
            self.reset_ui()

    def reset_ui(self):
        """Восстановить стандартный UI"""
        self.content.clear_widgets()
        self.content.add_widget(self.header)
        self.content.add_widget(self.upload_btn)
        self.content.add_widget(self.food_img)
        self.content.add_widget(self.result_label)
        self.content.add_widget(self.back_btn)

    def analyze_image(self, file_path):
        image = preprocess(PILImage.open(file_path)).unsqueeze(0).to(device)

        text_descriptions = [
            "not food",
            "fresh food",
            "edible food",
            "tasty food",
            "rotten food",
            "food with mold"
        ]
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
            result_text = "Это вообще не еда!"

        self.result_label.text = f"CLIP считает: {best_label}\n\n{result_text}"

    def go_back(self, instance):
        self.manager.current = "main"


class EcoCityApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(MapScreen(name="map"))
        sm.add_widget(FoodScreen(name="food"))  # 👈 новый экран
        return sm


if __name__ == "__main__":
    EcoCityApp().run()
