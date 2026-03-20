
import telebot
from telebot import types
import datetime

TOKEN = "8712446245:AAEXS7fjGWQqHiUmBljEM7GXmRNlA60sbpE"
ADMIN_ID = 6102437732
QR_FILE_ID = "AgACAgIAAxkBAAOQablujGlEzd0a5HYF0r-QLbY1KL8AAq4UaxusC8FJKsSCDqO4Qy0BAAMCAAN5AAM6BA"

bot = telebot.TeleBot(TOKEN)
pending = {}         # {chat_id: сумма с комиссией}
waiting_check = {}   # {chat_id: True} — ждём ввод чека

# ===== Главное меню =====
def main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row('💰 Купить OPEX', '💵 Продать OPEX')
    m.row('🆘 Поддержка')
    return m

# ===== Меню сумм с комиссией =====
def amount_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row('200 (220)', '500 (550)')
    m.row('1000 (1100)', 'Другая сумма')
    m.row('🔙 Назад')
    return m

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == '🔙 Назад')
def back(message):
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == '🆘 Поддержка')
def support(message):
    bot.send_message(message.chat.id, "Если есть вопросы или проблемы, пишите администратору: @Kana78kgkg")

@bot.message_handler(func=lambda m: m.text == '💵 Продать OPEX')
def sell(message):
    bot.send_message(message.chat.id, "Функция продажи скоро будет доступна")

# ===== Купить =====
@bot.message_handler(func=lambda m: m.text == '💰 Купить OPEX')
def buy(message):
    bot.send_message(message.chat.id, "Выберите сумму:", reply_markup=amount_menu())

# ===== Быстрые суммы =====
@bot.message_handler(func=lambda m: '(' in m.text)
def fast_amount(message):
    chat_id = message.chat.id
    amount = int(message.text.split('(')[0].strip())
    total = round(amount * 1.10, 2)
    pending[chat_id] = total

    confirm = types.ReplyKeyboardMarkup(resize_keyboard=True)
    confirm.row('📸 Отправил скрин')
    confirm.row('🔙 Назад')

    bot.send_photo(chat_id, QR_FILE_ID,
                   caption=f"💰 Вы выбрали {amount}\nК оплате с комиссией: {total}\n\nОтправьте скрин оплаты и нажмите '📸 Отправил скрин'",
                   reply_markup=confirm)

# ===== Другая сумма =====
@bot.message_handler(func=lambda m: m.text == 'Другая сумма')
def other_amount(message):
    msg = bot.send_message(message.chat.id, "Введите вашу сумму:")
    bot.register_next_step_handler(msg, process_custom_amount)

# ===== Обработка введённой суммы =====
def process_custom_amount(message):
    chat_id = message.chat.id
    if not message.text.isdigit():
        bot.send_message(chat_id, "Ошибка! Введите только цифры.")
        return
    amount = int(message.text)
    total = round(amount * 1.10, 2)
    pending[chat_id] = total

    confirm = types.ReplyKeyboardMarkup(resize_keyboard=True)
    confirm.row('📸 Отправил скрин')
    confirm.row('🔙 Назад')

    bot.send_photo(chat_id, QR_FILE_ID,
                   caption=f"💰 Вы выбрали {amount}\nК оплате с комиссией: {total}\n\nОтправьте скрин оплаты и нажмите '📸 Отправил скрин'",
                   reply_markup=confirm)

# ===== Клиент нажал "Отправил скрин" =====
@bot.message_handler(func=lambda m: m.text == '📸 Отправил скрин')
def confirm_payment(message):
    chat_id = message.chat.id
    amount = pending.get(chat_id, "неизвестно")

    bot.send_message(chat_id, "✅ Скрин получен, ожидайте подтверждения")
    now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    user = message.from_user
    name = user.first_name
    username = f"@{user.username}" if user.username else "нет"

    # кнопка подтверждения для админа
    markup = types.InlineKeyboardMarkup()
    confirm_btn = types.InlineKeyboardButton("✅ Подтвердить чек", callback_data=f"confirm_{chat_id}")
    markup.add(confirm_btn)

    caption = (
        f"📌 ЗАЯВКА\n"
        f"ID: {chat_id}\n"
        f"Имя: {name}\n"
        f"Username: {username}\n"
        f"Сумма к оплате: {amount}\n"
        f"Время: {now}"
    )

    bot.send_message(ADMIN_ID, caption, reply_markup=markup)

# ===== Кнопка подтверждения чека =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def approve_check(call):
    if call.from_user.id != ADMIN_ID:
        return
    user_id = int(call.data.split("_")[1])
    waiting_check[user_id] = True
    bot.send_message(ADMIN_ID, f"Введите номер чека для клиента {user_id}:")

# ===== Ввод номера чека =====
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def send_check_auto(message):
    check = message.text.strip()
    if not check or not waiting_check:
        return

    user_id = list(waiting_check.keys())[0]
    amount = pending.get(user_id, "неизвестно")

    bot.send_message(user_id,
                     f"✅ Оплата подтверждена\nOPEX успешно куплен\nСумма к оплате: {amount}\n📄 Чек: {check}\nСпасибо за покупку!")

    pending.pop(user_id, None)
    waiting_check.pop(user_id)
    bot.send_message(ADMIN_ID, f"✅ Чек {check} отправлен клиенту {user_id}")

bot.infinity_polling()
