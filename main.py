from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
from auth import start, start_auth, get_login, get_password, cancel_auth, LOGIN, PASSWORD
from me import about_me, exit  # Подключаем обработчик выхода
from racp import start_schedule_updates
import json


USER_DATA_FILE = 'user_data.json'
def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}



# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Вы авторизованы. Подключение к расписанию...")
    await start_schedule_updates(update, context)

def main():
    token = '7815051059:AAFn6ptQCA3Gxu_EDJ48uKhFG6xDmNCt01M'

    application = Application.builder().token(token).build()

    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Обработчик авторизации (многошаговый)
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Авторизоваться$'), start_auth)],
        states={
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_login)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel_auth)],
    )

    # Добавляем обработчики
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Regex('^Следить за обновлениями расписания$'), start))
    application.add_handler(MessageHandler(filters.Regex('^Обо мне$'), about_me))
    application.add_handler(MessageHandler(filters.Regex('^Выйти$'), exit))

    application.run_polling()

if __name__ == '__main__':
    main()
