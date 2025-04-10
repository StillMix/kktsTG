import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import aiohttp
from datetime import datetime, timedelta
import websockets
import json
import asyncio

USER_DATA_FILE = 'user_data.json'

def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
# Пример URL вашего сервера для получения расписания
SCHEDULE_API_URL = "http://127.0.0.1:8000/lesson/"


async def fetch_teacher_name(teacher_id):
    if not teacher_id:
        return ""
    
    try:
        url = f"http://127.0.0.1:8000/teachers/{teacher_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Извлекаем fullname из правильного пути
                    name = data.get("user", {}).get("fullname")
                    if name:
                        return name
                    else:
                        print(f"⚠️ Учитель {teacher_id} найден, но fullname отсутствует в user: {data}")
                        return "Неизвестно"
                else:
                    print(f"❌ Ошибка при запросе к {url}: статус {resp.status}")
                    return "Неизвестно"
    except Exception as e:
        print(f"🚫 Ошибка при получении имени преподавателя ID {teacher_id}: {e}")
        return "Неизвестно"




async def listen_for_schedule_updates(user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE):
    uri = f"ws://127.0.0.1:8000/ws/{user_id}"
    try:
        async with websockets.connect(uri) as websocket:
            while True:
                message = await websocket.recv()
                print("Сообщение от сервера:", message)

                if message.startswith("newlesson:"):
                    # Обработка уведомлений для группы
                    group = message.split(":", 1)[1].strip()
                    chat_id = update.message.chat_id
                    user_data = load_user_data()

                    # Проверяем наличие данных пользователя
                    if str(chat_id) in user_data:
                        user_info = user_data[str(chat_id)]
                        role = user_info.get('role', 'Нет данных')

                        if user_info is None:
                            await update.message.reply_text("Не удалось найти ваши данные. Повторите попытку позже.")
                            return

                        if role == 'user':
                            user_group = user_info.get("group")

                    # Обрабатываем уведомление для группы
                    if role == 'user' and user_group == group:
                        await send_schedule(update, group)

                    # Обработка уведомлений для преподавателей
                elif message.startswith("newlessonteacher:"):
                        if role == 'teacher':
                            teacher_id = message.split(":", 1)[1].strip()
                            print('Учительский ИД:', str(user_info.get("id")), str(user_info.get("id")) == teacher_id)
                            if str(user_info.get("id")) == teacher_id:  # Это уведомление для данного преподавателя
                                await send_schedule(update, group, teacher_id)

                    # Обработка уведомлений для второго преподавателя
                elif message.startswith("newlessonteacher2:"):
                        if role == 'teacher':
                            print('Учительский23 ИД:', message.split(":", 1)[1].strip())
                            teacher2_id = message.split(":", 1)[1].strip()
                            if teacher2_id:
                                print('Учительский2 ИД:', str(user_info.get("id")), str(user_info.get("id")) == teacher2_id)
                                if str(user_info.get("id")) == teacher2_id:  # Это уведомление для второго преподавателя
                                    await send_schedule(update, group, teacher2_id)

    except Exception as e:
        print(f"Ошибка при подключении к WebSocket: {e}")

# Функция для отправки расписания
async def send_schedule(update, group, teacher_id=None):
    async with aiohttp.ClientSession() as session:
        async with session.get("http://127.0.0.1:8000/lesson/") as resp:
            if resp.status == 200:
                data = await resp.json()
                lessons = data.get("lessons", [])

                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")

                for day in lessons:
                    if day.get("date") == tomorrow:
                        await update.message.reply_text("Обновленное расписание на завтра:")
                        for lesson in day.get("sessions", []):
                            # Если это студент, фильтруем занятия по группе
                            if teacher_id is None and lesson.get("group") == group:
                                await send_lesson_details(update, lesson)
                            # Если это преподаватель, фильтруем занятия по ID преподавателя
                            elif teacher_id and (lesson.get("teacher") == teacher_id or lesson.get("teacher2") == teacher_id):
                                await send_lesson_details(update, lesson)

# Функция для отправки информации о занятии
async def send_lesson_details(update, lesson):
    teacher_name = await fetch_teacher_name(lesson["teacher"])
    teacher2_name = await fetch_teacher_name(lesson.get("teacher2"))

    text = (
        f"📚 {lesson['name']}\n"
        f"👥 Группа: {lesson['group']}\n"
        f"👨‍🏫 Преподаватель: {teacher_name}\n"
    )
    if teacher2_name:
        text += f"👩‍🏫 Второй преподаватель: {teacher2_name}\n"
    text += (
        f"🕒 Время: {lesson['start']} - {lesson['end']}\n"
        f"🏫 Аудитория: {lesson['clases']}\n"
        f"📍 Адрес: {lesson['adress']}\n"
    )

    await update.message.reply_text(text)

async def start_schedule_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_data = load_user_data()
    user_info = user_data[str(chat_id)]
    user_id = user_info.get('id', 'Нет данных')  # Предполагаем, что user_id сохранен в context.user_data после авторизации

    if not user_id:
        await update.message.reply_text("Ошибка: Не найден user_id.")
        return
    # Запускаем слушатель для WebSocket
    asyncio.create_task(listen_for_schedule_updates(user_id, update, context))