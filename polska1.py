import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command


ADMIN_IDS = [5429733148]



def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()


init_db()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ Ошибка: Токен не найден!")
    print("Проверьте:")
    print("1. Переменную TELEGRAM_BOT_TOKEN в Railway")
    print("2. Файл .env (если тестируете локально)")
    exit(1)

router = Router()


def add_user_to_db(user_id: int):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


def get_users_count():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Обрати опцію")]],
        resize_keyboard=True
    )


@router.message(F.text == "/start")
async def start_command(message: types.Message):
    add_user_to_db(message.from_user.id)

    welcome_text = (
        "Вітаю! Цей бот допоможе вам отримати студентські документи в Польщі.\n\n"
        "Оберіть опцію нижче:"
    )
    await message.answer(welcome_text, reply_markup=get_reply_keyboard())


@router.message(Command("broadcast"))
async def broadcast_command(message: types.Message, bot: Bot):

    if message.from_user.id not in ADMIN_IDS:
        return


    args = message.text.split(' ', 1)
    if len(args) < 2:
        users_count = get_users_count()
        await message.answer(f"Использование: /broadcast <текст>\n\nВсего пользователей: {users_count}")
        return

    broadcast_text = args[1]
    users = get_all_users()

    if not users:
        await message.answer("В базе данных нет пользователей")
        return

    await message.answer(f"Начинаю рассылку для {len(users)} пользователей...")

    sent = 0
    failed = 0

    for user_id in users:
        try:
            await bot.send_message(user_id, broadcast_text)
            sent += 1
        except:
            failed += 1

        await asyncio.sleep(0.05)

    await message.answer(f"Рассылка завершена\nУспешно: {sent}\nНе удалось: {failed}")


