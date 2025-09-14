from transformers import pipeline

# Загружаем предобученную модель (маленькая GPT-2, чтобы быстрее работала)
generator = pipeline("text-generation", model="distilgpt2")

def ai_bot_reply(user_text):
    # Генерация текста
    response = generator(
        f"Вопрос: {user_text}\nОтвет про экологию:",
        max_length=80,
        num_return_sequences=1,
        do_sample=True,
        temperature=0.7
    )
    return response[0]["generated_text"]

# Проверка работы
if __name__ == "__main__":
    print("Eco-бот запущен! (напиши 'выход' чтобы завершить)")
    while True:
        q = input("Ты: ")
        if q.lower() in ["выход", "exit", "quit"]:
            break
        print("Eco-бот:", ai_bot_reply(q))
