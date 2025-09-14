from PIL import Image

# Путь к исходной фотографии
input_path = "me1.jpg"  # замените на вашу фотку
# Путь для сохранения сжатой фотографии
output_path = "output_image_40x40.png"

# Открываем изображение
img = Image.open(input_path)

# Сжимаем до 40x40 с современным методом ресэмплинга
img_resized = img.resize((400, 400), Image.Resampling.LANCZOS)

# Сохраняем
img_resized.save(output_path)

print(f"Фотка успешно сжата до 40x40 и сохранена как {output_path}")
