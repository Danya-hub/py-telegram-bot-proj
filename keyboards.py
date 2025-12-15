from telebot import types


# ---------- Головне меню користувача ----------
def main_reply():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📦 Каталог", "ℹ️ Про бота")
    kb.row("🛒 Як замовити?", "📝 Залишити відгук")
    kb.row("📞 Контакти", "❓ Допомога")
    return kb


# ---------- Передача номера телефону ----------
def share_phone_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📞 Поділитися номером телефону", request_contact=True))
    kb.add(types.KeyboardButton("✍️ Ввести номер вручну"))
    return kb


# ---------- Меню адміністратора ----------
def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("/add_item", "/remove_item")
    kb.row("/orders", "/catalog")
    kb.row("🚪 Вийти з адмін-панелі")
    return kb


# ---------- Інлайн-каталог ----------
def catalog_inline(products):
    kb = types.InlineKeyboardMarkup()
    for p in products:
        kb.add(
            types.InlineKeyboardButton(
                f"🎬 {p[1]} — {p[2]} грн",
                callback_data=f"product:{p[0]}"
            )
        )
    return kb


# ---------- Підтвердження замовлення ----------
def confirm_order(product_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Підтвердити", callback_data=f"order:{product_id}"),
        types.InlineKeyboardButton("❌ Скасувати", callback_data="cancel")
    )
    return kb


# ---------- Оплата ----------
def pay_inline(order_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 Оплатити", callback_data=f"pay:{order_id}"))
    kb.add(types.InlineKeyboardButton("❌ Скасувати", callback_data="cancel"))
    return kb
