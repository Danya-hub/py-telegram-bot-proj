import re
from database import get_db
from config import ADMINS

PHONE_RE = re.compile(r"^\+?\d{10,15}$")

def is_valid_phone(phone: str) -> bool:
    phone = phone.replace(" ", "").replace("-", "")
    return bool(PHONE_RE.match(phone))

def get_user_role(chat_id: int):
    if chat_id in ADMINS:
        return "admin"

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT role FROM bot_users WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()
    if row:
        db.close()
        return row[0]  # admin/manager

    cur.execute("SELECT id FROM users WHERE chat_id=?", (chat_id,))
    user = cur.fetchone()
    db.close()
    return "user" if user else None
