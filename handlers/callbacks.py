from telebot import TeleBot
from database import get_db
from keyboards import confirm_order, pay_inline


def register_callbacks(bot: TeleBot, log):

    @bot.callback_query_handler(func=lambda c: True)
    def callbacks(call):

        # ---------- Перегляд товару ----------
        if call.data.startswith("product:"):
            pid = int(call.data.split(":")[1])
            log.info(f"product view | chat_id={call.message.chat.id} | pid={pid}")

            db = get_db()
            cur = db.cursor()
            cur.execute(
                "SELECT id, name, price, description FROM products WHERE id=?",
                (pid,)
            )
            p = cur.fetchone()
            db.close()

            if not p:
                log.warning(f"product not found | pid={pid}")
                bot.send_message(call.message.chat.id, "❌ Товар не знайдено.")
                return

            bot.send_message(
                call.message.chat.id,
                f"🎬 {p[1]}\n💰 {p[2]} грн\n📝 {p[3]}",
                reply_markup=confirm_order(p[0])
            )

        # ---------- Створення замовлення ----------
        elif call.data.startswith("order:"):
            pid = int(call.data.split(":")[1])
            chat_id = call.message.chat.id

            db = get_db()
            cur = db.cursor()
            cur.execute(
                "INSERT INTO orders (user_chat, product_id, status) VALUES (?, ?, 'new')",
                (chat_id, pid)
            )
            oid = cur.lastrowid
            db.commit()
            db.close()

            log.info(f"order created | chat_id={chat_id} | order_id={oid} | pid={pid}")

            bot.send_message(
                chat_id,
                f"✅ Замовлення створено (#{oid}).\n"
                f"Натисніть «Оплатити» або використайте команду /pay",
                reply_markup=pay_inline(oid)
            )

        # ---------- Скасування ----------
        elif call.data == "cancel":
            log.info(f"order cancel | chat_id={call.message.chat.id}")
            bot.send_message(call.message.chat.id, "❌ Дію скасовано.")
