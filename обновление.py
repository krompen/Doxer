import os
import json
import sys
import re
import subprocess
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from telethon.tl.functions.channels import JoinChannelRequest, GetParticipantRequest
from telethon.errors import UserNotParticipantError
from config import API_ID, API_HASH, bot_token, TARGET_CHANNEL_ID, admin_chat_ids

JSON_FILE = "updates.json"
BOT_SCRIPT = "бот.py"
SESSION_DIR = "Не_основные"
CHANNEL_INVITE_LINK = "https://t.me/+-7kI1dpWHytkMGUy"

async def find_session_file():
    if not os.path.exists(SESSION_DIR):
        print(f"❌ Папка '{SESSION_DIR}' не найдена!")
        return None
    
    session_files = [f for f in os.listdir(SESSION_DIR) if f.endswith('.session')]
    
    if not session_files:
        print(f"❌ В папке '{SESSION_DIR}' нет файлов .session")
        return None
    
    return os.path.join(SESSION_DIR, session_files[0])

async def check_channel_membership(client):
    try:
        channel = await client.get_entity(PeerChannel(TARGET_CHANNEL_ID))
        await client(GetParticipantRequest(channel=channel, participant=await client.get_me()))
        return True
    except UserNotParticipantError:
        return False
    except Exception as e:
        print(f"Ошибка при проверке членства в канале: {e}")
        return False

async def join_channel(client):
    try:
        if CHANNEL_INVITE_LINK:
            await client(JoinChannelRequest(CHANNEL_INVITE_LINK))
            return True
        return False
    except Exception as e:
        print(f"Ошибка при присоединении к каналу: {e}")
        return False

