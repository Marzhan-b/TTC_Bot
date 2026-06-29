import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from monitor.checker import ping_host, check_and_log
from backend.queries import get_last_checks, get_offline_hosts
from backend.database import async_session, init_db, PingLog
from backend.queries import get_last_checks, get_offline_hosts, save_duty_user
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from monitor.checker import ping_host
from monitor.hosts import REGIONS
from monitor.scheduler import start_scheduler
import monitor.scheduler as scheduler_module
from bot.translations import t
from bot.user_lang import get_lang, set_lang

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


def main_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_regions", lang), callback_data="regions")],
        [InlineKeyboardButton(text=t("btn_check", lang),   callback_data="check")],
        [InlineKeyboardButton(text=t("btn_history", lang), callback_data="history")],
        [InlineKeyboardButton(text=t("btn_offline", lang), callback_data="offline")],
        [InlineKeyboardButton(text="🌐 Language", callback_data="language")],
        [InlineKeyboardButton(text=t("btn_help", lang), callback_data="help")]
    ])

def language_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kz")],
    ])

def regions_menu(lang):
    buttons = []
    for key, region in REGIONS.items():
        buttons.append([
            InlineKeyboardButton(text=region["name"], callback_data=f"region_{key}")
        ])
    buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cities_menu(region_key, lang):
    region = REGIONS[region_key]
    buttons = []
    for i, city in enumerate(region["cities"].keys()):
        buttons.append([
            InlineKeyboardButton(text=f"📍 {city}", callback_data=f"city_{region_key}_{i}")
        ])
    buttons.append([
        InlineKeyboardButton(text="🔍 " + t("btn_regions", lang), callback_data=f"allcities_{region_key}")
    ])
    buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="regions")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_button(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back_menu", lang), callback_data="back")]
    ])

# ── handlers ────────────────────────────────────────────────

@dp.message(Command("start"))
async def start(message: types.Message):
    lang = get_lang(message.chat.id)
    await message.answer(t("welcome", lang), parse_mode="HTML", reply_markup=main_menu(lang))

@dp.callback_query(F.data == "back")
async def cb_back(call: types.CallbackQuery):
    lang = get_lang(call.message.chat.id)
    await call.message.edit_text(t("welcome", lang), parse_mode="HTML", reply_markup=main_menu(lang))
    await call.answer()

@dp.callback_query(F.data == "language")
async def cb_language(call: types.CallbackQuery):
    lang = get_lang(call.message.chat.id)
    await call.message.edit_text(t("choose_language", lang), parse_mode="HTML", reply_markup=language_menu())
    await call.answer()

@dp.callback_query(F.data.startswith("lang_"))
async def cb_set_language(call: types.CallbackQuery):
    new_lang = call.data.replace("lang_", "")
    set_lang(call.message.chat.id, new_lang)
    await call.message.edit_text(t("language_set", new_lang), parse_mode="HTML", reply_markup=main_menu(new_lang))
    await call.answer()

@dp.callback_query(F.data == "regions")
async def cb_regions(call: types.CallbackQuery):
    lang = get_lang(call.message.chat.id)
    await call.message.edit_text(t("choose_region", lang), parse_mode="HTML", reply_markup=regions_menu(lang))
    await call.answer()

@dp.callback_query(F.data.startswith("region_"))
async def cb_region(call: types.CallbackQuery):
    lang = get_lang(call.message.chat.id)
    region_key = call.data.replace("region_", "")
    region = REGIONS.get(region_key)
    if not region:
        await call.answer("Not found")
        return
    await call.message.edit_text(
        f"📍 <b>{region['name']}</b>\n\n{t('choose_city', lang)}",
        parse_mode="HTML",
        reply_markup=cities_menu(region_key, lang)
    )
    await call.answer()

@dp.callback_query(F.data.startswith("city_"))
async def cb_city(call: types.CallbackQuery):
    lang = get_lang(call.message.chat.id)
    parts = call.data.split("_")
    region_key = parts[1]
    city_index = int(parts[2])
    region = REGIONS.get(region_key)

    if not region:
        await call.answer("Not found")
        return

    city_name = list(region["cities"].keys())[city_index]
    nodes = region["cities"][city_name]

    await call.message.edit_text(f"⏳ {t('checking', lang)} <b>{city_name}</b>...", parse_mode="HTML")
    await call.answer()

    tasks = [
        check_and_log(node_name, ip, city_name, region["name"])
        for node_name, ip in nodes.items()
    ]
    results = await asyncio.gather(*tasks)

    lines = [f"📊 <b>{city_name}</b>\n"]
    online = offline = 0

    for (node_name, ip), result in zip(nodes.items(), results):
        if result["alive"]:
            lines.append(f"🟢 <b>{node_name}</b> — {result['avg_time']}")
            online += 1
        else:
            lines.append(f"🔴 <b>{node_name}</b> — {t('offline', lang)}")
            offline += 1

    lines.append(f"\n✅ {t('online', lang)}: {online}  ❌ {t('offline', lang)}: {offline}")

    back = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data=f"region_{region_key}")],
        [InlineKeyboardButton(text=t("btn_back_menu", lang), callback_data="back")]
    ])

    await call.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=back)
