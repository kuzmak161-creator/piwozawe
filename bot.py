import telebot
import random
import os
import threading
from telebot import types

#НАСТРОЙКA 
TOKEN = os.getenv('BOT_TOKEN')
DB_FILE = "users.txt"
bot = telebot.TeleBot(TOKEN)

# Функция для записи ID в базу
def save_user(chat_id):
    chat_id = str(chat_id)
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f: f.write("")
    with open(DB_FILE, "r") as f:
        existing_users = f.read().splitlines()
    if chat_id not in existing_users:
        with open(DB_FILE, "a") as f:
            f.write(chat_id + "\n")

def add_easter_egg_point(user_id, word):
    user_id = str(user_id) 
    word = word.lower()
    user_data = {}
    
    if os.path.exists("stats.txt"):
        with open("stats.txt", "r") as f:
            for line in f:
                if ":" in line:
                    uid, words_str = line.strip().split(":", 1)
                    user_data[uid] = words_str.split(",") if words_str else []

    found_words = user_data.get(user_id, [])
    if word not in found_words:
        found_words.append(word)
        user_data[user_id] = found_words
        with open("stats.txt", "w") as f:
            for uid, words in user_data.items():
                f.write(f"{uid}:{','.join(words)}\n")
        return True 
    return False

#КОМАНДЫ

@bot.message_handler(commands=['start'])
def welcome(message):
    save_user(message.chat.id)
    bot.reply_to(message, "привет я пивозаврбот! напиши пивасик или /pivo , чтобы проверить насколько ты пиво. А если хочешь проверить насколько ты сухарик то напиши сухарики или /suhariki.")

@bot.message_handler(commands=['anus_anus_1'])
def secret_subscribe(message):
    save_user(message.chat.id)
    bot.reply_to(message, "✅ Доступ подтвержден. Ты в системе.")

@bot.message_handler(commands=['pivo'])
def pivo_command(message):pivas_test(message)

@bot.message_handler(commands=['suhariki'])
def suhariki_command(message):
    suhariki_logic(message)

@bot.message_handler(func=lambda message: message.text.lower() == "сухарики")
def suhariki_text(message):
    suhariki_logic(message)

@bot.message_handler(commands=['my_stats'])
def show_stats(message):
    user_id = str(message.from_user.id)
    count = 0
    if os.path.exists("stats.txt"):
        with open("stats.txt", "r") as f:
            for line in f:
                if line.startswith(user_id + ":"):
                    _, words_str = line.strip().split(":", 1)
                    count = len(words_str.split(",")) if words_str else 0
                    break
    bot.reply_to(message, f"🏆 Твои достижения:\nНайдено уникальных пасхалок: {count} из 7.")

#РАССЫЛКА
@bot.message_handler(func=lambda message: message.text.lower().startswith("рассылка"))
def mass_send(message):
    try:
        parts = message.text.split(" ", 2)
        if len(parts) < 3: return
        pin, text_to_send = parts[1], parts[2]
        if pin == os.getenv('BROADCAST_PIN'):
            with open(DB_FILE, "r") as f:
                users = f.read().splitlines()
            count = 0
            for user_id in users:
                try: 
                    bot.send_message(user_id, text_to_send)
                    count += 1
                except: continue
            bot.reply_to(message, f"✅ Рассылка завершена!\nОтправлено {count} пивозаврам.")
    except: pass

#ПАСХАЛКИ
@bot.message_handler(func=lambda message: any(word in message.text.lower() for word in ["пиздец", "папа мух", "даня", "кириешки", "флинт", "г99", "g99"]))
def common_easter_eggs(message):
    save_user(message.chat.id)
    user_name = message.from_user.first_name
    text_lower = message.text.lower()
    user_id = message.from_user.id
    
    trigger_words = ["пиздец", "папа мух", "даня", "кириешки", "флинт", "г99", "g99", ]
    
    
    found_word = next((w for w in trigger_words if w in text_lower), None)

    if found_word:
       
        is_new = add_easter_egg_point(user_id, found_word)
        
        if is_new:
            bot.send_message(message.chat.id, f"🌟 {user_name}, ты открыл НОВУЮ пасхалку: «{found_word}»!")

        
        if any(word in found_word for word in ["кириешки", "флинт", "g99"]):
            bot.send_message(message.chat.id, f"🥨 Опа, {user_name}, секрет раскрыт!")
            bot.send_message(message.chat.id, "Награда: на 100% ты состоишь из сухариков, твой титул — Мега сухарик! 🥖")
        else:
            bot.send_message(message.chat.id, f"Поздравляю, {user_name}, вы нашли пасхалку!")
            bot.send_message(message.chat.id, "Награда: на 100% ты состоишь из пивасика, твой титул бог хмеля ! 🍺")

            if "пиздец" in found_word:
                bot.send_message(message.chat.id, "[Еще одна награда](https://youtu.be/bTkIdiG0QmQ?si=6BA-xCjpJ1uFUH1I)",
                                 parse_mode='Markdown', disable_web_page_preview=True)

# Функция для чтения ввода из терминала
def terminal_broadcast():
    print("--- Консоль рассылки активна. Введи текст и нажми Enter ---")
    while True:
        text_to_send = input("Рассылка > ")
        if text_to_send:
            if not os.path.exists(DB_FILE):
                print("❌ База пользователей пуста.")
                continue
                
            with open(DB_FILE, "r") as f:
                users = f.read().splitlines()
            
            print(f"🚀 Начинаю рассылку на {len(users)} чел...")
            count = 0
            for user_id in users:
                try:
                    bot.send_message(user_id, text_to_send)
                    count += 1
                except:
                    continue
            print(f"✅ Готово! Доставлено: {count}")

# Запускаем поток консоли.
threading.Thread(target=terminal_broadcast, daemon=True).start()

#РАНДОМ
@bot.message_handler(func=lambda message: message.text.lower() == "пивасик")
def pivas_test(message):
    save_user(message.chat.id)
    percent = random.randint(1, 100)
    if percent == 37: title = "Егор Котлетов"
    elif percent < 10: title = "лох"
    elif percent < 20: title = "гопникчек"
    elif percent < 30: title = "Любитель светлого"
    elif percent < 50: title = "любитель охоты крепкой" 
    elif percent < 70: title = "практически пивозавр"
    elif percent < 80: title = "пивозавр"
    elif percent < 99: title = "батя"
    else: title = "бог хмеля"
    
    bot.reply_to(message, f"📊 Ты состоишь из пивасика на {percent}%\nТвой титул: {title} 🍺")

def suhariki_logic(message):
    save_user(message.chat.id)
    percent = random.randint(1, 100)
    
    if percent <= 10: title = "нахлебник"
    elif percent <= 30: title = "начинающий"
    elif percent <= 50: title = "сухаречок"
    elif percent <= 70: title = "сухари"
    elif percent <= 85: title = "сухарище"
    else: title = "Мега сухарик"
    
    bot.reply_to(message, f"🥨 Ты состоишь из сухариков на {percent}%\n🏆 Твой титул: {title}")

@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/') and message.chat.type == 'private')
def unknown_command(message):
    save_user(message.chat.id)
    from datetime import datetime
    
    user_name = message.from_user.first_name 
    
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    bot.reply_to(message, f"{user_name}, ты не нашёл пасхалку, но теперь будешь знать который час на данный момент\n🕐 {now} .")

print("Бот запущен...")
bot.infinity_polling()
