from telebot import TeleBot
from database import get_db
from handlers.auth import get_user_role
from keyboards import admin_menu, main_reply

def register_admin_handlers(bot: TeleBot, log):

    def deny(chat_id: int):
        bot.send_message(chat_id, "❌ Доступ заборонено.")

    @bot.message_handler(commands=["admin"])
    def admin(message):
        role = get_user_role(message.chat.id)
        if role != "admin":
            return deny(message.chat.id)
        bot.send_message(message.chat.id, "✅ Адмін-панель", reply_markup=admin_menu())

    @bot.message_handler(commands=["add_item"])
    def add_item(message):
        role = get_user_role(message.chat.id)
        if role != "admin":
            return deny(message.chat.id)

        bot.send_message(message.chat.id, "Введіть товар у форматі:\nНазва | Ціна | Опис")
        bot.register_next_step_handler(message, save_item)

    def save_item(message):
        role = get_user_role(message.chat.id)
        if role != "admin":
            return deny(message.chat.id)

        raw = (message.text or "").strip()
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) != 3:
            bot.send_message(message.chat.id, "❌ Формат невірний. Приклад:\nМонтаж ролика | 1200 | Монтаж 1 хв відео")
            return

        name, price_str, desc = parts
        try:
            price = float(price_str.replace(",", "."))
            if price <= 0:
                raise ValueError()
        except:
            bot.send_message(message.chat.id, "❌ Ціна має бути додатнім числом.")
            return

        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO products(name, price, description) VALUES(?,?,?)", (name, price, desc))
        db.commit()
        db.close()

        log.info(f"admin add_item by {message.chat.id}: {name} {price}")
        bot.send_message(message.chat.id, "✅ Товар додано.")

    @bot.message_handler(commands=["remove_item"])
    def remove_item(message):
        role = get_user_role(message.chat.id)
        if role != "admin":
            return deny(message.chat.id)

        bot.send_message(message.chat.id, "Введіть ID товару для видалення:")
        bot.register_next_step_handler(message, do_remove_item)

    def do_remove_item(message):
        role = get_user_role(message.chat.id)
        if role != "admin":
            return deny(message.chat.id)

        try:
            pid = int((message.text or "").strip())
        except:
            bot.send_message(message.chat.id, "❌ Введіть число (ID).")
            return

        db = get_db()
        cur = db.cursor()
        cur.execute("DELETE FROM products WHERE id=?", (pid,))
        db.commit()
        deleted = cur.rowcount
        db.close()

        bot.send_message(message.chat.id, "✅ Видалено." if deleted else "⚠️ Товар з таким ID не знайдено.")

    @bot.message_handler(commands=["orders"])
    def orders(message):
        role = get_user_role(message.chat.id)
        if role != "admin":
            return deny(message.chat.id)

        db = get_db()
        cur = db.cursor()
        cur.execute("""
            SELECT o.id, o.user_chat, p.name, p.price, o.qty, o.status, o.created_at
            FROM orders o
            JOIN products p ON p.id = o.product_id
            ORDER BY o.id DESC
            LIMIT 20
        """)
        rows = cur.fetchall()
        db.close()

        if not rows:
            bot.send_message(message.chat.id, "Замовлень поки немає.")
            return

        for r in rows:
            oid, uchat, pname, price, qty, status, created = r
            bot.send_message(
                message.chat.id,
                f"🧾 #{oid} | {status}\n"
                f"Користувач: {uchat}\n"
                f"Товар: {pname} ({price} грн) x{qty}\n"
                f"Час: {created}"
            )

    # ---------- Вихід з адмін-панелі ----------
    @bot.message_handler(func=lambda m: m.text == "🚪 Вийти з адмін-панелі")
    def exit_admin(message):
        role = get_user_role(message.chat.id)
        if role != "admin":
            bot.send_message(message.chat.id, "❌ Ви не адміністратор.")
            return

        log.info(f"admin exit | chat_id={message.chat.id}")

        bot.send_message(
            message.chat.id,
            "🚪 Ви вийшли з адмін-панелі.",
            reply_markup=main_reply()
        )