from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import json

USER_DATA_FILE = 'user_data.json'

# Функция для загрузки данных о пользователях из файла
def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Функция для сохранения данных о пользователях в файл
def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

async def about_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет информацию о пользователе, если он авторизован."""
    chat_id = update.message.chat_id

    # Загружаем данные о пользователях из файла
    user_data = load_user_data()

    # Проверяем, есть ли информация о пользователе
    if str(chat_id) in user_data:  # Преобразуем chat_id в строку для сравнения с ключом в файле
        user_info = user_data[str(chat_id)]  # Делаем так же и здесь
        role = user_info.get('role', 'Нет данных')
        if role == 'teacher':
            role = 'Преподаватель'
        elif role == 'user':
            role = 'Студент'
        
        # Создаем клавиатуру с кнопками "Обо мне" и "Выйти"
        keyboard = [
            [KeyboardButton("Обо мне")],
            [KeyboardButton("Выйти")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)

        text = (
            f"👤 *Ваши данные:*\n"
            f"🔹 *Имя:* {user_info.get('fullname', 'Нет данных')}\n"
            f"🔹 *Логин:* {user_info.get('login', 'Нет данных')}\n"
            f"🔹 *Роль:* {role}\n"
            f"🔹 *Email:* {user_info.get('gmail', 'Нет данных')}\n"
            f"🔹 *Группа:* {user_info.get('group', 'Не назначена')}\n"
            f"🔹 *VK:* {user_info.get('vk', 'Нет данных')}"

        )
       
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    
    else:
        await update.message.reply_text("Вы не авторизованы! Введите /start для авторизации.")

async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет данные о пользователе при нажатии на кнопку 'Выйти'."""
    chat_id = update.message.chat_id

    # Загружаем данные о пользователях из файла
    user_data = load_user_data()

    # Проверяем, есть ли информация о пользователе
    if str(chat_id) in user_data:
        # Удаляем данные о пользователе
        del user_data[str(chat_id)]

        # Сохраняем обновленные данные в файл
        save_user_data(user_data)

        # Отправляем сообщение пользователю, что он успешно вышел
        await update.message.reply_text("Вы успешно вышли. Ваши данные удалены.")
        
        # Отправляем кнопки для неавторизованного пользователя
        keyboard = [
            [KeyboardButton("Авторизоваться")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("Для авторизации нажмите кнопку ниже.", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Вы не авторизованы!")
