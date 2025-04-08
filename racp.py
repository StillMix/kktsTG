import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Пример URL вашего сервера для получения расписания
SCHEDULE_API_URL = "http://127.0.0.1:8000/lesson/"

# Функция для получения расписания с сервера
def fetch_schedule():
    try:
        response = requests.get(SCHEDULE_API_URL)
        if response.status_code == 200:
            data = response.json()
            return data['session']  # Предполагается, что сервер возвращает данные в поле 'lessons'
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при подключении к серверу: {e}")
        return None