@router.message(F.text == "Обрати опцію")
async def show_options(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Канал", url="https://t.me/status_studentappl")
    keyboard.button(text="Менеджер", url="https://t.me/Status_Studenta3")
    keyboard.button(text="Інстаграм", url="https://www.instagram.com/status_studenta_ua?igsh=dW5tMHBxeGZjejBt==")
    keyboard.button(text="Відгуки", callback_data="reviews")
    keyboard.button(text="Інфо", callback_data="info")
    keyboard.button(text="Ціни", callback_data="prices")
    keyboard.adjust(3, 2)
    await message.answer("Оберіть опцію:", reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "info")
async def info_callback(callback: types.CallbackQuery):
    image = FSInputFile("images/info.jpg") if os.path.exists("images/info.jpg") else None

    part1 = """
СКІЛЬКИ ЧАСУ ЗАЙМАЄ ВИГОТОВЛЕННЯ ДОКУМЕНТІВ І ТЕРМІН ЇХ ДІЇ?

🔹 Термін виготовлення:
Зазвичай до 14 днів, але в разі відсутності форс-мажорних обставин — 2-5 днів.

🔹 Термін дії документів:
– Поліцеальні школи: документи дійсні на семестр
Зимовий семестр: 01.09 - 31.01
Літній семестр: 01.02 - 31.08
"""

    part2 = """
– Університети: документи дійсні на семестр
Зимовий семестр: 01.10 - 28.02
Літній семестр: 01.03 - 30.09

Не важливо, чи замовили ви документи в листопаді або вересні, вони дійсні до кінця семестру.
"""

    part3 = """
ЯК ВІДБУВАЄТЬСЯ ОПЛАТА?

Ми працюємо по передоплаті 50%, решта — коли документи готові.
Щоб переконатися в нашій чесності, ви можете ознайомитись з нашими відгуками 
"""

    part4 = """
ЩО БУДЕ, ЯКЩО Я НЕ ЗАБЕРУ СВОЇ ДОКУМЕНТИ З ПАЧКОМАТУ InPost?

🔹 Це ваша відповідальність забрати документи.
🔹 Якщо документи не забрані вчасно, то ми не можемо повторно відправити їх безкоштовно.
🔹 У разі повторного запиту на документи:
– 150 зл за заświadczenie
– 250 зл за заświadczenie + легітимація
– +17 зл за доставку

Для замовлення пишіть @Status_Studenta3  

Ми працюємо для Вас
"""

    if image:
        await callback.message.answer_photo(image, caption=part1)
        await callback.message.answer(part2)
        await callback.message.answer(part3)
        await callback.message.answer(part4)
    else:
        await callback.message.answer(part1 + "\n" + part2 + "\n" + part3 + "\n" + part4)

    await callback.answer()


@router.callback_query(F.data == "reviews")
async def reviews_callback(callback: types.CallbackQuery):
    image = FSInputFile("images/reviews.jpg") if os.path.exists("images/reviews.jpg") else None
    caption = "✅ Відгуки / Отзывы ✅"
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔗 Перейти до відгуків", url="https://t.me/status_studenta_polska")

    if image:
        await callback.message.answer_photo(image, caption=caption, reply_markup=keyboard.as_markup())
    else:
        await callback.message.answer(caption, reply_markup=keyboard.as_markup())

    await callback.answer()


@router.callback_query(F.data == "prices")
async def prices_callback(callback: types.CallbackQuery):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Статус студента", callback_data="student_status")
    keyboard.button(text="Лікарняні", callback_data="hospital")
    keyboard.button(text="Медичні документи", callback_data="medical_docs")
    keyboard.adjust(1)
    await callback.message.answer("Виберіть розділ:", reply_markup=keyboard.as_markup())
    await callback.answer()


@router.callback_query(F.data == "student_status")
async def student_status_callback(callback: types.CallbackQuery):
    image = FSInputFile("images/status.jpg") if os.path.exists("images/status.jpg") else None
    text = """1️⃣ Довідка з вищого навчального закладу України без перекладу на польську мову - 300 зл 🔥

2️⃣ Довідка з вищого навчального закладу України з перекладом на польську мову - 400 зл 🔥

3️⃣ Довідка з польської поліцеальної школи, без легітимації - 600 зл або 700 зл 🔥

4️⃣ Довідка з польської поліцеальної школи з пластиковою легітимацією - 850 зл / 950 зл 🔥

5️⃣ Довідка з польського університету з пластиковою легітимацією - 1300 зл 🔥

‼️‼️‼️ВАЖЛИВО ‼️‼️‼️

✅ Ціна на польські довідки різна, тому що різні школи. Щоб дізнатись різницю між ними — пишіть у приват менеджеру 💖

📄 Легітимація — студентський квиток. За допомогою цього документу ви можете користуватись знижками у громадському транспорті 🤯, на залізничний транспорт 🚃, у музеї та інше.

▪️ Виготовлення від 1 до 3 днів у середньому."""

    if image:
        await callback.message.answer_photo(image, caption=text)
    else:
        await callback.message.answer(text)

    await callback.answer()


@router.callback_query(F.data == "hospital")
async def hospital_callback(callback: types.CallbackQuery):
    image = FSInputFile("images/hospital.jpg") if os.path.exists("images/hospital.jpg") else None
    text = """⚠️ Актуальна ціна на лікарняний:

▪️ 1 день — 70 злотих 🔥  
▪️ 2–3 дні — 100 злотих 🔥  
▪️ 4–5 днів — 130 злотих 🔥  
▪️ 6–10 днів — 200 злотих 🔥  
▪️ 11–14 днів — 250 злотих 🔥

Оформлення тільки для тих, хто працює на умові злеценя ‼️

📍 Термін виконання: від 1 години до 24 годин. Якщо замовлення в суботу чи неділю — виконується в понеділок.

‼️ Важлива інформація: оформлення лікарняних з повною оплатою, без виключень."""

    if image:
        await callback.message.answer_photo(image, caption=text)
    else:
        await callback.message.answer(text)

    await callback.answer()


@router.callback_query(F.data == "medical_docs")
async def medical_docs_callback(callback: types.CallbackQuery):
    image = FSInputFile("images/medical_docs.jpg") if os.path.exists("images/medical_docs.jpg") else None
    text = """🧐 Актуальні ціни на медичні документи:

💊 Комплект: Orzeczenie lekarskie + Książeczka sanepidowska + аналізи — 293 зл  
💊 Комплект: Orzeczenie lekarskie + Książeczka sanepidowska — 253 зл  
💊 Orzeczenie lekarskie (санітарно-епідеміологічне) — 185 зл  
💊 Orzeczenie lekarskie (попереднє обстеження до роботи) — 185 зл"""

    if image:
        await callback.message.answer_photo(image, caption=text)
    else:
        await callback.message.answer(text)

    await callback.answer()


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())