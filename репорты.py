from config import banned_users, private_channel_ids, dp, banned_users_file, re, logger, clients, session_dir, script_dir, API_ID, API_HASH, bot, receivers, smtp_servers, receivers
from session import active_sessions

from states import ChannelDemolitionStates, ReportStates, EmailTemplateStates, ComplaintStates, option_mapping, RestoreAccountStates, CreateAccountStates, reason_mapping
from aiogram import exceptions
from text import email_templates
import html
import aiohttp
import asyncio
import logging
import time
import os
import random
import smtplib
import inspect
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ReportRequest


from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.channels import JoinChannelRequest
from datetime import datetime, timedelta
import re
import json





def get_all_sessions():
    sessions = []
    for client in clients:
        client_folder = os.path.join(session_dir, client["name"])
        if os.path.exists(client_folder):
            for file in os.listdir(client_folder):
                if file.endswith(".session"):
                    sessions.append({
                        "path": os.path.join(client_folder, file),
                        "api_id": client["api_id"],
                        "api_hash": client["api_hash"]
                    })
    return sessions
###


def read_private_users():
    try:
        with open("База_Бота/private_users.txt", "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        return {"ids": [], "usernames": []}
    
    ids = []
    usernames = []
    
    if lines:
        ids = [int(id_str) for id_str in lines[0].split(',') if id_str.strip().isdigit()]
    if len(lines) > 1:
        usernames = [uname.lstrip('@') for uname in lines[1].split(',') if uname.strip()]
    
    return {"ids": ids, "usernames": usernames}

def write_private_users(data):
    with open("База_Бота/private_users.txt", "w", encoding="utf-8") as f:
        ids_str = ",".join(map(str, data["ids"])) if data["ids"] else ""
        usernames_str = ",".join(f"@{uname}" for uname in data["usernames"]) if data["usernames"] else ""
        f.write(f"{ids_str}\n{usernames_str}\n")
private_users = read_private_users()

async def is_private_user(text, private_users):
    words = text.split()
    for word in words:
        if word.isdigit() and int(word) in private_users["ids"]:
            return True
        if word.startswith('@') and word[1:] in private_users["usernames"]:
            return True
    return False
@dp.message_handler(state=RestoreAccountStates.phone)
async def process_restore_phone(message: types.Message, state: FSMContext):
    phone_number = message.text.strip()
    if not phone_number.isdigit() or len(phone_number) < 5 or len(phone_number) > 15:
        await message.answer("❌ Неверный формат номера. Пожалуйста, введите корректный номер телефона.")
        return

    await state.update_data(phone_number=phone_number)
    await message.answer("📝 Введите количество отправок:")
    await RestoreAccountStates.send_count.set()

@dp.message_handler(state=RestoreAccountStates.send_count)
async def process_send_count(message: types.Message, state: FSMContext):
    try:
        try:
            with open('База_Бота/emails.json', 'r') as f:
                senders = json.load(f)
            if not senders:
                await message.answer("<b>❌ Файл emails.json пуст или не содержит почт</b>", parse_mode="HTML")
                return
        except FileNotFoundError:
            await message.answer("<b>❌ Файл emails.json не найден</b>", parse_mode="HTML")
            return
        except json.JSONDecodeError:
            await message.answer("<b>❌ Ошибка в формате файла emails.json</b>", parse_mode="HTML")
            return

        try:
            send_count = int(message.text)
            if send_count <= 0:
                raise ValueError("<b>Количество отправок должно быть больше 0</b>")
            if send_count > 100:
                raise ValueError("<b>Максимальное количество отправок - 100</b>")
        except ValueError as e:
            await message.answer(f"<b>❌ Ошибка:</b> {e}", parse_mode="HTML")
            return

        data = await state.get_data()
        phone_number = data.get("phone_number")
        if not phone_number:
            await message.answer("<b>❌ Не удалось получить номер телефона</b>", parse_mode="HTML")
            return

        target_email = "recover@telegram.org"
        bodies = [
            f"I'm trying to use my mobile phone number: {phone_number}\n"
            "But Telegram says it's banned. Please help.\n\n"
            "App version: 11.4.3 (54732)\n"
            "OS version: SDK 33\n"
            "Device Name: samsungSM-A325F\n"
            "Locale: ru",

            f"Hello Telegram support,\n\n"
            f"My phone number {phone_number} has been banned. "
            "I believe this was a mistake. Can you please review and unban it?\n\n"
            "Best regards,\n",

            f"Dear Support,\n\n"
            f"I can't access my account with number {phone_number}. "
            "It shows as banned. Please assist in recovering my account.\n\n"
            "Device: iPhone 13\n"
            "App version: 10.2.1\n"
            "Country: US",

            f"Help! My number {phone_number} is banned. "
            "I need this account for work. Please unban as soon as possible.\n\n"
            "Android 13\n"
            "Telegram 9.5.2"
        ]

        success_count = 0
        fail_count = 0
        processing_msg = await message.answer("<b>⏳ Начинаю отправку писем...</b>", parse_mode="HTML")

        for i in range(send_count):
            sender_email, sender_password = random.choice(list(senders.items()))
            subject = f"Banned phone number: {phone_number}"
            body = random.choice(bodies)

            success, result = await send_recovery_email(
                receiver=target_email,
                sender_email=sender_email,
                sender_password=sender_password,
                subject=subject,
                body=body,
                photos=[],
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                bot_instance=message.bot
            )

            if success:
                success_count += 1
                status = f"<b>✅ Успешно</b> ({i+1}/{send_count})"
            else:
                fail_count += 1
                status = f"<b>❌ Ошибка</b> ({i+1}/{send_count}): {result}"

            await processing_msg.edit_text(
                f"<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote><b>⏳ Отправка писем...</b>\n"
                f"<b>📞 Номер:</b> <code>{phone_number}</code>\n"
                f"<b>📧 Цель:</b> <code>{target_email}</code>\n"
                f"<b>📊 Прогресс:</b> <i>{i+1}/{send_count}</i>\n"
                f"<b>✅ Успешно:</b> {success_count}\n"
                f"<b>❌ Ошибок:</b> {fail_count}\n"
                f"<b>🔹 Статус:</b> {status}</blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>",
                parse_mode="HTML"
            )

            await asyncio.sleep(1)

        await processing_msg.edit_text(
            f"<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote><b>📬 Итоговый отчет:</b>\n"
            f"<b>📞 Номер:</b> <code>{phone_number}</code>\n"
            f"<b>📧 Получатель:</b> <code>{target_email}</code>\n"
            f"<b>📊 Всего отправок:</b> {send_count}\n"
            f"<b>✅ Успешно:</b> {success_count}\n"
            f"<b>❌ Ошибок:</b> {fail_count}\n\n"
            f"<b>Работа завершена!</b></blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>",
            parse_mode="HTML"
        )

    except Exception as e:
        await message.answer(f"<b>⚠️ Произошла непредвиденная ошибка:</b> <code>{html.escape(str(e))}</code>", parse_mode="HTML")
    finally:
        await state.finish()


async def send_recovery_email(receiver, sender_email, sender_password, subject, body, photos, chat_id, message_id, bot_instance):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if photos:
        for photo in photos:
            image = MIMEImage(photo)
            msg.attach(image)

    try:
        domain = sender_email.split('@')[1]
        if domain not in smtp_servers:
            error_message = f'❌ Отправка не удалась в почте {sender_email}: Неизвестный домен'
            return False, error_message

        smtp_server, smtp_port = smtp_servers[domain]
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver, msg.as_string())

        logging.info(f'Email sent to {receiver} from {sender_email}')
        return True, None
    except Exception as e:
        error_message = f'❌ Ошибка при отправке письма на [{receiver}] от [{sender_email}]: {e}'
        logging.error(f'Error sending email: {e}')
        return False, error_message