@dp.callback_query(F.data.startswith("allcities_"))
async def cb_all_cities(call: types.CallbackQuery):
    lang = get_lang(call.message.chat.id)
    region_key = call.data.replace("allcities_", "")
    region = REGIONS.get(region_key)

    await call.message.edit_text(f"⏳ {t('checking', lang)} <b>{region['name']}</b>...", parse_mode="HTML")
    await call.answer()

    lines = [f"📊 <b>{region['name']}</b>\n"]
    total_online = total_offline = 0

    for city_name, nodes in region["cities"].items():
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(None, ping_host, ip) for ip in nodes.values()]
        results = await asyncio.gather(*tasks)

        online = offline = 0
        city_lines = []
        for (node_name, ip), result in zip(nodes.items(), results):
            if result["alive"]:
                city_lines.append(f"  🟢 {node_name} — {result['avg_time']}")
                online += 1
            else:
                city_lines.append(f"  🔴 {node_name} — {t('offline', lang)}")
                offline += 1

        lines.append(f"\n📍 <b>{city_name}</b> — ✅{online} ❌{offline}")
        lines.extend(city_lines)
        total_online += online
        total_offline += offline

    lines.append(f"\n\n📈 {t('online', lang)}: {total_online}  {t('offline', lang)}: {total_offline}")

    await call.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=back_button(lang))

@dp.callback_query(F.data == "check")
async def cb_check(call: types.CallbackQuery):
    lang = get_lang(call.message.chat.id)
    await call.message.edit_text(t("enter_host", lang), parse_mode="HTML", reply_markup=back_button(lang))
    await call.answer()

@dp.callback_query(F.data == "history")
async def cb_history(call: types.CallbackQuery):
    lang = get_lang(call.message.chat.id)
    logs = await get_last_checks(10)

    if not logs:
        await call.message.edit_text(t("history_empty", lang), reply_markup=back_button(lang))
        await call.answer()
        return

    lines = [t("history_title", lang) + "\n"]
    for log in logs:
        status = "🟢" if log.is_online else "🔴"
        time = log.checked_at.strftime("%d.%m %H:%M")
        lines.append(f"{status} {log.city} — {log.node_name} — {time}")

    await call.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=back_button(lang))
    await call.answer()

@dp.callback_query(F.data == "offline")
async def cb_offline(call: types.CallbackQuery):
    lang = get_lang(call.message.chat.id)
    logs = await get_offline_hosts(10)

    if not logs:
        await call.message.edit_text(t("offline_empty", lang), reply_markup=back_button(lang))
        await call.answer()
        return

    lines = [t("offline_title", lang) + "\n"]
    for log in logs:
        time = log.checked_at.strftime("%d.%m %H:%M")
        lines.append(f"🔴 {log.city} — {log.node_name} — {time}")

    await call.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=back_button(lang))
    await call.answer()

@dp.callback_query(F.data == "help")
async def cb_help(call: types.CallbackQuery):
    lang = get_lang(call.message.chat.id)
    await call.message.edit_text(
        t("help_text", lang),
        parse_mode="HTML",
        reply_markup=back_button(lang)
    )
    await call.answer()

@dp.message(Command("setduty"))
async def set_duty(message: types.Message):
    lang = get_lang(message.chat.id)
    await save_duty_user(message.chat.id)
    await message.answer(t("duty_set", lang), parse_mode="HTML")

@dp.message(F.text)
async def handle_host(message: types.Message):
    lang = get_lang(message.chat.id)
    host = message.text.strip()
    wait_msg = await message.answer(f"⏳ {t('checking', lang)} <code>{host}</code>...", parse_mode="HTML")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, ping_host, host)

    if result["alive"]:
        text = f"✅ <b>{host}</b> — {t('online', lang)}\n\n⚡ {t('response_time', lang)}: <b>{result['avg_time']}</b>"
    else:
        text = f"❌ <b>{host}</b> — {t('offline', lang)}\n\n⚠️ {t('not_responding', lang)}"

    await wait_msg.delete()
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu(lang))

async def main():
    await init_db()
    start_scheduler(bot)
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())