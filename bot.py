from telebot import TeleBot
from config import TOKEN
from database import init_db
from logger import setup_logger

from handlers.user import register_user_handlers
from handlers.admin import register_admin_handlers
from handlers.callbacks import register_callbacks
from handlers.payments import register_payment_handlers

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is empty. Set env var BOT_TOKEN")

    log = setup_logger()
    bot = TeleBot(TOKEN)

    init_db()

    register_user_handlers(bot, log)
    register_admin_handlers(bot, log)
    register_callbacks(bot, log)
    register_payment_handlers(bot, log)

    log.info("Bot started")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    main()
