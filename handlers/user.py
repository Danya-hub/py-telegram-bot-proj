from telebot import TeleBot, types
from database import get_db
from keyboards import main_reply, share_phone_kb, catalog_inline
from handlers.auth import get_user_role, is_valid_phone
from config import ADMINS


def register_user_handlers(bot: TeleBot, log):

    def send_instructions(chat_id: int):
        bot.send_message(
            chat_id,
            "🤖 Я бот-магазин відеопродукції.\n"
            "Можу показати каталог, прийняти замовлення та відгуки.",
            reply_markup=main_reply()
        )

    # ---------- /start ----------
    @bot.message_handler(commands=["start"])
    def start(message):
        log.info(f"/start | chat_id={message.chat.id}")
        role = get_user_role(message.chat.id)

        if role is None:
            bot.send_message(
                message.chat.id,
                "👋 Для початку роботи поділіться номером телефону:",
                reply_markup=share_phone_kb()
            )
        else:
            send_instructions(message.chat.id)

    # ---------- /help ----------
    @bot.message_handler(commands=["help"])
    def help_cmd(message):
        log.info(f"/help | chat_id={message.chat.id}")
        bot.send_message(
            message.chat.id,
            "/start — почати\n"
            "/catalog — каталог\n"
            "/info — про бота\n"
            "/feedback — відгук\n"
            "/order — надіслати замовлення адміну"
        )

    # ---------- /info ----------
    @bot.message_handler(commands=["info"])
    def info(message):
        log.info(f"/info | chat_id={message.chat.id}")
        bot.send_message(
            message.chat.id,
            "ℹ️ Telegram-бот для замовлення відеопродукції."
        )

    # ---------- /hello ----------
    @bot.message_handler(commands=["hello"])
    def hello(message):
        log.info(f"/hello | chat_id={message.chat.id}")
        bot.send_message(message.chat.id, "Привіт! 👋", reply_markup=main_reply())

    # ---------- Контакт (телефон) ----------
    @bot.message_handler(content_types=["contact"])
    def save_contact(message):
        phone = message.contact.phone_number.replace(" ", "").replace("-", "")
        log.info(f"contact | chat_id={message.chat.id} | phone={phone}")

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO users(chat_id, phone) VALUES(?,?)",
            (message.chat.id, phone)
        )
        db.commit()
        db.close()

        bot.send_message(
            message.chat.id,
            "✅ Авторизація успішна!",
            reply_markup=main_reply()
        )

    # ---------- Ручний ввід телефону ----------
    @bot.message_handler(func=lambda m: m.text == "✍️ Ввести номер вручну")
    def ask_phone_text(message):
        log.info(f"manual phone request | chat_id={message.chat.id}")
        bot.send_message(message.chat.id, "Введіть номер у форматі +380XXXXXXXXX:")
        bot.register_next_step_handler(message, save_phone_text)

    def save_phone_text(message):
        phone = message.text.strip().replace(" ", "").replace("-", "")
        if not is_valid_phone(phone):
            log.warning(f"invalid phone | chat_id={message.chat.id} | {phone}")
            bot.send_message(message.chat.id, "❌ Некоректний номер.")
            return

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO users(chat_id, phone) VALUES(?,?)",
            (message.chat.id, phone)
        )
        db.commit()
        db.close()

        log.info(f"phone saved | chat_id={message.chat.id}")
        bot.send_message(message.chat.id, "✅ Номер збережено!", reply_markup=main_reply())

    # ---------- /catalog ----------
    def show_catalog(chat_id):
        log.info(f"catalog view | chat_id={chat_id}")
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id, name, price, description FROM products")
        products = cur.fetchall()
        db.close()

        if not products:
            bot.send_message(chat_id, "Каталог порожній.")
        else:
            bot.send_message(chat_id, "📦 Каталог:", reply_markup=catalog_inline(products))

    @bot.message_handler(commands=["catalog"])
    def catalog_cmd(message):
        show_catalog(message.chat.id)

    @bot.message_handler(func=lambda m: m.text == "📦 Каталог")
    def catalog_btn(message):
        show_catalog(message.chat.id)

    # ---------- /feedback ----------
    @bot.message_handler(commands=["feedback"])
    def feedback_cmd(message):
        log.info(f"feedback start | chat_id={message.chat.id}")
        bot.send_message(message.chat.id, "✍️ Напишіть ваш відгук:")
        bot.register_next_step_handler(message, save_feedback)

    @bot.message_handler(func=lambda m: m.text == "📝 Залишити відгук")
    def feedback_btn(message):
        log.info(f"feedback btn | chat_id={message.chat.id}")
        bot.send_message(message.chat.id, "✍️ Напишіть ваш відгук:")
        bot.register_next_step_handler(message, save_feedback)

    def save_feedback(message):
        text = message.text.strip()
        log.info(f"feedback saved | chat_id={message.chat.id}")

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO feedback(user_chat, text) VALUES(?,?)",
            (message.chat.id, text)
        )
        db.commit()
        db.close()

        for admin in ADMINS:
            bot.send_message(admin, f"📝 Відгук від {message.chat.id}:\n{text}")

        bot.send_message(message.chat.id, "🙏 Дякуємо за відгук!", reply_markup=main_reply())

    @bot.message_handler(func=lambda m: m.text == "🛒 Як замовити?")
    def how_to_order(message):
        log.info(f"how_to_order | chat_id={message.chat.id}")
        bot.send_message(
            message.chat.id,
            "🛒 Як зробити замовлення:\n\n"
            "1️⃣ Натисніть «📦 Каталог»\n"
            "2️⃣ Оберіть товар зі списку\n"
            "3️⃣ Натисніть «✅ Підтвердити»\n"
            "4️⃣ Оплатіть замовлення кнопкою «💳 Оплатити»\n\n"
            "Після оплати менеджер зв’яжеться з вами.",
            reply_markup=main_reply()
        )

    @bot.message_handler(func=lambda m: m.text == "❓ Допомога")
    def help_btn(message):
        log.info(f"help button | chat_id={message.chat.id}")
        bot.send_message(
            message.chat.id,
            "❓ Допомога:\n\n"
            "📦 Каталог — перегляд товарів\n"
            "🛒 Як замовити? — інструкція\n"
            "📝 Залишити відгук — надіслати відгук\n"
            "📞 Контакти — наші контакти\n\n"
            "Також доступні команди:\n"
            "/catalog /info /feedback /order",
            reply_markup=main_reply()
        )