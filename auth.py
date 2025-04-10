import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import json

USER_DATA_FILE = 'user_data.json'
user_data = {}

# Состояния
LOGIN, PASSWORD = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)  # Преобразуем в строку для корректного сравнения
    load_user_data()  # Загружаем актуальные данные

    if chat_id in user_data:
        await update.message.reply_text("✅ Вы уже авторизованы!")
        
        # Показываем кнопки "Обо мне" и "Выйти"
        keyboard = [
            [KeyboardButton("Следить за обновлениями расписания")],
            [KeyboardButton("Обо мне")],
            [KeyboardButton("Выйти")]
        ]
    else:
        await update.message.reply_text("🔐 Вам нужно авторизоваться.")
        
        # Показываем кнопку "Авторизоваться"
        keyboard = [
            [KeyboardButton("Авторизоваться")]
        ]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Загружаем данные пользователей из файла
def load_user_data():
    global user_data
    try:
        with open(USER_DATA_FILE, 'r') as f:
            user_data = json.load(f)
    except FileNotFoundError:
        user_data = {}

# Сохраняем данные пользователей в файл
def save_user_data():
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(user_data, f, indent=4)

# Функция для обработки команды /start
async def start_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Введите ваш логин:")
    return LOGIN

# Функция для получения логина
async def get_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.chat_id] = {'login': update.message.text}
    await update.message.reply_text("Введите ваш пароль:")
    return PASSWORD

# Функция для получения пароля и отправки данных на сервер
async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.message.chat_id]['password'] = update.message.text

    login = user_data[update.message.chat_id]['login']
    password = user_data[update.message.chat_id]['password']

    # Отправка данных на сервер с использованием JSON
    headers = {'Content-Type': 'application/json'}
    json_data = {
        'login': login,
        'password': password
    }
    
    try:
        response = requests.post('http://127.0.0.1:8000/auth/login', json=json_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            if access_token:
                # Храним всю информацию о пользователе
                user_data[update.message.chat_id].update({
                    'role': data.get('role'),
                    'fullname': data.get('fullname'),
                    'name': data.get('name'),
                    'gmail': data.get('gmail'),
                    'login': data.get('login'),
                    'vk': data.get('vk'),
                    'group': data.get('group'),
                    'id': data.get('id'),
                })

                # Сохраняем данные о пользователе в файл
                save_user_data()

                # Извлекаем имя из fullname
                fullname = data.get('fullname', '').strip()
                name_parts = fullname.split()
                name = name_parts[1] if len(name_parts) > 1 else name_parts[0]

                # Создаем клавиатуру с кнопками "Обо мне" и "Выйти"
                keyboard = [
                    [KeyboardButton("Следить за обновлениями расписания")],
                    [KeyboardButton("Обо мне")],
                    [KeyboardButton("Выйти")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

                # Отправляем сообщение с клавиатурой
                await update.message.reply_text(f"Вы успешно авторизованы, {name}!", reply_markup=reply_markup)
            else:
                await update.message.reply_text("Не удалось получить токен.")
        else:
            await update.message.reply_text(f"Ошибка при отправке данных: {response.status_code}")
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Ошибка при подключении к серверу: {str(e)}")
    
    return ConversationHandler.END

# Функция для отмены процесса
async def cancel_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Процесс был отменен.")
    return ConversationHandler.END
