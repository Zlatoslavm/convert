import logging
import asyncio
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup

# --- НАСТРОЙКИ ---
API_TOKEN = '8640709725:AAHZ925vEUFI1qa2OWnWP8Nd1QL_grryS5I'
OWNER_ID = 8419332734  # СЮДА ВСТАВЬ СВОЙ ID ИЗ @userinfobot

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

storage = {}
admins = {OWNER_ID}


def parse_raw_text(text):
    """Вытаскивает данные из пересланного сообщения"""
    # Улучшенный поиск: ищем значение после тире до конца строки
    email = re.search(r'почта\s*-\s*(\S+)', text, re.I)
    password = re.search(r'пароль\s*-\s*(\S+)', text, re.I)
    q1 = re.search(r'вопрос\s*1\s*-\s*(.+)', text, re.I)
    q2 = re.search(r'вопрос\s*2\s*-\s*(.+)', text, re.I)
    q3 = re.search(r'вопрос\s*3\s*-\s*(.+)', text, re.I)

    if email and password and q1 and q2 and q3:
        return f"{email.group(1).strip()}:{password.group(1).strip()}:{q1.group(1).strip()}:{q2.group(1).strip()}:{q3.group(1).strip()}"
    return None


@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    # Добавим вывод ID в консоль при старте, чтобы ты мог проверить
    print(f"Твой ID: {message.from_user.id}")

    if message.from_user.id not in admins:
        await message.answer(f"У тебя нет доступа. Твой ID: {message.from_user.id}")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    if message.from_user.id == OWNER_ID:
        kb.inline_keyboard.append([InlineKeyboardButton(text="➕ Add Admin", callback_data="add_admin")])
    await message.answer("Бот запущен! Пересылай сообщения с аккаунтами.", reply_markup=kb)


@dp.message(F.text)
async def handle_message(message: types.Message):
    if message.from_user.id not in admins:
        return

    # Обработка добавления админа
    if message.text.isdigit() and message.from_user.id == OWNER_ID:
        admins.add(int(message.text))
        await message.answer(f"Админ {message.text} добавлен!")
        return

    # Парсим
    result = parse_raw_text(message.text)

    uid = message.from_user.id
    if result:
        if uid not in storage: storage[uid] = []
        storage[uid].append(result)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📥 Скачать .txt ({len(storage[uid])})", callback_data="get_file")],
            [InlineKeyboardButton(text="🗑 Очистить", callback_data="clear")]
        ])
        await message.answer(f"✅ Аккаунт №{len(storage[uid])} принят!", reply_markup=kb)
    else:
        # Если прислали текст, который бот не понял
        if not message.text.startswith('/'):
            await message.answer(
                "❌ Не удалось найти данные в сообщении. Проверь, что там есть 'почта -', 'пароль -' и 3 вопроса.")


@dp.callback_query(F.data == "get_file")
async def send_txt(cb: types.CallbackQuery):
    uid = cb.from_user.id
    if uid not in storage or not storage[uid]:
        await cb.answer("Список пуст!")
        return

    content = "\n".join(storage[uid])
    file = BufferedInputFile(content.encode('utf-8'), filename="accounts.txt")

    await bot.send_document(uid, file, caption=f"Готово! Всего строк: {len(storage[uid])}")
    storage[uid] = []
    await cb.answer()


@dp.callback_query(F.data == "clear")
async def clear_list(cb: types.CallbackQuery):
    storage[cb.from_user.id] = []
    await cb.message.answer("Список очищен.")
    await cb.answer()


@dp.callback_query(F.data == "add_admin")
async def req_admin(cb: types.CallbackQuery):
    await cb.message.answer("Пришли ID нового админа (цифрами):")
    await cb.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())