@dp.message_handler(state=ComplaintStates.subject)
async def process_subject_step(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.answer('📢Администратор посчитал ваш аккаунт подозрительным и вы были забанены📢')
        return
    
    async with state.proxy() as data:
        data['subject'] = message.text
    await message.answer('📝 Введите текст жалобы:')
    await ComplaintStates.next()

@dp.message_handler(state=ComplaintStates.body)
async def process_body_step(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.answer('📢Администратор посчитал ваш аккаунт подозрительным и вы были забанены📢')
        return
    
    async with state.proxy() as data:
        data['body'] = message.text
    
    await message.answer('🖼 Хотите добавить фотографии? (Да/Нет):')
    await ComplaintStates.photos.set()  

@dp.message_handler(state=ComplaintStates.photos)
async def process_photo_choice_step(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.answer('📢Администратор посчитал ваш аккаунт подозрительным и вы были забанены📢')
        return
    
    add_photo = message.text.lower()
    if add_photo == 'да':
        await message.answer('📎 Пожалуйста, отправьте фотографии:')
    elif add_photo == 'нет':
        await message.answer('🔢 Введите количество отправок (не больше 50):')
        await ComplaintStates.count.set()  
    else:
        await message.answer('❌ Неверный ввод. Пожалуйста, ответьте "Да" или "Нет":')

@dp.message_handler(content_types=['photo'], state=ComplaintStates.photos)
async def process_photos_step(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.answer('📢Администратор посчитал ваш аккаунт подозрительным и вы были забанены📢')
        return
    
    photos = []
    for photo in message.photo:
        file_info = await bot.get_file(photo.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        photos.append(downloaded_file.read())  
    
    async with state.proxy() as data:
        data['photos'] = photos
    
    await message.answer('🔢 Введите количество отправок (не больше 50):')
    await ComplaintStates.next()


@dp.message_handler(state=ComplaintStates.count)
async def process_count_step(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.answer('<b>📢 Администратор посчитал ваш аккаунт подозрительным, и вы были забанены! 📢</b>', 
                           parse_mode="HTML")
        return
    
    try:
        with open('База_Бота/emails.json', 'r') as f:
            senders = json.load(f)
        if not senders:
            await message.answer('<b>❌ Файл emails.json пуст или не содержит почт</b>', parse_mode="HTML")
            return
    except FileNotFoundError:
        await message.answer('<b>❌ Файл emails.json не найден</b>', parse_mode="HTML")
        return
    except json.JSONDecodeError:
        await message.answer('<b>❌ Ошибка в формате файла emails.json</b>', parse_mode="HTML")
        return

    try:
        count = int(message.text)
        if count > 50:
            await message.answer('<b>🚫 Количество отправок не должно превышать 50. Повторите ввод:</b>', 
                                parse_mode="HTML")
            return
        if count <= 0:
            await message.answer('<b>❌ Количество должно быть больше 0. Повторите ввод:</b>', 
                               parse_mode="HTML")
            return
    except ValueError:
        await message.answer('<b>🔢 Пожалуйста, введите число. Повторите ввод:</b>', 
                           parse_mode="HTML")
        return
    
    async with state.proxy() as data:
        subject = data['subject']
        body = data['body']
        photos = data.get('photos', []) 
    private_users = read_private_users()
    for word in body.split():
        if word.startswith('@') and word[1:] in private_users["usernames"]:
            await message.answer(f'<b>❌ Это приватный пользователь: <code>{word}</code>. Жалоба на него невозможна.</b>',
                              parse_mode="HTML")
            return
        if word.isdigit() and int(word) in private_users["ids"]:
            await message.answer(f'<b>❌ Это приватный пользователь: ID <code>{word}</code>. Жалоба на него невозможна.</b>',
                                parse_mode="HTML")
            return
    
    status_message = await message.answer("<b>🔄 Начинаю отправку...</b>", parse_mode="HTML")
    success_count = 0
    fail_count = 0
    
    for i in range(count):
        receiver = random.choice(receivers)
        sender_email, sender_password = random.choice(list(senders.items()))
        success, error_message = await send_email(
            receiver, sender_email, sender_password, subject, body, photos,
            chat_id=message.chat.id, message_id=status_message.message_id, bot_instance=bot
        )
        
        send_result_message = (
            f"<b>───── ⋆⋅☆⋅⋆ ─────</b>\n<blockquote>"
            f"<b>📌 Тема письма:</b> <code>{html.escape(subject)}</code>\n"
            f"<b>📝 Текст письма:</b> <code>{html.escape(body[:50])}...</code>\n\n"
            f"<b>📩 Отправитель:</b> <code>{sender_email}</code>\n"
            f"<b>📨 Получатель:</b> <code>{receiver}</code>\n"
            f"<b>📷 Фото:</b> {'✅ С фото' if photos else '❌ Без фото'}\n"
            f"<b>📌 Статус отправки:</b> {'✅ Успешно' if success else '❌ Не удачно'}\n"
            f"<b>💬 Сообщение:</b> <code>{html.escape(error_message) if not success else 'Письмо отправлено'}</code>\n"
            f"<b>📊 Прогресс:</b> <i>{i+1}/{count}</i>\n</blockquote>"
            f"<b>───── ⋆⋅☆⋅⋆ ─────</b>"
        )
        
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_message.message_id,
            text=send_result_message,
            parse_mode="HTML"
        )
        
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        await asyncio.sleep(1)  
    
    final_message = (
        f"<b>───── ⋆⋅☆⋅⋆ ─────</b>\n<blockquote>"
        f"<b>📊 Итоговый результат:</b>\n\n"
        f"<b>✅ Успешно отправлено:</b> <code>{success_count}</code>\n"
        f"<b>❌ Не удачно отправлено:</b> <code>{fail_count}</code>\n"
        f"<b>📌 Тема:</b> <code>{html.escape(subject)}</code>\n"
        f"<b>📝 Текст:</b> <code>{html.escape(body[:50])}...</code>\n"
        f"<b>📷 Медиа:</b> {'✅ С фото' if photos else '❌ Без фото'}\n</blockquote>"
        f"<b>───── ⋆⋅☆⋅⋆ ─────</b>"
    )
    
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=final_message,
        parse_mode="HTML"
    )
    await state.finish()    
async def send_email(receiver, sender_email, sender_password, subject, body, photos, chat_id, message_id, bot_instance):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    if photos:
        for photo in photos:
            image = MIMEImage(photo)
            msg.attach(image)
    
    try:
        domain = sender_email.split('@')[1]
        if domain not in smtp_servers:
            error_message = f'❌ Отправка не удалась в почте {sender_email}: Неизвестный домен'
            return False, error_message
        
        smtp_server, smtp_port = smtp_servers[domain]
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver, msg.as_string())
        
        logging.info(f'Email sent to {receiver} from {sender_email}')
        return True, None
    except Exception as e:
        error_message = f'❌ Ошибка при отправке письма на [{receiver}] от [{sender_email}]: {e}'
        logging.error(f'Error sending email: {e}')
        return False, error_message
            
@dp.message_handler(state=ComplaintStates.text_for_site)
async def process_text_for_site_step(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.answer('📢 Администратор посчитал ваш аккаунт подозрительным, и вы были забанены! 📢')
        return

    async with state.proxy() as data:
        data['text_for_site'] = message.text

    await message.answer('🔢 Введите количество отправок (не больше 50):')
    await ComplaintStates.next()

from aiogram.dispatcher import FSMContext

async def get_working_proxy():
       for proxy in random.sample(proxies, len(proxies)):
           try:
               response = requests.get('https://www.google.com', proxies=proxy, timeout=5)
               if response.status_code == 200:
                   return proxy
           except Exception as e:
               logging.error(f'Proxy {proxy} is not working: {e}')
       return None

@dp.message_handler(state=ComplaintStates.count_for_site)
async def process_count_for_site_step(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.answer('📢 Администратор посчитал ваш аккаунт подозрительным, и вы были забанены! 📢')
        return
    
    try:
        count = int(message.text)
        if count > 50:
            await message.answer('🚫 Количество отправок не должно превышать 50. Повторите ввод:')
            return
    except ValueError:
        await message.answer('🔢 Пожалуйста, введите число. Повторите ввод:')
        return
    
    async with state.proxy() as data:
        text = data['text_for_site']

    private_users = read_private_users()
    if await is_private_user(text, private_users):
        await message.answer('🚫 Нельзя отправлять жалобы на приватных пользователей.')
        await state.finish()
        return

    status_message = await message.answer("🔄 Начинаю отправку...")
    
    success_count = 0
    fail_count = 0
    
    for _ in range(count):
        email = random.choice(mail)
        phone = random.choice(phone_numbers)
        proxy = await get_working_proxy()
        if not proxy:
            await message.answer('❌ В данный момент отсутствуют работоспособные прокси для отправки.')
            break
        
        success = await send_to_site(text, email, phone, proxy)
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        await bot.edit_message_text(
            chat_id=message.chat.id,
            parse_mode="HTML",
            message_id=status_message.message_id,
            text=(
                f"───── ⋆⋅☆⋅⋆ ─────\n"
                f"<blockquote>🔄 Отправка...\n"
                f"✅ Успешно: {success_count}\n"
                f"❌ Не удачно: {fail_count}\n"
                f"📝 Текст: {text}\n"
                f"📧 Почта: {email}\n"
                f"📞 Телефон: {phone}\n"
                f"🌐 Прокси: {proxy}\n</blockquote>"
                f"───── ⋆⋅☆⋅⋆ ─────"
            )
        )
    
    final_message = (
        f"───── ⋆⋅☆⋅⋆ ─────\n"
        f"<blockquote>📊 Итоговый результат:\n"
        f"✅ Успешно отправлено: {success_count}\n"
        f"❌ Не удачно отправлено: {fail_count}\n</blockquote>"
        f"───── ⋆⋅☆⋅⋆ ─────"
    )
    
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=final_message,
        parse_mode="HTML"
    )
    await state.finish()
##
ID_REQUEST_MESSAGES = [
    "👀 Эй, детектив! Введи мне @username или ID злодея:",
    "🕵️‍♂️ Кто наш нарушитель спокойствия? Дайте мне его @username или ID:",
    "🔍 Шерлок Холмс просит: введите @username или ID подозреваемого:",
    "👮‍♂️ Полиция нравов запрашивает ID или @username нарушителя:",
    "🚨 Внимание! Требуется идентификатор преступника (@username или ID):",
    "🧐 Хмм... Кто же этот загадочный нарушитель? Введите @username или ID:"
]

URL_REQUEST_MESSAGES = [
    "🌐 Детектив, нам нужны улики! Пришлите ссылку на нарушение (http/https):",
    "🔗 Шерлок, не забудьте прикрепить доказательства! Введите URL нарушения:",
    "📌 Бинго! Теперь дайте ссылку на преступление (начинается с http/https):",
    "🖇️ Улика номер два: ссылка на нарушение (давайте быстрее, http/https):",
    "🧩 Пазл почти собран! Осталось ввести URL нарушения:",
    "📎 Прикрепите ссылку на злодеяние (начинается с http/https):"
]

COUNT_REQUEST_MESSAGES = [
    "🔢 Сколько раз будем бомбить нарушителя? (1-50):",
    "💣 Какая у нас мощность артобстрела? Введите число писем (1-50):",
    "📦 Сколько подарков отправим? Введите число (1-50):",
    "✉️ Количество любовных писем для нарушителя (1-50):",
    "🎯 Сколько выстрелов делаем? Введите число писем (1-50):",
    "📮 Почтальон Печкин спрашивает: сколько писем отправить (1-50)?"
]

def get_templates_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    for template_name in email_templates.keys():
        btn = InlineKeyboardButton(f'📌 {template_name.capitalize()}', callback_data=f'template_{template_name}')
        markup.add(btn)
    markup.add(InlineKeyboardButton('🔙 Назад', callback_data='Email_snos_men'))
    return markup

photos_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
photos_keyboard.add(KeyboardButton('✅ Да'), KeyboardButton('❌ Нет'))

@dp.callback_query_handler(lambda c: c.data == 'email_hablon', state='*')
async def email_templates_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    message_text = "📫 Выберите тип нарушения:"
    if callback_query.message.photo:
        await dp.bot.edit_message_caption(callback_query.message.chat.id, callback_query.message.message_id, caption=message_text, reply_markup=get_templates_keyboard())
    else:
        await dp.bot.edit_message_text(message_text, callback_query.message.chat.id, callback_query.message.message_id, reply_markup=get_templates_keyboard())
    await EmailTemplateStates.choose_template.set()

@dp.callback_query_handler(lambda c: c.data.startswith('template_'), state=EmailTemplateStates.choose_template)
async def process_template_choice(callback_query: types.CallbackQuery, state: FSMContext):
    template_name = callback_query.data.split('_')[1]
    await callback_query.answer()
    async with state.proxy() as data:
        data['template_name'] = template_name
        data['all_subjects'] = email_templates[template_name]['subjects']
        data['all_templates'] = email_templates[template_name]['templates']
    await callback_query.message.answer(random.choice(ID_REQUEST_MESSAGES))
    await EmailTemplateStates.get_target.set()

@dp.message_handler(state=EmailTemplateStates.get_target)
async def process_target_step(message: types.Message, state: FSMContext):
    target = message.text.strip()
    if not target:
        await message.answer("❌ Эй, детектив, вы забыли ввести цель! Попробуйте еще раз.")
        return
    
    async with state.proxy() as data:
        data['target'] = target
    
    await message.answer(random.choice(URL_REQUEST_MESSAGES))
    await EmailTemplateStates.get_violation_url.set()

@dp.message_handler(state=EmailTemplateStates.get_violation_url)
async def process_violation_url_step(message: types.Message, state: FSMContext):
    url = message.text.strip()
    if not url.startswith(('http://', 'https://')):
        await message.answer("❌ Некорректная ссылка! Введите URL с http/https")
        return
    
    async with state.proxy() as data:
        template_name = data['template_name']
        
        subject = random.choice(email_templates[template_name]['subjects']).format(target=data['target'])
        body = random.choice(email_templates[template_name]['templates']).format(
            target=data['target'],
            url=url
        )
        
        data.update({
            'url': url,
            'subject': subject,
            'body': body
        })
        
        preview_message = f"""
<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote>
<b>📌 Шаблон:</b> <code>{template_name}</code>
<b>👤 Нарушитель:</b> <code>{data['target']}</code>
<b>🔗 Ссылка:</b> <code>{url}</code>
</blockquote>
Хотите добавить фото 📷 (только одно)
<b>───── ⋆⋅☆⋅⋆ ─────</b>
"""
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(text="✅ Да", callback_data="add_photo_yes"),
        types.InlineKeyboardButton(text="❌ Нет", callback_data="add_photo_no")
    )
    
    await message.answer(preview_message, reply_markup=keyboard, parse_mode="HTML")    
    await EmailTemplateStates.get_photo_confirm.set()

@dp.callback_query_handler(lambda c: c.data in ['add_photo_yes', 'add_photo_no'], state=EmailTemplateStates.get_photo_confirm)
async def process_photo_confirm_step(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    
    if callback_query.data == 'add_photo_yes':
        await callback_query.message.answer("📎 Отправьте ОДНО фото:")
        await EmailTemplateStates.get_photo.set()
    else:
        async with state.proxy() as data:
            data['photo'] = None
        await callback_query.message.answer(random.choice(COUNT_REQUEST_MESSAGES))
        await EmailTemplateStates.get_count.set()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=EmailTemplateStates.get_photo)
async def process_photo_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['photo'] = message.photo[-1].file_id
        
    await message.answer("✅ Фото добавлено")
    await message.answer(random.choice(COUNT_REQUEST_MESSAGES))
    await EmailTemplateStates.get_count.set()


@dp.message_handler(state=EmailTemplateStates.get_count)
async def process_count_step(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 1 or count > 50:
            raise ValueError
    except ValueError:
        await message.answer("❌ Серьезно? Нужно число от 1 до 50!")
        return
    
    try:
        with open('База_Бота/emails.json') as f:
            senders = json.load(f)
        if not senders:
            await message.answer("❌ Ошибка: Нет доступных email для отправки!")
            return
    except Exception as e:
        await message.answer(f"❌ Ошибка загрузки emails.json: {html.escape(str(e))}")
        return
    
    async with state.proxy() as data:
        target = data['target']
        url = data['url']
        all_subjects = data['all_subjects']
        all_templates = data['all_templates']
        photo_id = data.get('photo')

    status_message = await message.answer("🔄 Начинаю отправку...", parse_mode="HTML")
    
    success_count = 0
    fail_count = 0
    
    for i in range(count):
        subject = random.choice(all_subjects).format(target=target)
        body = random.choice(all_templates).format(
            target=target,
            url=url
        )
        
        receiver = random.choice(receivers)
        sender_email, sender_password = random.choice(list(senders.items()))
        
        photo_data = None
        if photo_id:
            photo_file = await dp.bot.get_file(photo_id)
            photo_data = await dp.bot.download_file(photo_file.file_path)
        
        success, error_message = await send_email(
            receiver=receiver,
            sender_email=sender_email,
            sender_password=sender_password,
            subject=subject,
            body=body,
            photos=[photo_data.getvalue()] if photo_data else [],
            chat_id=message.chat.id,
            message_id=status_message.message_id,
            bot_instance=dp.bot
        )
        
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        progress_message = f"""<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote>
<b>📊 Прогресс:</b> {i+1}/{count}
<b>✅ Успешно:</b> {success_count}
<b>❌ Ошибки:</b> {fail_count}
<b>📩Отправитель:</b> <code>{sender_email}</code>
<b>📨Получатель:</b> <code>{receiver}</code>
</blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>
"""
        await dp.bot.edit_message_text(
            progress_message,
            message.chat.id,
            status_message.message_id,
            parse_mode="HTML"
        )
        
        await asyncio.sleep(1)
    
    final_message = f"""<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote>
<b>🎯 Итоги:</b>
<b>✅ Успешно:</b> {success_count}
<b>❌ Ошибки:</b> {fail_count}
</blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>
"""
    await dp.bot.edit_message_text(
        final_message,
        message.chat.id,
        status_message.message_id,
        parse_mode="HTML"
    )
    await state.finish()



async def send_to_site(text, email, phone, proxy):
    url = "https://telegram.org/support"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": random.choice(user_agents)
    }
    data = {
        "message": text,
        "email": email,
        "phone": phone,
        "setln": "ru"
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, proxies=proxy, timeout=10)
        if response.status_code == 200:
            logging.info(f'Data sent to site: {text}, email: {email}, phone: {phone}')
            return True
        else:
            logging.error(f'Error sending data to site: {response.status_code}')
            return False
    except Exception as e:
        logging.error(f'Error sending data to site: {e}')
        return False
##

user_last_report_time = {}
            
async def process_with_session(session_info, target, message):
    client = TelegramClient(
        session=SQLiteSession(session_info["path"]),
        api_id=session_info["api_id"],
        api_hash=session_info["api_hash"]
    )
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await message.answer("❌ Ошибка авторизации сессии")
            return None

        dox_handler = DoxBotHandler(session_info["name"])
        return await dox_handler.process_dox_request(target, message)
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке запроса: {str(e)}")
        return None
    finally:
        await client.disconnect()            




@dp.callback_query_handler(lambda c: c.data.startswith('option_'), state=ReportStates.option)
async def process_user_report(call: types.CallbackQuery, state: FSMContext):
    try:
        user_id = call.from_user.id
        
        if user_id in user_last_report_time:
            time_since_last_report = datetime.now() - user_last_report_time[user_id]
            if time_since_last_report < timedelta(minutes=2):
                remaining_time = timedelta(minutes=2) - time_since_last_report
                minutes = remaining_time.seconds // 60
                seconds = remaining_time.seconds % 60
                await call.answer(
                    f"⏳ Подождите {minutes:02d}:{seconds:02d} минут",
                    show_alert=True
                )
                return

        option = call.data.split('_')[1]
        await call.answer()
        
        async with state.proxy() as data:
            data['option'] = option
            targets_data = data['message_links']
            users_info = data.get('users_info', {})
            
        await call.message.edit_text('<b>🚨 Отправка репортов на пользователей...</b>', parse_mode="HTML")
        await send_reports(call, state)

    except Exception as e:
        logger.error(f"User report error: {str(e)}")
        await call.message.edit_text(f'❌ Ошибка: {str(e)}')




######$$



async def send_reports(call: types.CallbackQuery, state: FSMContext, report_msg: types.Message = None):
    try:
        user_id = call.from_user.id
        async with state.proxy() as data:
            targets_data = data['message_links']
            option = data['option']
            users_info = data.get('users_info', {})

        sessions = get_all_sessions()
        if not sessions:
            await call.message.answer('❌ Нет доступных сессий.')
            await state.finish()
            return
        
        def ensure_session_json(session_path):
            json_path = os.path.splitext(session_path)[0] + '.json'
            if not os.path.exists(json_path):
                default_data = {
                    "status": "Свободна",
                    "last_used": None,
                    "usage_count": 0
                }
                with open(json_path, 'w') as f:
                    json.dump(default_data, f)
            return json_path
        
        for session in sessions:
            session['json_path'] = ensure_session_json(session['path'])

        option_names = {
            "1": "Спам", "2": "Насилие", "3": "Насилие над детьми", "4": "Порнография",
            "5": "Нарушение авторских прав", "6": "Личные данные", "7": "Геонерелевантный",
            "8": "Фальшивка", "9": "Наркотики"
        }
        
        stats = {
            'total_reports': 0,
            'failed_reports': 0,
            'flood_errors': 0,
            'private_users_skipped': [],
            'last_report_text': "—",
            'active_sessions': 0,
            'current_message_text': "",
            'reports_per_target': {},
            'current_target': "—",
            'current_link': "—",
            'processed_targets': 0,
            'processed_links': 0
        }

        for target_username in targets_data:
            stats['reports_per_target'][target_username] = {
                'total': 0,
                'failed': 0,
                'links_processed': 0
            }

        initial_text = (
            "───── ⋆⋅☆⋅⋆ ─────\n"
            "<blockquote>📊 <b>Статус отправки репортов:</b>\n"
            f"✅ Успешно: <code>0</code>\n"
            f"❌ Неудачно: <code>0</code>\n"
            f"🔄 Активных сессий: <code>0</code>\n"
            f"⏳ FloodWait: <code>0</code>\n"
            f"🎯 Текущая цель: <code>{stats['current_target']}</code>\n"
            f"📌 Текущая ссылка: <code>{stats['current_link']}</code>\n"
            f"📝 Текст репорта: <code>{stats['last_report_text']}</code></blockquote>\n"
            "───── ⋆⋅☆⋅⋆ ─────"
        )
        result_message = await call.message.edit_text(initial_text, parse_mode="HTML")
        stats['current_message_text'] = initial_text

        last_update_time = time.time()
        update_interval = 1.0

        async def update_status(force=False):
            nonlocal last_update_time
            current_time = time.time()
            
            if not force and current_time - last_update_time < update_interval:
                return
                
            text = f"""───── ⋆⋅☆⋅⋆ ─────
<blockquote>📊 <b>Статус:</b>
✅ Успешно: <code>{stats['total_reports']}</code>
❌ Ошибки: <code>{stats['failed_reports']}</code>
🔄 Активных сессий: <code>{stats['active_sessions']}</code>
⏳ FloodWait: <code>{stats['flood_errors']}</code>
🎯 Текущая цель: <code>{stats['current_target']}</code>
📌 Текущая ссылка: <code>{stats['current_link'].split('/')[-1] if stats['current_link'] != '—' else '—'}</code>
📝 Текст репорта: <code>{stats['last_report_text']}</code>"""
            
            if stats['private_users_skipped']:
                text += f"\n👤 Пропущено приватных: <code>{len(stats['private_users_skipped'])}</code>"
            
            if len(targets_data) > 1:
                text += f"\n📈 Прогресс: <code>{stats['processed_targets']}/{len(targets_data)} целей</code>"
            
            text += "</blockquote>\n───── ⋆⋅☆⋅⋆ ─────"
            
            if text != stats['current_message_text']:
                try:
                    await result_message.edit_text(text, parse_mode="HTML")
                    stats['current_message_text'] = text
                    last_update_time = current_time
                except Exception as e:
                    if "Message is not modified" not in str(e):
                        logger.error(f"Error updating status message: {str(e)}")

        async def process_message(session_data, target_username, message_link):
            client = None
            try:
                async with session_lock:
                    with open(session_data["json_path"], 'r+') as f:
                        data = json.load(f)
                        if data.get("status") != "Свободна":
                            return False
                        data["status"] = "Занята"
                        data["last_used"] = datetime.now().isoformat()
                        data["usage_count"] = data.get("usage_count", 0) + 1
                        f.seek(0)
                        json.dump(data, f)
                        f.truncate()
                
                stats['active_sessions'] += 1
                await update_status()
                
                
                delay = random.uniform(0.3, 0.9)
                await asyncio.sleep(delay)
                
                client = TelegramClient(session_data["path"], session_data["api_id"], session_data["api_hash"])
                await client.connect()
                
                if not await client.is_user_authorized():
                    stats['failed_reports'] += 1
                    stats['reports_per_target'][target_username]['failed'] += 1
                    return False

                parts = message_link.split('/')
                if parts[3] == 'c':
                    chat_id = int('-100' + parts[4])
                    message_id = int(parts[5])
                    chat = await client.get_entity(PeerChannel(chat_id))
                else:
                    chat_username = parts[3]
                    message_id = int(parts[4])
                    try:
                        chat = await client.get_entity(chat_username)
                    except errors.UsernameNotOccupiedError:
                        stats['failed_reports'] += 1
                        stats['reports_per_target'][target_username]['failed'] += 1
                        return False
                    except errors.ChannelPrivateError:
                        stats['private_users_skipped'].append(chat_username)
                        return False

                try:
                    await client(JoinChannelRequest(chat))
                except errors.UserAlreadyParticipantError:
                    pass
                except errors.ChannelPrivateError:
                    stats['private_users_skipped'].append(chat_username)
                    return False

                target_message = await client.get_messages(chat, ids=message_id)
                if not target_message:
                    stats['failed_reports'] += 1
                    stats['reports_per_target'][target_username]['failed'] += 1
                    return False

                
                use_text = random.choice([True, False])
                report_text = generate_report_text(call.from_user, message_link, option, target_message, chat, users_info) if use_text else ""
                stats['last_report_text'] = report_text if use_text else "—"
                
                await client(ReportRequest(
                    peer=chat,
                    id=[message_id],
                    option=option,
                    message=report_text
                ))
                
                stats['total_reports'] += 1
                stats['reports_per_target'][target_username]['total'] += 1
                stats['reports_per_target'][target_username]['links_processed'] += 1
                return True

            except errors.FloodWaitError as e:
                stats['flood_errors'] += 1
                await asyncio.sleep(e.seconds + 1)
                stats['failed_reports'] += 1
                stats['reports_per_target'][target_username]['failed'] += 1
                return False
            except Exception as e:
                stats['failed_reports'] += 1
                stats['reports_per_target'][target_username]['failed'] += 1
                logger.error(f"Error processing message {message_link} for target {target_username} with session {session_data['path']}: {str(e)}")
                return False
            finally:
                if client:
                    try:
                        await client.disconnect()
                    except Exception as disconnect_e:
                        logger.error(f"Error during client disconnect for session {session_data['path']}: {disconnect_e}")
                async with session_lock:
                    with open(session_data["json_path"], 'r+') as f:
                        data = json.load(f)
                        data["status"] = "Свободна"
                        f.seek(0)
                        json.dump(data, f)
                        f.truncate()
                
                stats['active_sessions'] -= 1
                await update_status()
        
        session_lock = asyncio.Lock()
        
        for target_username, target_data in targets_data.items():
            stats['current_target'] = target_username
            stats['processed_targets'] += 1
            links = target_data['links']
            
            for message_link in links:
                stats['current_link'] = message_link
                stats['processed_links'] += 1
                await update_status(force=True)
                
                tasks = []
                for session in sessions:
                    task = asyncio.create_task(process_message(session, target_username, message_link))
                    tasks.append(task)
                    await asyncio.sleep(0.1)
                
                try:
                    await asyncio.gather(*tasks)
                except Exception as e:
                    logger.error(f"Error in gather for target {target_username}: {str(e)}")
                
                await update_status(force=True)
        
        report_details = f"""───── ⋆⋅☆⋅⋆ ─────
<blockquote>🎉 <b>Итоговый отчет</b>
🎯 <b>Целей обработано:</b> <code>{len(targets_data)}</code>
📌 <b>Причина:</b> <code>{option_names.get(option, 'Неизвестно')}</code>
✅ <b>Всего успешно:</b> <code>{stats['total_reports']}</code>
❌ <b>Неудачно:</b> <code>{stats['failed_reports']}</code>\n"""
        
        for target_username, target_stats in stats['reports_per_target'].items():
            report_details += (
                f"\n🎯 <b>{target_username}:</b> "
                f"✅<code>{target_stats['total']}</code> "
                f"❌<code>{target_stats['failed']}</code> "
                f"🔗<code>{len(targets_data[target_username]['links'])}</code>"
            )
        
        if stats['private_users_skipped']:
            report_details += f"\n\n👤 <b>Пропущено приватных:</b> <code>{len(stats['private_users_skipped'])}</code>"
        
        report_details += "</blockquote>───── ⋆⋅☆⋅⋆ ─────"
        
        await result_message.edit_text(report_details, parse_mode="HTML")
        await state.finish()
        user_last_report_time[user_id] = datetime.now()

    except Exception as e:
        logger.error(f"Error in send_reports: {str(e)}")
        if 'result_message' in locals() and result_message:
            await result_message.edit_text(f'❌ Произошла ошибка: {str(e)}', parse_mode="HTML")
        else:
            await call.message.answer(f'❌ Произошла ошибка: {str(e)}')





######$$
def generate_report_text(user, message_link, option, target_message, chat, chat_id=None, chat_title=None):
    if chat_title is None and hasattr(chat, 'title'):
        chat_title = chat.title
    elif chat_title is None and hasattr(chat, 'username'):
        chat_title = chat.username
    elif chat_title is None:
        chat_title = "this chat"

    target_id_str = f"ID: {chat_id}" if chat_id else ""
    target_name_str = f"Chat: {chat_title}" if chat_title else ""
    
    context_info = ""
    if target_id_str and target_name_str:
        context_info = f"({target_id_str}, {target_name_str})"
    elif target_id_str:
        context_info = f"({target_id_str})"
    elif target_name_str:
        context_info = f"({target_name_str})"

    message_content = target_message.message if target_message.message else "media content"

    message_type = "a message"
    if target_message.media:
        message_type_raw = target_message.media.__class__.__name__.lower()
        if "document" in message_type_raw:
            message_type = "a document"
        elif "photo" in message_type_raw:
            message_type = "a photo"
        elif "webpage" in message_type_raw:
            message_type = "a link"
        elif "video" in message_type_raw:
            message_type = "a video"
        elif "voice" in message_type_raw:
            message_type = "a voice message"
        elif "sticker" in message_type_raw:
            message_type = "a sticker"
        else:
            message_type = "a media file"
    
    english_templates = {
        '1': [  
            f"This {message_type} ({message_link}) contains clear spam. It promotes unwanted services and disrupts communication.",
            f"The user is sending unsolicited promotional content ({message_link}) in {chat_title}. This is a violation of spam policies.",
            f"Detected mass messaging activity via this {message_type} ({message_link}) in {chat_title}. Please take action against this spammer.",
            f"This message is spam: '{message_content}'. It needs to be removed from {chat_title} as soon as possible. {context_info}.",
            f"Unacceptable spam was posted. The message link is {message_link}. It is crucial to address this immediately. The content: '{message_content}'.",
            f"Incoming spam message identified at {message_link} in {chat_title}. It contains unsolicited material. This user abuses the platform. Please act. {context_info}.",
            f"Report for spam: {message_link}. This user is repeatedly sending unwanted commercial content in {chat_title}. This undermines user experience. Kindly intervene."
        ],
        '2': [  
            f"This {message_type} ({message_link}) contains violent threats. This content poses a danger to users and must be removed.",
            f"The message ({message_link}) posted in {chat_title} incites violence and promotes harmful behavior. Urgent action is required.",
            f"Graphic violent content was shared through this {message_type} ({message_link}) in {chat_title}. This is a serious violation.",
            f"Urgent report: message '{message_content}' at {message_link} promotes violence. This is highly inappropriate for {chat_title} and must be addressed. {context_info}.",
            f"This content is extremely disturbing: '{message_content}' at {message_link}. It clearly advocates for violence and is unacceptable.",
            f"Violence is being propagated through {message_link} in {chat_title}. This {message_type} promotes aggressive and harmful acts. Immediate removal is essential. {context_info}.",
            f"Reporting violent content: {message_link}. This user is posting material that could cause serious harm or distress in {chat_title}. Please take swift action."
        ],
        '3': [  
            f"This {message_type} ({message_link}) contains child sexual abuse material. This is illegal and extremely dangerous.",
            f"The message ({message_link}) posted in {chat_title} involves the exploitation of minors. Law enforcement must be notified immediately.",
            f"Illegal content depicting child sexual abuse was shared through this {message_type} ({message_link}) in {chat_title}. This requires immediate intervention.",
            f"This message '{message_content}' at {message_link} shows clear signs of child endangerment. This is a severe criminal act that needs immediate investigation in {chat_title}. {context_info}.",
            f"CRITICAL REPORT: Child abuse material found at {message_link}. This content is illegal and must be removed and reported to authorities. The content: '{message_content}'.",
            f"Child exploitation content detected at {message_link} in {chat_title}. This {message_type} contains illegal material related to minors. It is imperative to act immediately and involve law enforcement. {context_info}.",
            f"Urgent child safety report: {message_link}. This user has shared content that exploits children in {chat_title}. Please ensure this is handled with the highest priority and reported to relevant authorities."
        ],
        '4': [  
            f"This {message_type} ({message_link}) contains explicit pornographic material. This content is inappropriate for the platform.",
            f"The message ({message_link}) posted in {chat_title} displays sexually explicit content. This violates platform guidelines.",
            f"NSFW content was shared through this {message_type} ({message_link}) in {chat_title}. This is inappropriate and needs to be removed.",
            f"Explicit content detected: '{message_content}' at {message_link}. This is inappropriate for {chat_title} and should be removed. {context_info}.",
            f"This message contains pornographic material at {message_link}. It is crucial to remove this content immediately. The content: '{message_content}'.",
            f"Pornographic material found at {message_link} in {chat_title}. This {message_type} contains highly explicit content. Please ensure its immediate removal. {context_info}.",
            f"Reporting inappropriate adult content: {message_link}. This user is posting explicit material in {chat_title} that violates community standards. Please take appropriate action."
        ],
        '5': [  
            f"This {message_type} ({message_link}) infringes on copyrighted material. The content is used without authorization.",
            f"The message ({message_link}) posted in {chat_title} contains unauthorized copyrighted content. This is a clear violation of intellectual property rights.",
            f"Pirated content was shared through this {message_type} ({message_link}) in {chat_title}. This needs to be taken down immediately.",
            f"Copyright violation: '{message_content}' at {message_link}. This content in {chat_title} is stolen and must be removed. {context_info}.",
            f"Unauthorized use of copyrighted material found at {message_link}. Please remove this immediately. The content: '{message_content}'.",
            f"Copyright infringement reported at {message_link} in {chat_title}. This {message_type} contains intellectual property that is not licensed for use. Please take action to remove it. {context_info}.",
            f"Reporting copyright breach: {message_link}. This user is distributing copyrighted material without permission in {chat_title}. Kindly ensure this content is removed and sanctions are applied."
        ],
        '6': [  
            f"This {message_type} ({message_link}) exposes personal private data. This is a privacy violation and risk to users.",
            f"The message ({message_link}) posted in {chat_title} leaks sensitive personal information. This is a serious privacy breach.",
            f"Unauthorized personal data was shared through this {message_type} ({message_link}) in {chat_title}. This needs to be removed and investigated.",
            f"Privacy breach: '{message_content}' at {message_link}. This message exposes private information in {chat_title} and must be removed. {context_info}.",
            f"Sensitive personal data found at {message_link}. This is a direct privacy violation and requires immediate removal. The content: '{message_content}'.",
            f"Personal data leak reported at {message_link} in {chat_title}. This {message_type} contains confidential user information. Immediate action to secure and remove this data is necessary. {context_info}.",
            f"Reporting personal data exposure: {message_link}. This user is sharing private information in {chat_title} without consent. Please ensure this content is deleted and the user is held accountable."
        ],
        '7': [  
            f"This {message_type} ({message_link}) is off-topic and irrelevant for {chat_title}. It disrupts the community focus.",
            f"The message ({message_link}) posted in {chat_title} is geo-irrelevant and not suitable for this region/group. Please remove it.",
            f"Disruptive content was shared through this {message_type} ({message_link}) in {chat_title}. It does not align with the group's purpose.",
            f"Irrelevant content: '{message_content}' at {message_link}. This message in {chat_title} is off-topic and should be removed. {context_info}.",
            f"This message is completely irrelevant for {chat_title} at {message_link}. It adds no value and should be deleted. The content: '{message_content}'.",
            f"Off-topic content found at {message_link} in {chat_title}. This {message_type} is not relevant to the chat's purpose or region. Please remove it to maintain focus. {context_info}.",
            f"Reporting irrelevant content: {message_link}. This user is consistently posting material that is not aligned with the group's purpose or geographic scope in {chat_title}. Please intervene."
        ],
        '8': [  
            f"This {message_type} ({message_link}) contains false information and is misleading. It should be removed to prevent misinformation.",
            f"The message ({message_link}) posted in {chat_title} is deceptive and spreads fake news. This is harmful to users.",
            f"Fabricated claims were shared through this {message_type} ({message_link}) in {chat_title}. This needs to be labeled or removed.",
            f"False information: '{message_content}' at {message_link}. This message in {chat_title} is misleading and should be taken down. {context_info}.",
            f"This message contains deliberate falsehoods at {message_link}. It is crucial to remove this misinformation immediately. The content: '{message_content}'.",
            f"Misinformation detected at {message_link} in {chat_title}. This {message_type} contains false or misleading content. Please ensure it is addressed promptly. {context_info}.",
            f"Reporting fake content: {message_link}. This user is spreading fabricated information in {chat_title}. Please take appropriate action to combat this misinformation."
        ],
        '9': [  
            f"This {message_type} ({message_link}) promotes illegal drug use. This content is dangerous and must be removed.",
            f"The message ({message_link}) posted in {chat_title} facilitates drug trafficking or glorifies narcotics. Urgent action is required.",
            f"Content related to illegal substances was shared through this {message_type} ({message_link}) in {chat_title}. This is a serious violation.",
            f"Drug-related content: '{message_content}' at {message_link}. This message promotes illegal substances in {chat_title} and needs immediate removal. {context_info}.",
            f"Illegal drug promotion found at {message_link}. This content is highly dangerous and must be removed immediately. The content: '{message_content}'.",
            f"Narcotics content reported at {message_link} in {chat_title}. This {message_type} contains material promoting illegal drug activities. Please act swiftly to remove it. {context_info}.",
            f"Reporting drug promotion: {message_link}. This user is sharing content related to illegal drugs in {chat_title}. Please ensure this content is deleted and investigated thoroughly."
        ]
    }

    russian_templates = {
        '1': [
            f"Этот {message_type} ({message_link}) содержит явный спам. Он продвигает нежелательные услуги и нарушает общение.",
            f"Пользователь рассылает нежелательный рекламный контент ({message_link}) в {chat_title}. Это нарушение политики спама.",
            f"Обнаружена массовая рассылка через этот {message_type} ({message_link}) в {chat_title}. Примите меры против этого спамера.",
            f"Это сообщение является спамом: «{message_content}». Его необходимо удалить из {chat_title} как можно скорее. {context_info}.",
            f"Был опубликован неприемлемый спам. Ссылка на сообщение: {message_link}. Крайне важно немедленно решить эту проблему. Содержимое: «{message_content}».",
            f"Входящее спам-сообщение идентифицировано по адресу {message_link} в {chat_title}. Оно содержит нежелательный материал. Этот пользователь злоупотребляет платформой. Пожалуйста, примите меры. {context_info}.",
            f"Жалоба на спам: {message_link}. Этот пользователь неоднократно отправляет нежелательный коммерческий контент в {chat_title}. Это ухудшает пользовательский опыт. Просим вмешаться."
        ],
        '2': [
            f"Этот {message_type} ({message_link}) содержит угрозы насилия. Этот контент представляет опасность для пользователей и должен быть удален.",
            f"Сообщение ({message_link}), опубликованное в {chat_title}, подстрекает к насилию и пропагандирует вредоносное поведение. Требуются срочные меры.",
            f"Графический контент с насилием был опубликован через этот {message_type} ({message_link}) в {chat_title}. Это серьезное нарушение.",
            f"Срочный отчет: сообщение «{message_content}» по адресу {message_link} пропагандирует насилие. Это крайне неуместно для {chat_title} и должно быть рассмотрено. {context_info}.",
            f"Этот контент крайне тревожен: «{message_content}» по адресу {message_link}. Он явно призывает к насилию и является неприемлемым.",
            f"Насилие распространяется через {message_link} в {chat_title}. Этот {message_type} пропагандирует агрессивные и вредоносные действия. Немедленное удаление обязательно. {context_info}.",
            f"Сообщаем о насильственном контенте: {message_link}. Этот пользователь публикует материалы, которые могут причинить серьезный вред или дистресс в {chat_title}. Пожалуйста, примите оперативные меры."
        ],
        '3': [
            f"Этот {message_type} ({message_link}) содержит материалы о сексуальном насилии над детьми. Это незаконно и крайне опасно.",
            f"Сообщение ({message_link}), опубликованное в {chat_title}, содержит материалы, связанные с эксплуатацией несовершеннолетних. Правоохранительные органы должны быть немедленно уведомлены.",
            f"Незаконный контент, изображающий сексуальное насилие над детьми, был опубликован через этот {message_type} ({message_link}) в {chat_title}. Это требует немедленного вмешательства.",
            f"Это сообщение «{message_content}» по адресу {message_link} содержит явные признаки угрозы для детей. Это серьезное уголовное преступление, требующее немедленного расследования в {chat_title}. {context_info}.",
            f"КРИТИЧЕСКИЙ ОТЧЕТ: Материалы о жестоком обращении с детьми найдены по адресу {message_link}. Этот контент является незаконным и должен быть удален и сообщен властям. Содержимое: «{message_content}».",
            f"Контент, связанный с эксплуатацией детей, обнаружен по адресу {message_link} в {chat_title}. Этот {message_type} содержит незаконные материалы, касающиеся несовершеннолетних. Крайне важно действовать немедленно и привлечь правоохранительные органы. {context_info}.",
            f"Срочный отчет о безопасности детей: {message_link}. Этот пользователь поделился контентом, который эксплуатирует детей в {chat_title}. Пожалуйста, обеспечьте наивысший приоритет в обработке и сообщите об этом соответствующим органам."
        ],
        '4': [
            f"Этот {message_type} ({message_link}) содержит откровенные порнографические материалы. Этот контент не подходит для платформы.",
            f"Сообщение ({message_link}), опубликованное в {chat_title}, содержит материалы сексуального характера. Это нарушает правила платформы.",
            f"Контент NSFW был опубликован через этот {message_type} ({message_link}) в {chat_title}. Это неприемлемо и должно быть удалено.",
            f"Обнаружен откровенный контент: «{message_content}» по адресу {message_link}. Это неприемлемо для {chat_title} и должно быть удалено. {context_info}.",
            f"Это сообщение содержит порнографические материалы по адресу {message_link}. Крайне важно немедленно удалить этот контент. Содержимое: «{message_content}».",
            f"Порнографический материал найден по адресу {message_link} в {chat_title}. Этот {message_type} содержит крайне откровенный контент. Пожалуйста, обеспечьте его немедленное удаление. {context_info}.",
            f"Сообщаем о неприемлемом контенте для взрослых: {message_link}. Этот пользователь публикует откровенные материалы в {chat_title}, которые нарушают стандарты сообщества. Пожалуйста, примите соответствующие меры."
        ],
        '5': [
            f"Этот {message_type} ({message_link}) нарушает авторские права. Контент используется без разрешения.",
            f"Сообщение ({message_link}), опубликованное в {chat_title}, содержит несанкционированный контент, защищенный авторским правом. Это явное нарушение прав интеллектуальной собственности.",
            f"Пиратский контент был опубликован через этот {message_type} ({message_link}) в {chat_title}. Это должно быть немедленно удалено.",
            f"Нарушение авторских прав: «{message_content}» по адресу {message_link}. Этот контент в {chat_title} является украденным и должен быть удален. {context_info}.",
            f"Несанкционированное использование материалов, защищенных авторским правом, найдено по адресу {message_link}. Пожалуйста, немедленно удалите это. Содержимое: «{message_content}».",
            f"Сообщение о нарушении авторских прав по адресу {message_link} в {chat_title}. Этот {message_type} содержит интеллектуальную собственность, которая не лицензирована для использования. Пожалуйста, примите меры по ее удалению. {context_info}.",
            f"Сообщаем о нарушении авторских прав: {message_link}. Этот пользователь распространяет материалы, защищенные авторским правом, без разрешения в {chat_title}. Пожалуйста, убедитесь, что этот контент удален и применены санкции."
        ],
        '6': [
            f"Этот {message_type} ({message_link}) раскрывает личные данные. Это нарушение конфиденциальности и риск для пользователей.",
            f"Сообщение ({message_link}), опубликованное в {chat_title}, раскрывает конфиденциальную личную информацию. Это серьезное нарушение конфиденциальности.",
            f"Несанкционированные личные данные были опубликованы через этот {message_type} ({message_link}) в {chat_title}. Это должно быть удалено и расследовано.",
            f"Нарушение конфиденциальности: «{message_content}» по адресу {message_link}. Это сообщение раскрывает личную информацию в {chat_title} и должно быть удалено. {context_info}.",
            f"Конфиденциальные личные данные найдены по адресу {message_link}. Это прямое нарушение конфиденциальности и требует немедленного удаления. Содержимое: «{message_content}».",
            f"Сообщение об утечке личных данных по адресу {message_link} в {chat_title}. Этот {message_type} содержит конфиденциальную информацию пользователя. Необходимы немедленные меры по обеспечению безопасности и удалению этих данных. {context_info}.",
            f"Сообщаем о раскрытии личных данных: {message_link}. Этот пользователь делится личной информацией в {chat_title} без согласия. Пожалуйста, убедитесь, что этот контент удален, и пользователь привлечен к ответственности."
        ],
        '7': [
            f"Этот {message_type} ({message_link}) является не по теме и неактуален для {chat_title}. Он нарушает фокус сообщества.",
            f"Сообщение ({message_link}), опубликованное в {chat_title}, не соответствует географии и не подходит для этого региона/группы. Пожалуйста, удалите его.",
            f"Разрушительный контент был опубликован через этот {message_type} ({message_link}) в {chat_title}. Он не соответствует цели группы.",
            f"Неактуальный контент: «{message_content}» по адресу {message_link}. Это сообщение в {chat_title} не по теме и должно быть удалено. {context_info}.",
            f"Это сообщение совершенно неактуально для {chat_title} по адресу {message_link}. Оно не добавляет ценности и должно быть удалено. Содержимое: «{message_content}».",
            f"Неактуальный контент найден по адресу {message_link} в {chat_title}. Этот {message_type} не относится к цели чата или региону. Пожалуйста, удалите его, чтобы сохранить фокус. {context_info}.",
            f"Сообщаем о неактуальном контенте: {message_link}. Этот пользователь постоянно публикует материалы, которые не соответствуют цели группы или географическому охвату в {chat_title}. Пожалуйста, вмешайтесь."
        ],
        '8': [
            f"Этот {message_type} ({message_link}) содержит ложную информацию и вводит в заблуждение. Его следует удалить, чтобы предотвратить дезинформацию.",
            f"Сообщение ({message_link}), опубликованное в {chat_title}, является обманчивым и распространяет фейковые новости. Это вредно для пользователей.",
            f"Вымышленные утверждения были опубликованы через этот {message_type} ({message_link}) в {chat_title}. Это должно быть помечено или удалено.",
            f"Ложная информация: «{message_content}» по адресу {message_link}. Это сообщение в {chat_title} вводит в заблуждение и должно быть удалено. {context_info}.",
            f"Это сообщение содержит преднамеренную ложь по адресу {message_link}. Крайне важно немедленно удалить эту дезинформацию. Содержимое: «{message_content}».",
            f"Дезинформация обнаружена по адресу {message_link} в {chat_title}. Этот {message_type} содержит ложный или вводящий в заблуждение контент. Пожалуйста, убедитесь, что он будет оперативно рассмотрен. {context_info}.",
            f"Сообщаем о фейковом контенте: {message_link}. Этот пользователь распространяет вымышленную информацию в {chat_title}. Пожалуйста, примите соответствующие меры для борьбы с этой дезинформацией."
        ],
        '9': [
            f"Этот {message_type} ({message_link}) пропагандирует употребление нелегальных наркотиков. Этот контент опасен и должен быть удален.",
            f"Сообщение ({message_link}), опубликованное в {chat_title}, способствует торговле наркотиками или прославляет их. Требуются срочные меры.",
            f"Контент, связанный с запрещенными веществами, был опубликован через этот {message_type} ({message_link}) в {chat_title}. Это серьезное нарушение.",
            f"Контент, связанный с наркотиками: «{message_content}» по адресу {message_link}. Это сообщение пропагандирует запрещенные вещества в {chat_title} и требует немедленного удаления. {context_info}.",
            f"Обнаружена пропаганда запрещенных наркотиков по адресу {message_link}. Этот контент крайне опасен и должен быть немедленно удален. Содержимое: «{message_content}».",
            f"Сообщение о контенте, связанном с наркотиками, по адресу {message_link} в {chat_title}. Этот {message_type} содержит материалы, пропагандирующие незаконную деятельность, связанную с наркотиками. Пожалуйста, примите оперативные меры по его удалению. {context_info}.",
            f"Сообщаем о пропаганде наркотиков: {message_link}. Этот пользователь делится контентом, связанным с запрещенными наркотиками, в {chat_title}. Пожалуйста, убедитесь, что этот контент удален и тщательно расследован."
        ]
    }

    report_parts = []
    
    if random.random() < 0.5:
        report_parts.append(random.choice(english_templates[option]))
        if chat_id and chat_title:
            report_parts.append(f"The message was posted in chat '{chat_title}' (ID: {chat_id}).")
        elif chat_id:
            report_parts.append(f"The message was posted in chat with ID: {chat_id}.")
        elif chat_title:
            report_parts.append(f"The message was posted in chat: '{chat_title}'.")
        
        actions_eng = [
            "Immediate removal and account termination are required.",
            "Please delete this content and apply appropriate sanctions.",
            "Urgent removal of this material and user suspension are necessary."
        ]
        report_parts.append(random.choice(actions_eng))
    else:
        report_parts.append(random.choice(russian_templates[option]))
        if chat_id and chat_title:
            report_parts.append(f"Сообщение было отправлено в чат «{chat_title}» (ID: {chat_id}).")
        elif chat_id:
            report_parts.append(f"Сообщение было отправлено в чат с ID: {chat_id}.")
        elif chat_title:
            report_parts.append(f"Сообщение было отправлено в чат: «{chat_title}».")
            
        actions_rus = [
            "Требуется немедленное удаление и блокировка аккаунта.",
            "Пожалуйста, удалите этот контент и примените соответствующие санкции.",
            "Срочно удалите этот материал и заблокируйте пользователя."
        ]
        report_parts.append(random.choice(actions_rus))

    return "\n".join(report_parts)


###
@dp.message_handler(state=ChannelDemolitionStates.channel_link)
async def process_channel_link_step(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id in banned_users:
        await message.answer('<b>📢 Администратор посчитал ваш аккаунт подозрительным, и вы были забанены. 📢</b>', parse_mode="HTML")
        return

    channel_links = message.text.split()
    if not all(re.match(r'^https://t\.me/[^/]+$|^https://t\.me/c/\d+$', link) for link in channel_links):
        await message.answer(
            '<b>❌ Неверный формат ссылки на канал.</b>\n'
            '<blockquote>Пожалуйста, введите ссылки в формате:\n'
            '<code>https://t.me/username</code>\n'
            '<code>https://t.me/c/channel_id</code></blockquote>',
            parse_mode="HTML"
        )
        return
    
    async with state.proxy() as data:
        data['channel_links'] = channel_links

    sessions = get_all_sessions()
    if not sessions:
        await message.answer('<b>❌ Нет доступных сессий. Пожалуйста, создайте аккаунт сначала.</b>', parse_mode="HTML")
        await state.finish()
        return
    search_message = await message.answer("<b>Идёт поиск постов</b>.", parse_mode="HTML")
    animations = [".", "..", "..."]
    animation_task = None
    
    async def animate_search():
        i = 0
        while True:
            try:
                await search_message.edit_text(f"<b>Идёт поиск постов</b> {animations[i % len(animations)]}", parse_mode="HTML")
                await asyncio.sleep(0.5)
                i += 1
            except errors.MessageNotModified:
                continue
            except Exception:
                break
    animation_task = asyncio.create_task(animate_search())

    session = sessions[0]
    client = TelegramClient(session["path"], api_id=session["api_id"], api_hash=session["api_hash"])
    await client.connect()
    
    try:
        channels_info = {}
        target_channel_ids = set()
        for channel_link in channel_links:
            parts = channel_link.split('/')
            if parts[3] == 'c':
                channel_id = int(f"-100{parts[4]}")
                if channel_id in private_channel_ids:
                    await message.answer(f'<b>❌ Канал с ID</b> <code>{channel_id}</code> <b>является приватным и не может быть репорчен.</b>', parse_mode="HTML")
                    continue
                try:
                    channel = await client.get_entity(channel_id)
                except errors.ChannelPrivateError:
                    await message.answer(f'<b>❌ Канал с ID</b> <code>{channel_id}</code> <b>является приватным. Доступ запрещен.</b>', parse_mode="HTML")
                    continue
                except Exception as e:
                    logger.error(f"Ошибка при получении информации о канале: {e}")
                    await message.answer(f'<b>❌ Ошибка при обработке ссылки на канал.</b>', parse_mode="HTML")
                    continue
            else:
                channel_username = parts[3]
                try:
                    channel = await client.get_entity(channel_username)
                except errors.UsernameNotOccupiedError:
                    await message.answer(f'<b>❌ Канал с именем</b> <code>{channel_username}</code> <b>не существует.</b>', parse_mode="HTML")
                    continue
                except errors.ChannelPrivateError:
                    await message.answer(f'<b>❌ Канал</b> <code>{channel_username}</code> <b>является приватным. Доступ запрещен.</b>', parse_mode="HTML")
                    continue
            channel_id = channel.id
            if channel_id in private_channel_ids:
                await message.answer(f'<b>❌ Канал с ID</b> <code>{channel_id}</code> <b>является приватным и не может быть репорчен.</b>', parse_mode="HTML")
                continue

            try:
                await client(JoinChannelRequest(channel))
            except errors.ChannelPrivateError:
                await message.answer(f'<b>❌ Канал</b> <code>{channel_username}</code> <b>является приватным. Доступ запрещен.</b>', parse_mode="HTML")
                continue
            except errors.UserAlreadyParticipantError:
                pass  

            try:
                full_channel = await client(GetFullChannelRequest(channel))
                channel_members_count = full_channel.full_chat.participants_count if hasattr(full_channel.full_chat, 'participants_count') else "Скрыто"
                channel_creation_date = full_channel.full_chat.date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(full_channel.full_chat, 'date') else "Неизвестно"
            except Exception as e:
                logger.error(f"Ошибка при получении информации о канале: {e}")
                channel_members_count = "Скрыто"
                channel_creation_date = "Неизвестно"

            try:
                messages = await client.get_messages(channel, limit=None)
                message_ids = [msg.id for msg in messages]
                messages_count = len(message_ids)
                first_message_date = messages[-1].date.strftime("%Y-%m-%d %H:%M:%S") if messages else "Не найдено"
                last_message_id = messages[0].id if messages else None
            except Exception as e:
                logger.error(f"Ошибка при получении сообщений: {e}")
                message_ids = []
                messages_count = 0
                first_message_date = "Ошибка"
                last_message_id = None
            
            channel_info = f"@{channel.username}" if channel.username else f"ID: {channel.id}"
            
            if channel_info not in channels_info:
                channels_info[channel_info] = {
                    "channel_id": channel_id,
                    "channel_title": channel.title,
                    "channel_members_count": channel_members_count,
                    "channel_creation_date": channel_creation_date,
                    "first_message_date": first_message_date,
                    "last_message_id": last_message_id,
                    "messages_count": messages_count,
                    "message_ids": message_ids
                }
            
            target_channel_ids.add(channel.id)
        
        async with state.proxy() as data:
            data['target_channel_ids'] = list(target_channel_ids)
            data['channels_info'] = channels_info
        
        if animation_task:
            animation_task.cancel()
            try:
                await animation_task
            except (asyncio.CancelledError, Exception):
                pass
        report_message = "───── ⋆⋅☆⋅⋆ ─────<blockquote>\n"
        for channel_info, details in channels_info.items():
            report_message += (
                f"<b>📊 Информация о канале(ах):</b>\n"
                f"📢 <b>Канал:</b> <code>{channel_info}</code>\n"
                f"🆔 <b>ID канала:</b> <code>{details['channel_id']}</code>\n"
                f"📄 <b>Название канала:</b> <code>{details['channel_title']}</code>\n"
                f"👥 <b>Участников в канале:</b> <code>{details['channel_members_count']}</code>\n"
                f"📅 <b>Дата создания канала (приблизительно):</b> <code>{details['first_message_date']}</code>\n"
                f"📝 <b>Количество постов:</b> <code>{details['messages_count']}</code>\n"
                f"🔢 <b>ID последнего сообщения:</b> <code>{details['last_message_id']}</code></blockquote>\n"
                f"───── ⋆⋅☆⋅⋆ ─────\n\n"
            )
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton('🚫 Спам', callback_data='option_1'),
            InlineKeyboardButton('🔪 Насилие', callback_data='option_2'),
            InlineKeyboardButton('👶 Дети', callback_data='option_3'),
            InlineKeyboardButton('🔞 Порно', callback_data='option_4'),
            InlineKeyboardButton('©️ Авторство', callback_data='option_5'),
            InlineKeyboardButton('👤 Данные', callback_data='option_6'),
            InlineKeyboardButton('🌍 Гео', callback_data='option_7'),
            InlineKeyboardButton('🎭 Фейк', callback_data='option_8'),
            InlineKeyboardButton('💊 Наркотики', callback_data='option_9')
        )
        
        report_message += "\n<b>🚨 Выберите причину репорта:</b>"
        await search_message.edit_text(report_message, reply_markup=markup, parse_mode="HTML")
        await ChannelDemolitionStates.option.set()
    except errors.FloodWaitError as e:
        logger.error(f"FloodWaitError: {e}")
        if animation_task:
            animation_task.cancel()
        await asyncio.sleep(e.seconds)
        await message.answer('<b>❌ Ошибка при получении сообщений. Попробуйте позже.</b>', parse_mode="HTML")
        await state.finish()
    except Exception as e:
        logger.error(f"Error: {e}")
        if animation_task:
            animation_task.cancel()
        await message.answer('<b>❌ Ошибка при получении сообщений.</b>', parse_mode="HTML")
        await state.finish()
    finally:
        if animation_task and not animation_task.done():
            animation_task.cancel()
        await client.disconnect()
        
@dp.callback_query_handler(lambda c: c.data.startswith('option_'), state=ChannelDemolitionStates.option)
async def process_channel_report(call: types.CallbackQuery, state: FSMContext):
    try:
        user_id = call.from_user.id
        
        if user_id in user_last_report_time:
            time_since_last_report = datetime.now() - user_last_report_time[user_id]
            if time_since_last_report < timedelta(minutes=2):
                remaining_time = timedelta(minutes=2) - time_since_last_report
                minutes = remaining_time.seconds // 60
                seconds = remaining_time.seconds % 60
                await call.answer(
                    f"⏳ Подождите {minutes:02d}:{seconds:02d} минут",
                    show_alert=True
                )
                return

        option = call.data.split('_')[1]
        await call.answer()  
        
        async with state.proxy() as data:
            data['option'] = option
            channel_links = data['channel_links']
            channels_info = data.get('channels_info', {})
            
        await send_channel_reports(call, None, state)  
        user_last_report_time[user_id] = datetime.now()

    except Exception as e:
        logger.error(f"Channel report error: {str(e)}")
        await call.message.answer(f'❌ Ошибка: {str(e)}')          
        
async def send_channel_reports(call: types.CallbackQuery, report_msg: types.Message, state: FSMContext):
    try:
        user_id = call.from_user.id
        async with state.proxy() as data:
            channel_links = data['channel_links']
            option = data['option']
            channels_info = data.get('channels_info', {})

        sessions = get_all_sessions()
        if not sessions:
            await call.message.answer('❌ Нет доступных сессий.')
            await state.finish()
            return
        def ensure_session_json(session_path):
            json_path = os.path.splitext(session_path)[0] + '.json'
            if not os.path.exists(json_path):
                default_data = {
                    "status": "Свободна",
                    "last_used": None,
                    "usage_count": 0,
                    "reports_sent": 0,
                    "errors": 0
                }
                with open(json_path, 'w') as f:
                    json.dump(default_data, f)
            return json_path
        for session in sessions:
            session['json_path'] = ensure_session_json(session['path'])

        option_names = {
            "1": "Спам",
            "2": "Насилие",
            "3": "Насилие над детьми",
            "4": "Порнография",
            "5": "Нарушение авторских прав",
            "6": "Личные данные",
            "7": "Геонерелевантный",
            "8": "Фальшивка",
            "9": "Наркотики"
        }
        stats = {
            'total': 0,
            'failed': 0,
            'active_sessions': 0,
            'flood': 0,
            'private': [],
            'last_text': "—",
            'last_update': None
        }

        result_message = await call.message.edit_text(
            "───── ⋆⋅☆⋅⋆ ─────\n"
            "<blockquote>📊 <b>Статус отправки репортов:</b>\n"
            f"✅ Успешно: <code>0</code>\n"
            f"❌ Неудачно: <code>0</code>\n"
            f"🔄 Активных сессий: <code>0</code>\n"
            f"⏳ FloodWait: <code>0</code>\n"
            f"📝 Текст репорта: <code>—</code></blockquote>\n"
            "───── ⋆⋅☆⋅⋆ ─────",
            parse_mode="HTML"
        )

        async def update_status(force=False):
            now = datetime.now()
            if not force and stats['last_update'] and (now - stats['last_update']).total_seconds() < 2:
                return

            try:
                text = f"""───── ⋆⋅☆⋅⋆ ─────
<blockquote>📊 <b>Статус:</b>
✅ Успешно: <code>{stats['total']}</code>
❌ Ошибки: <code>{stats['failed']}</code>
🔄 Активных сессий: <code>{stats['active_sessions']}</code>
⏳ FloodWait: <code>{stats['flood']}</code>
📝 Текст репорта: <code>{stats['last_text']}</code>"""
                
                if stats['private']:
                    text += f"\n🔒 Пропущено приватных каналов: <code>{len(stats['private'])}</code>"
                
                text += "</blockquote>\n───── ⋆⋅☆⋅⋆ ─────"
                current_text = result_message.text if hasattr(result_message, 'text') else ""
                if force or text != current_text:
                    await result_message.edit_text(text, parse_mode="HTML")
                    stats['last_update'] = now
            except exceptions.MessageNotModified:
                pass
            except Exception as e:
                logger.error(f"Ошибка при обновлении статуса: {str(e)}")

        async def process_channel(session_data, channel_link, message_ids):
            client = None
            try:
                async with session_lock:
                    with open(session_data["json_path"], 'r+') as f:
                        data = json.load(f)
                        if data.get("status") != "Свободна":
                            return False
                        data["status"] = "Занята"
                        data["last_used"] = datetime.now().isoformat()
                        f.seek(0)
                        json.dump(data, f)
                        f.truncate()
                
                stats['active_sessions'] += 1
                await update_status()
                
                client = TelegramClient(session_data["path"], session_data["api_id"], session_data["api_hash"])
                await client.connect()
                
                if not await client.is_user_authorized():
                    stats['failed'] += len(message_ids)
                    return False

                parts = channel_link.split('/')
                if parts[3] == 'c':
                    chat_id = int('-100' + parts[4])
                    try:
                        chat = await client.get_entity(PeerChannel(chat_id))
                    except errors.ChannelPrivateError:
                        stats['private'].append(f"channel{chat_id}")
                        return False
                else:
                    channel_username = parts[3]
                    try:
                        chat = await client.get_entity(channel_username)
                    except errors.UsernameNotOccupiedError:
                        stats['failed'] += len(message_ids)
                        return False
                    except errors.ChannelPrivateError:
                        stats['private'].append(channel_username)
                        return False

                try:
                    await client(JoinChannelRequest(chat))
                except errors.UserAlreadyParticipantError:
                    pass
                except errors.ChannelPrivateError:
                    stats['private'].append(channel_username if 'username' in dir(chat) else f"channel{chat.id}")
                    return False

                report_option = option_mapping.get(option, "0")
                successful_reports = 0
                
                for message_id in message_ids:
                    try:
                        target_message = await client.get_messages(chat, ids=message_id)
                        if not target_message:
                            stats['failed'] += 1
                            continue

                        stats['last_text'] = generate_channel_report_text(chat, channel_link, option, target_message)
                        
                        await client(ReportRequest(
                            peer=chat,
                            id=[message_id],
                            option=report_option,
                            message=stats['last_text']
                        ))
                        
                        successful_reports += 1
                        stats['total'] += 1
                    except errors.FloodWaitError as e:
                        stats['flood'] += 1
                        await asyncio.sleep(e.seconds)
                        stats['failed'] += 1
                        break
                    except Exception as e:
                        logger.error(f"Ошибка при отправке репорта: {str(e)}")
                        stats['failed'] += 1
                async with session_lock:
                    with open(session_data["json_path"], 'r+') as f:
                        data = json.load(f)
                        data["usage_count"] = data.get("usage_count", 0) + 1
                        data["reports_sent"] = data.get("reports_sent", 0) + successful_reports
                        data["errors"] = data.get("errors", 0) + (len(message_ids) - successful_reports)
                        f.seek(0)
                        json.dump(data, f)
                        f.truncate()
                
                return successful_reports > 0

            except Exception as e:
                logger.error(f"Ошибка при отправке репорта: {str(e)}")
                stats['failed'] += len(message_ids)
                return False
            finally:
                if client:
                    await client.disconnect()
                async with session_lock:
                    with open(session_data["json_path"], 'r+') as f:
                        data = json.load(f)
                        data["status"] = "Свободна"
                        f.seek(0)
                        json.dump(data, f)
                        f.truncate()
                
                stats['active_sessions'] -= 1
                await update_status()
        session_lock = asyncio.Lock()        
        tasks = []
        for channel_link in channel_links:
            parts = channel_link.split('/')
            channel_identifier = parts[3] if parts[3] != 'c' else parts[4]
            channel_info = channels_info.get(f"@{channel_identifier}" if parts[3] != 'c' else f"ID: -100{parts[4]}", {})
            message_ids = channel_info.get('message_ids', [])
            
            if not message_ids:
                continue
                
            for session in sessions:
                task = asyncio.create_task(process_channel(session, channel_link, message_ids))
                tasks.append(task)
                await asyncio.sleep(0.1) 
        await asyncio.gather(*tasks)
        await update_status(force=True)

        report_details = f"""───── ⋆⋅☆⋅⋆ ─────
<blockquote>🎉 <b>Отчет о репортах</b>
📌 <b>Причина:</b> <code>{option_names.get(option, 'Неизвестно')}</code>
✅ <b>Успешно:</b> <code>{stats['total']}</code>
❌ <b>Неудачно:</b> <code>{stats['failed']}</code>"""
        
        if stats['private']:
            report_details += f"\n🔒 <b>Пропущено приватных каналов:</b> <code>{len(stats['private'])}</code>"
        
        report_details += f"\n</blockquote>───── ⋆⋅☆⋅⋆ ─────"
        
        try:
            await result_message.edit_text(report_details, parse_mode="HTML")
        except exceptions.MessageNotModified:
            pass
        except Exception as e:
            logger.error(f"Ошибка при отправке финального отчета: {str(e)}")

        await state.finish()
        user_last_report_time[user_id] = datetime.now()

    except Exception as e:
        logger.error(f"Error in send_channel_reports: {str(e)}")
        await call.message.answer(f'❌ Произошла ошибка: {str(e)}')

from aiogram.dispatcher.filters.state import State, StatesGroup
    
def generate_channel_report_text(channel, channel_link, option, target_message):
    if channel.username:
        channel_mention = f"@{channel.username}"
    else:
        channel_mention = f"channel with ID {channel.id}"
    channel_name = channel.title if hasattr(channel, 'title') else "unknown channel"

    reason_text = reason_mapping.get(option, "unknown reason")
    template_parts = {
        '1': {  
            'intros': [
                f"Channel {channel_mention} is engaged in spamming, violating platform rules and creating a negative user experience.",
                f"Suspicious activity has been observed in channel {channel_mention}, indicating the distribution of unwanted advertising messages.",
                f"The content of channel {channel_mention} mainly consists of intrusive advertising and links to third-party resources, which is classified as spam.",
            ],
            'mains': [
                f"Link to the channel: {channel_link}. The channel systematically publishes advertising materials that are of no value to the audience.",
                f"The channel violates the platform's policy by distributing spam. {channel_link} is a prime example of the spam activity of this channel.",
                f"We ask you to pay attention to the channel {channel_mention}, which abuses spam distribution. Details: {channel_link}.",
            ],
            'conclusions': [
                "We ask you to take the necessary measures to stop the spam activity of this channel and protect users from unwanted information.",
                "We consider it necessary to block this channel and delete the spam content published by it.",
                "We hope for a prompt response and action on this spam incident.",
            ]
        },
        '2': {  
            'intros': [
                f"Channel {channel_mention} contains content that promotes violence and cruelty, which is a serious violation of platform rules.",
                f"Materials that can provoke aggression and hatred in society have been found in channel {channel_mention}.",
                f"The content of channel {channel_mention} is aimed at spreading ideas of violence and intolerance, which is unacceptable.",
            ],
            'mains': [
                f"Link to the channel: {channel_link}. The channel publishes shocking content containing scenes of violence.",
                f"This channel violates safety principles by distributing materials related to violence. {channel_link} confirms the presence of such content.",
                f"We ask you to take action against channel {channel_mention}, which promotes violence. Details: {channel_link}.",
            ],
            'conclusions': [
                "We call for the immediate blocking of channel {channel_mention} and the removal of all materials promoting violence.",
                "We consider it necessary to conduct a thorough check of the channel for the presence of other content related to violence and take appropriate measures.",
                "Decisive measures must be taken to prevent the spread of violence and cruelty through this channel.",
            ]
        },
        '3': {  
            'intros': [
                f"Channel {channel_mention} contains materials related to child abuse.",
                f"Content that exploits children has been found in channel {channel_mention}.",
                f"The content of channel {channel_mention} poses a threat to children.",
            ],
            'mains': [
                f"Link to the channel: {channel_link}. The channel violates the rules by distributing content related to child abuse.",
                f"This channel is involved in the distribution of child abuse materials. {channel_link} confirms the presence of such content.",
                f"We ask you to take immediate action against channel {channel_mention}, which distributes child abuse content. Details: {channel_link}.",
            ],
            'conclusions': [
                "We urge the immediate blocking of channel {channel_mention} and the removal of all materials related to child abuse.",
                "We consider it necessary to conduct a thorough check of the channel for the presence of other illegal content and take appropriate measures.",
                "It is necessary to take decisive measures to prevent the distribution of child abuse materials through this channel.",
            ]
        },
        '4': { 
            'intros': [
                f"Channel {channel_mention} distributes pornographic materials.",
                f"Content of a pornographic nature has been found in channel {channel_mention}.",
                f"The content of channel {channel_mention} is sexually explicit and violates platform rules.",
            ],
            'mains': [
                f"Link to the channel: {channel_link}. The channel violates the rules by distributing pornography.",
                f"This channel is involved in the distribution of pornographic materials. {channel_link} confirms the presence of such content.",
                f"We ask you to take action against channel {channel_mention}, which distributes pornography. Details: {channel_link}.",
            ],
            'conclusions': [
                "We urge the immediate blocking of channel {channel_mention} and the removal of all pornographic materials.",
                "We consider it necessary to conduct a thorough check of the channel for the presence of other illegal content and take appropriate measures.",
                "It is necessary to take decisive measures to prevent the distribution of pornography through this channel.",
            ]
        },
        '5': {  
            'intros': [
                f"Channel {channel_mention} infringes copyright.",
                f"The use of someone else's content without permission has been found in channel {channel_mention}.",
                f"The content of channel {channel_mention} violates intellectual property rights.",
            ],
            'mains': [
                f"Link to the channel: {channel_link}. The channel violates copyright by distributing someone else's content.",
                f"This channel is involved in copyright infringement. {channel_link} confirms the presence of such content.",
                f"We ask you to take action against channel {channel_mention}, which infringes copyright. Details: {channel_link}.",
            ],
            'conclusions': [
                "We urge the removal of the infringing content from channel {channel_mention}.",
                "We consider it necessary to conduct a thorough check of the channel for the presence of other infringing content and take appropriate measures.",
                "It is necessary to take measures to protect copyright holders from the distribution of their content through this channel.",
            ]
        },
        '6': {  
            'intros': [
                f"Channel {channel_mention} distributes users' personal data.",
                f"Disclosure of personal information has been found in channel {channel_mention}.",
                f"The content of channel {channel_mention} violates the privacy of users.",
            ],
            'mains': [
                f"Link to the channel: {channel_link}. The channel violates the rules by distributing personal data.",
                f"This channel is involved in the distribution of personal data. {channel_link} confirms the presence of such content.",
                f"We ask you to take immediate action against channel {channel_mention}, which distributes personal data. Details: {channel_link}.",
            ],
            'conclusions': [
                "We urge the immediate blocking of channel {channel_mention} and the removal of all personal data.",
                "We consider it necessary to conduct a thorough check of the channel for the presence of other confidential information and take appropriate measures.",
                "It is necessary to take decisive measures to prevent the distribution of personal data through this channel.",
            ]
        },
        '7': {  
            'intros': [
                f"The content of channel {channel_mention} does not correspond to the geographical focus.",
                f"Channel {channel_mention} publishes content that is not relevant to the region.",
                f"The content of channel {channel_mention} is not intended for the target audience.",
            ],
            'mains': [
                f"Link to the channel: {channel_link}. The channel publishes geo-irrelevant content.",
                f"This channel distributes content that is not relevant to the specified region. {channel_link} confirms the presence of such content.",
                f"We ask you to take action against channel {channel_mention}, which distributes geo-irrelevant content. Details: {channel_link}.",
            ],
            'conclusions': [
                "We recommend changing the geographical focus of channel {channel_mention} or removing the irrelevant content.",
                "We consider it necessary to conduct a thorough check of the channel for the presence of other geo-irrelevant content and take appropriate measures.",
                "It is necessary to take measures to ensure that the content of the channel corresponds to the specified geographical focus.",
            ]
        },
       '8': {  
            'intros': [
                f"Channel {channel_mention} spreads fake information.",
                f"False information has been found in channel {channel_mention}.",
                f"The content of channel {channel_mention} is misleading and untrue.",
            ],
            'mains': [
                f"Link to the channel: {channel_link}. The channel spreads fakes and misinformation.",
                f"This channel is involved in the distribution of fake information. {channel_link} confirms the presence of such content.",
                f"We ask you to take action against channel {channel_mention}, which spreads fake information. Details: {channel_link}.",
            ],
            'conclusions': [
                "We urge the removal of fake information from channel {channel_mention}.",
                "We consider it necessary to conduct a thorough check of the channel for the presence of other fake information and take appropriate measures.",
                "It is necessary to take measures to prevent the distribution of fake information through this channel.",
            ]
        },
        '9': {  
            'intros': [
                f"Channel {channel_mention} promotes drugs.",
                f"Content related to drugs has been found in channel {channel_mention}.",
                f"The content of channel {channel_mention} is related to the illegal circulation of drugs.",
            ],
            'mains': [
                f"Link to the channel: {channel_link}. The channel violates the rules by distributing information about drugs.",
                f"This channel is involved in the distribution of drug-related content. {channel_link} confirms the presence of such content.",
                f"We ask you to take immediate action against channel {channel_mention}, which distributes information about drugs. Details: {channel_link}.",
            ],
            'conclusions': [
                "We urge the immediate blocking of channel {channel_mention} and the removal of all drug-related materials.",
                "We consider it necessary to conduct a thorough check of the channel for the presence of other illegal content and take appropriate measures.",
                "It is necessary to take decisive measures to prevent the distribution of information about drugs through this channel.",
            ]
        },
    }

    if option in template_parts:
        intro = random.choice(template_parts[option]['intros'])
        main = random.choice(template_parts[option]['mains'])
        conclusion = random.choice(template_parts[option]['conclusions'])
        return f"{intro}{main}{conclusion}"
    else:
        return f"Report on channel {channel_mention}. Reason: {reason_text}. Link: {channel_link}."
        