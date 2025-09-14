import tkinter as tk
from tkinter import filedialog
from PIL import Image
import torch
import clip

# Загружаем модель CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Функция обработки изображения
def analyze_image():
    # Выбираем файл
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
    if not file_path:
        return
    
    # Загружаем и обрабатываем изображение
    image = preprocess(Image.open(file_path)).unsqueeze(0).to(device)
    
    # Список текстовых описаний
    text_descriptions = [
        "not food",
        "fresh food",
        "edible food",
        "tasty food",
        "rotten food",
        "food with mold"
    ]
    text_tokens = clip.tokenize(text_descriptions).to(device)
    
    # Получаем сходство
    with torch.no_grad():
        image_features = model.encode_image(image)
        text_features = model.encode_text(text_tokens)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        similarity = (image_features @ text_features.T).squeeze(0)
    
    # Находим наиболее подходящее описание
    best_idx = similarity.argmax().item()
    best_label = text_descriptions[best_idx]

    # Сначала выводим, что думает CLIP
    clip_text = f"CLIP считает, что это: {best_label}\n"

    # Потом даём решение
    if "fresh" in best_label or "edible" in best_label or "tasty" in best_label:
        result_text = "✅ Эту еду можно есть!"
    elif "rotten" in best_label or "mold" in best_label:
        result_text = "❌ Эту еду есть нельзя!"
    else:
        result_text = "🚫 Это вообще не еда!"

    # Выводим всё вместе
    result_label.config(text=clip_text + result_text)

# Создаем окно Tkinter
root = tk.Tk()
root.title("Food Safety Checker")

# Кнопка для выбора и анализа изображения
btn = tk.Button(root, text="Загрузить фото еды", command=analyze_image, font=("Arial", 12))
btn.pack(pady=20)

# Место для вывода результата
result_label = tk.Label(root, text="", font=("Arial", 16), justify="center")
result_label.pack(pady=20)

root.mainloop()