async def load_updates():
    if not os.path.exists(JSON_FILE):
        return {"last_update": {"publish_date": "Не определено", "update_date": "Не определено", "version": "Не определено"}}
    try:
        with open(JSON_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            if not data.get("last_update"):
                data["last_update"] = {"publish_date": "Не определено", "update_date": "Не определено", "version": "Не определено"}
            return data
    except:
        return {"last_update": {"publish_date": "Не определено", "update_date": "Не определено", "version": "Не определено"}}

async def save_updates(publish_date, update_date, version):
    data = await load_updates()
    data["last_update"] = {
        "publish_date": publish_date,
        "update_date": update_date,
        "version": version
    }
    with open(JSON_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

async def send_notifications(bot, message, callback_query=None, reply_markup=None):
    if callback_query:
        try:
            await callback_query.answer("✅ Код успешно запущен и готов к работе", show_alert=True)
            await asyncio.sleep(0.5) 
        except Exception as e:
            print(f"Ошибка при отправке callback answer: {e}")
    
    for chat_id in admin_chat_ids:
        try:
            await bot.send_message(chat_id, message, parse_mode='HTML', reply_markup=reply_markup)
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")

async def get_bot_messages(client):
    try:
        if not await check_channel_membership(client):
            if not await join_channel(client):
                await send_notifications(Bot(token=bot_token), 
                    f"<b>❌ Не удалось присоединиться к каналу!</b>\n"
                    f"<b>Пожалуйста, вступите в канал вручную:</b>\n"
                    f"{CHANNEL_INVITE_LINK}")
                return None
        
        channel = await client.get_entity(PeerChannel(TARGET_CHANNEL_ID))
        messages = await client.get_messages(channel, limit=20)
        
        bot_messages = []
        for msg in messages:
            if hasattr(msg, 'document') and msg.document:
                for attr in msg.document.attributes:
                    if hasattr(attr, 'file_name') and attr.file_name == BOT_SCRIPT:
                        version = None
                        text = msg.text or msg.message
                        if text:
                            version_match = re.search(r'(\d+\.\d+)', text)
                            if version_match:
                                version = version_match.group(1)
                        
                        bot_messages.append({
                            "message": msg,
                            "version": version or "Неизвестная версия",
                            "date": msg.date.strftime('%Y-%m-%d %H:%M:%S')
                        })
        return bot_messages
    except Exception as e:
        print(f"Ошибка при поиске сообщений: {e}")
        return None

async def create_version_keyboard(messages):
    keyboard = InlineKeyboardMarkup()
    for msg in messages:
        keyboard.add(InlineKeyboardButton(
            text=f"Версия {msg['version']}",
            callback_data=f"version_{msg['message'].id}"
        ))
    return keyboard

async def download_and_save_message(client, message, callback_query=None):
    try:
        publish_date = message.date.strftime('%Y-%m-%d %H:%M:%S')
        bot_messages = await get_bot_messages(client)
        version = next((m['version'] for m in bot_messages if m['message'].id == message.id), "Неизвестная версия")
        
        if os.path.exists(BOT_SCRIPT):
            os.remove(BOT_SCRIPT)

        await client.download_media(message.document, file=BOT_SCRIPT)
        update_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await save_updates(publish_date, update_date, version)

        await send_notifications(
            callback_query.bot if callback_query else Bot(token=bot_token),
            f"<b>───── ⋆⋅☆⋅⋆ ─────</b>\n<blockquote><b>✅ Файл успешно обновлён</b>\n"
            f"<b>🔄 Версия:</b> {version}\n"
            f"<b>📅 Дата публикации:</b> {publish_date}\n"
            f"<b>🔄 Дата обновления:</b> {update_date}\n"
            f"<b>🚀 Запускаю обновлённую версию...</b></blockquote>\n<b>───── ⋆⋅☆⋅⋆ ─────</b>",
            callback_query
        )

        return True
    except Exception as e:
        error_msg = f"<b>❌ Ошибка при обновлении:</b> {str(e)}"
        print(error_msg)
        await send_notifications(callback_query.bot if callback_query else Bot(token=bot_token), error_msg, callback_query)
        return False

async def check_channel_and_update(callback_query=None, selected_message_id=None):
    session_file = await find_session_file()
    if not session_file:
        return False

    notifier_bot = Bot(token=bot_token) if not callback_query else callback_query.bot
    client = TelegramClient(session_file, API_ID, API_HASH)
    
    try:
        await client.start()
        if not await client.is_user_authorized():
            await send_notifications(notifier_bot, "<b>❌ Сессия не авторизована!</b>", callback_query)
            return False

        if not await check_channel_membership(client):
            if not await join_channel(client):
                await send_notifications(
                    notifier_bot,
                    f"<b>❌ Вы не состоите в целевом канале!</b>\n"
                    f"<b>🔗 Пожалуйста, вступите в канал:</b>\n"
                    f"{CHANNEL_INVITE_LINK}",
                    callback_query
                )
                return False

        bot_messages = await get_bot_messages(client)
        if not bot_messages:
            saved_updates = await load_updates()
            await send_notifications(
                notifier_bot,
                f"<b>───── ⋆⋅☆⋅⋆ ─────</b>\n<blockquote><b>ℹ️ Не найдено сообщение с файлом бот.py</b>\n"
                f"<b>🔄 Текущая версия:</b> {saved_updates['last_update']['version']}\n"
                f"<b>📅 Дата публикации:</b> {saved_updates['last_update']['publish_date']}\n"
                f"<b>🔄 Дата обновления:</b> {saved_updates['last_update']['update_date']}\n"
                f"<b>🚀 Запускаю текущую версию...</b></blockquote>\n<b>───── ⋆⋅☆⋅⋆ ─────</b>",
                callback_query
            )
            return False

        if selected_message_id:
            selected_message = next((m['message'] for m in bot_messages if m['message'].id == selected_message_id), None)
            if not selected_message:
                await send_notifications(notifier_bot, "<b>❌ Выбранное сообщение не найдено</b>", callback_query)
                return False
            
            return await download_and_save_message(client, selected_message, callback_query)
        else:
            saved_updates = await load_updates()
            last_message = bot_messages[0]
            
            if saved_updates.get("last_update", {}).get("publish_date") == last_message['date']:
                last_update = saved_updates["last_update"]["update_date"]
                await send_notifications(
                    notifier_bot,
                    f"<b>───── ⋆⋅☆⋅⋆ ─────</b>\n<blockquote><b>🔄 Файл уже обновлён</b>\n"
                    f"<b>🔄 Версия:</b> {saved_updates['last_update']['version']}\n"
                    f"<b>📅 Дата публикации:</b> {last_message['date']}\n"
                    f"<b>🕒 Последнее обновление:</b> {last_update}\n"
                    f"<i>Выберите версию для обновления или запустите текущую...</i></blockquote>\n<b>───── ⋆⋅☆⋅⋆ ─────</b>",
                    callback_query,
                    reply_markup=await create_version_keyboard(bot_messages)
                )
                return False
            else:
                await send_notifications(
                    notifier_bot,
                    f"<b>───── ⋆⋅☆⋅⋆ ─────</b>\n<blockquote><b>🔄 Доступные версии бота</b>\n"
                    f"<b>📅 Последняя версия:</b> {last_message['version']}\n"
                    f"<b>🕒 Дата публикации:</b> {last_message['date']}\n"
                    f"<i>Выберите версию для обновления...</i></blockquote>\n<b>───── ⋆⋅☆⋅⋆ ─────</b>",
                    callback_query,
                    reply_markup=await create_version_keyboard(bot_messages)
                )
                return False

    except Exception as e:
        saved_updates = await load_updates()
        error_msg = f"<b>───── ⋆⋅☆⋅⋆ ─────</b>\n<blockquote><b>❌ Ошибка при обновлении:</b> {str(e)}\n"
        f"<b>🔄 Текущая версия:</b> {saved_updates['last_update']['version']}\n"
        f"<b>📅 Дата публикации:</b> {saved_updates['last_update']['publish_date']}\n"
        f"<b>🔄 Дата обновления:</b> {saved_updates['last_update']['update_date']}\n"
        f"<b>🚀 Запускаю текущую версию...</b></blockquote>\n<b>───── ⋆⋅☆⋅⋆ ─────</b>"
        print(error_msg)
        await send_notifications(notifier_bot, error_msg, callback_query)
        return False
    finally:
        await client.disconnect()
        if not callback_query:
            await notifier_bot.close()

async def handle_version_selection(callback_query: types.CallbackQuery):
    selected_message_id = int(callback_query.data.split('_')[1])
    await check_channel_and_update(callback_query, selected_message_id)

async def main(callback_query=None):
    if not await check_channel_and_update(callback_query):
        saved_updates = await load_updates()
        print(f"Запускаю текущую версию: {saved_updates['last_update']['version']}")
        subprocess.Popen([sys.executable, BOT_SCRIPT])
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())