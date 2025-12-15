from telebot import TeleBot, types
from config import PAYMENTS_PROVIDER_TOKEN, CURRENCY
from database import get_db

def register_payment_handlers(bot: TeleBot, log):

    # 1) Команда /pay (оплатить последнее новое/ожидающее)
    @bot.message_handler(commands=["pay"])
    def pay_cmd(message):
        if not PAYMENTS_PROVIDER_TOKEN:
            bot.send_message(message.chat.id, "❌ Оплата не налаштована (немає provider token).")
            return

        # берем последнее "awaiting_payment" или "new"
        db = get_db()
        cur = db.cursor()
        cur.execute("""
            SELECT o.id, p.name, p.price, o.qty
            FROM orders o
            JOIN products p ON p.id = o.product_id
            WHERE o.user_chat=? AND o.status IN ('new','awaiting_payment')
            ORDER BY o.id DESC
            LIMIT 1
        """, (message.chat.id,))
        row = cur.fetchone()
        db.close()

        if not row:
            bot.send_message(message.chat.id, "У вас немає замовлень для оплати. Спочатку оформіть замовлення в каталозі.")
            return

        order_id, name, price, qty = row
        send_invoice(bot, message.chat.id, order_id, name, price, qty, log)


    # 2) Callback "pay:ORDER_ID"
    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("pay:"))
    def pay_callback(call):
        if not PAYMENTS_PROVIDER_TOKEN:
            bot.send_message(call.message.chat.id, "❌ Оплата не налаштована (немає provider token).")
            return

        order_id = int(call.data.split(":")[1])

        db = get_db()
        cur = db.cursor()
        cur.execute("""
            SELECT o.id, p.name, p.price, o.qty, o.user_chat
            FROM orders o
            JOIN products p ON p.id = o.product_id
            WHERE o.id=?
        """, (order_id,))
        row = cur.fetchone()
        db.close()

        if not row:
            bot.send_message(call.message.chat.id, "⚠️ Замовлення не знайдено.")
            return

        oid, name, price, qty, user_chat = row
        if user_chat != call.message.chat.id:
            bot.send_message(call.message.chat.id, "❌ Це не ваше замовлення.")
            return

        send_invoice(bot, call.message.chat.id, oid, name, price, qty, log)


    # 3) Pre-checkout (обязательно!)
    @bot.pre_checkout_query_handler(func=lambda q: True)
    def pre_checkout(pre_checkout_query):
        # Здесь можно проверить payload/заказ, наличие в БД и т.д.
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


    # 4) Успешная оплата
    @bot.message_handler(content_types=["successful_payment"])
    def got_payment(message):
        sp = message.successful_payment
        payload = sp.invoice_payload  # например "order:123"

        log.info(f"PAYMENT success chat={message.chat.id} payload={payload} amount={sp.total_amount} {sp.currency}")

        order_id = None
        if payload.startswith("order:"):
            try:
                order_id = int(payload.split(":")[1])
            except:
                order_id = None

        # сохраняем платеж + меняем статус заказа
        db = get_db()
        cur = db.cursor()

        if order_id is not None:
            cur.execute("UPDATE orders SET status='paid' WHERE id=? AND user_chat=?",
                        (order_id, message.chat.id))

            cur.execute("""
                INSERT INTO payments(order_id, user_chat, total_amount, currency,
                                     provider_payment_charge_id, telegram_payment_charge_id, status)
                VALUES(?,?,?,?,?,?, 'paid')
            """, (
                order_id,
                message.chat.id,
                sp.total_amount,
                sp.currency,
                sp.provider_payment_charge_id,
                sp.telegram_payment_charge_id
            ))

        db.commit()
        db.close()

        bot.send_message(
            message.chat.id,
            "✅ Оплата успішна! Дякуємо 🙏\n"
            "Наш менеджер зв’яжеться з вами щодо виконання замовлення."
        )


def send_invoice(bot: TeleBot, chat_id: int, order_id: int, name: str, price: float, qty: int, log):
    # Telegram ожидает цену в минимальных единицах:
    # UAH -> копейки => *100
    total = int(round(price * 100)) * int(qty)

    prices = [
        types.LabeledPrice(label=f"{name} (x{qty})", amount=total)
    ]

    # Можно добавить доставку/скидки отдельными позициями
    # prices.append(types.LabeledPrice(label="Доставка", amount=5000))

    bot.send_invoice(
        chat_id=chat_id,
        title="Оплата замовлення",
        description=f"Замовлення #{order_id}: {name} x{qty}",
        invoice_payload=f"order:{order_id}",
        provider_token=PAYMENTS_PROVIDER_TOKEN,
        currency=CURRENCY,
        prices=prices,
        start_parameter="video_shop_pay",
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False
    )

    # обновим статус заказа на awaiting_payment
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE orders SET status='awaiting_payment' WHERE id=? AND user_chat=?",
                (order_id, chat_id))
    db.commit()
    db.close()

    log.info(f"INVOICE sent chat={chat_id} order={order_id} total={total} {CURRENCY}")
