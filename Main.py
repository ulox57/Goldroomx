import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

logging.basicConfig(level=logging.INFO)

TOKEN = "9285396228:AAHlauV20ibfCyE3WrVkvHJl77cxIJHPlb0"
RENDER_URL = "https://onrender.com"
WEBHOOK_PATH = f"/webhook/{TOKEN}"

bot = Bot(token=TOKEN)
dp = Dispatcher()

TEXTS = {
    "ua": {
        "welcome": "Привіт! Оберіть мову / Choose your language:",
        "main_menu": "🎰 Ласкаво просимо до Лудки!\n\nОберіть гру нижче:",
        "spin_slots": "🎰 Крутити Слоти",
        "throw_darts": "🎯 Кинути Дартс",
        "change_lang": "🌐 Змінити мову",
        "slots_win": "🎉 JACKPOT! 777 WINNER!\n\n👑 Гравець: {name}\n🎁 Приз: 25 Telegram Stars\n\n👤 Адмін @M7aq10, перевірте виграш вручну.",
        "slots_lose": "😢 Спробуй ще раз! Тобі випало не 777.",
        "darts_center": "🎯 ЧИСТЕ ВЛУЧАННЯ В ЦЕНТР!\n\n👑 Гравець: {name}\n🎁 Приз: 25 Telegram Stars\n\n👤 Адмін @M7aq10, перевірте виграш вручну.",
        "darts_lose": "🔘 Майже! Але не центр. Спробуй ще раз!"
    },
    "en": {
        "welcome": "Hello! Choose your language / Оберіть мову:",
        "main_menu": "🎰 Welcome to the Gambling Bot!\n\nChoose your game below:",
        "spin_slots": "🎰 Spin Slots",
        "throw_darts": "🎯 Throw Darts",
        "change_lang": "🌐 Change Language",
        "slots_win": "🎉 JACKPOT! 777 WINNER!\n\n👑 Player: {name}\n🎁 Prize: 25 Telegram Stars\n\n👤 Admin @M7aq10, check the win manually.",
        "slots_lose": "😢 Try again! You didn't get 777.",
        "darts_center": "🎯 DIRECT HIT TO THE CENTER!\n\n👑 Player: {name}\n🎁 Prize: 25 Telegram Stars\n\n👤 Admin @M7aq10, check the win manually.",
        "darts_lose": "🔘 Close! But not the center. Try again!"
    }
}

user_lang = {}

def get_menu_kb(lang):
    kb = InlineKeyboardBuilder()
    kb.button(text=TEXTS[lang]["spin_slots"], callback_data="play_slots")
    kb.button(text=TEXTS[lang]["throw_darts"], callback_data="play_darts")
    kb.button(text=TEXTS[lang]["change_lang"], callback_data="choose_lang")
    kb.adjust(1)
    return kb.as_markup()

# --- ХЕНДЛЕРИ ДЛЯ ТЕКСТОВИХ КОМАНД ТА КНОПОК ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🇺🇦 Українська", callback_data="set_lang_ua")
    kb.button(text="🇬🇧 English", callback_data="set_lang_en")
    await message.answer(TEXTS["ua"]["welcome"], reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[-1]
    user_lang[callback.from_user.id] = lang
    await callback.message.edit_text(TEXTS[lang]["main_menu"], reply_markup=get_menu_kb(lang))
    await callback.answer()

@dp.callback_query(F.data == "choose_lang")
async def change_language(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🇺🇦 Українська", callback_data="set_lang_ua")
    kb.button(text="🇬🇧 English", callback_data="set_lang_en")
    await callback.message.edit_text(TEXTS["ua"]["welcome"], reply_markup=kb.as_markup())
    await callback.answer()

# --- ЛОГІКА ІГОР ЧЕРЕЗ КНОПКИ МЕНЮ ---

@dp.callback_query(F.data == "play_slots")
async def play_slots(callback: types.CallbackQuery):
    lang = user_lang.get(callback.from_user.id, "ua")
    msg = await callback.message.answer_dice(emoji="🎰")
    await asyncio.sleep(4)
    if msg.dice.value == 64:
        await msg.reply(TEXTS[lang]["slots_win"].format(name=callback.from_user.full_name))
    else:
        await msg.reply(TEXTS[lang]["slots_lose"])
    await callback.answer()

@dp.callback_query(F.data == "play_darts")
async def play_darts(callback: types.CallbackQuery):
    lang = user_lang.get(callback.from_user.id, "ua")
    msg = await callback.message.answer_dice(emoji="🎯")
    await asyncio.sleep(4)
    if msg.dice.value == 6:
        await msg.reply(TEXTS[lang]["darts_center"].format(name=callback.from_user.full_name))
    else:
        await msg.reply(TEXTS[lang]["darts_lose"])
    await callback.answer()

# --- НОВЕ: ХЕНДЛЕР ДЛЯ ПЕРЕВІРКИ КУБИКІВ, ЯКІ КИДАЮТЬ РУКАМИ В ЧАТ ---

@dp.message(F.dice)
async def handle_user_dice(message: types.Message):
    lang = user_lang.get(message.from_user.id, "ua")
    
    # Якщо кинули Слоти
    if message.dice.emoji == "🎰":
        await asyncio.sleep(4)  # Чекаємо поки закінчиться анімація крутіння
        if message.dice.value == 64:
            await message.reply(TEXTS[lang]["slots_win"].format(name=message.from_user.full_name))
        else:
            await message.reply(TEXTS[lang]["slots_lose"])
            
    # Якщо кинули Дартс
    elif message.dice.emoji == "🎯":
        await asyncio.sleep(4)  # Чекаємо поки летить дротик
        if message.dice.value == 6:
            await message.reply(TEXTS[lang]["darts_center"].format(name=message.from_user.full_name))
        else:
            await message.reply(TEXTS[lang]["darts_lose"])

# --- НАЛАШТУВАННЯ WEBHOOK ТА СЕРВЕРА ---

async def handle_root(request):
    return web.Response(text="Бот успішно працює!")

async def handle_webhook(request):
    url = str(request.url)
    if WEBHOOK_PATH in url:
        update = types.Update.model_validate_json(await request.text(), context={"bot": bot})
        await dp.feed_update(bot, update)
        return web.Response(text="OK")
    return web.Response(status=403)

async def on_startup(app):
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=f"{RENDER_URL}{WEBHOOK_PATH}")
    logging.info("Webhook встановлено.")

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()

def main():
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
