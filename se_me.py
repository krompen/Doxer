import os
import json
import zipfile
import rarfile
from telethon.tl.types import User
from telethon.errors import SessionPasswordNeededError, AuthKeyDuplicatedError
from telethon.tl.functions.users import GetFullUserRequest


from states import CheckSessionStates, DeleteNonMainSessionStates, DeleteSessionStates
from config import dp, bot, logger, clients

import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from telethon import TelegramClient, errors
from aiogram.dispatcher import FSMContext
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from aiogram import types
from telethon.sessions import StringSession
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import JoinChannelRequest, GetFullChannelRequest
from telethon.sessions import SQLiteSession
from aiogram import types
from aiogram.dispatcher import FSMContext
import asyncio
import sqlite3
from telethon import TelegramClient
from aiogram.dispatcher.filters.state import State, StatesGroup 
import aiohttp
import asyncio
import logging
import time
import os
import random
import smtplib
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


async def find_session_files_in_dir(directory: str) -> list:
    session_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.session'):
                session_files.append(os.path.join(root, file))
    return session_files

@dp.callback_query_handler(text='sessionOsn_menu', state='*')
async def sessionOsn_menu_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    email_message = """
<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote>
<b>📤 Загрузить .session</b> - Загрузить существующий сессионный файл.
<b>📥 Добавить .sesion</b> - Создать новый сессионный файл.
<b>🗑 Удалить .sesion</b> - Функция удаления сессионный файлов.
<b>📋 Проверить .sesion</b> - Функция проверки sesion 
🔙 <b>Назад</b> - Вернуться в админ панель.
</blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>
"""    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton('📤 Загрузить .session', callback_data='upload_session'),
        InlineKeyboardButton('📥 Добавить .sesion', callback_data='create_account'),
        InlineKeyboardButton('🗑 Удалить .sesion', callback_data='delete_sessionOsn'),
        InlineKeyboardButton('📋 Проверить .sesion', callback_data='list_sessionOsn'),
        InlineKeyboardButton('🔙 Назад', callback_data='admin_panel')
    )
    
    try:
        await bot.edit_message_caption(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            caption=email_message,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=email_message,
            reply_markup=markup,
            parse_mode="HTML"
        )
    await callback_query.answer()

@dp.callback_query_handler(text='upload_session', state='*')
async def upload_session_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "📤 Отправьте .session файл или архив (.zip/.rar) с .session файлами")
    await state.set_state("waiting_for_session_file")

@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, state="waiting_for_session_file")
async def handle_session_file(message: types.Message, state: FSMContext):
    try:
        if not os.path.exists("Session"):
            os.makedirs("Session")
        for client_info in clients:
            os.makedirs(os.path.join("Session", client_info["name"]), exist_ok=True)
        
        file_id = message.document.file_id
        file_name = message.document.file_name
        file_ext = os.path.splitext(file_name)[1].lower()
        
        file = await bot.get_file(file_id)
        downloaded_file = await bot.download_file(file.file_path)
        
        if file_ext == '.session':
            await process_single_session(downloaded_file, file_name, message)
        elif file_ext in ('.zip', '.rar'):
            await process_archive_file(downloaded_file, file_ext, message)
        else:
            await message.reply("❌ Отправьте .session, .zip или .rar файл")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {str(e)}")
    finally:
        await state.finish()

async def process_single_session(downloaded_file, file_name, message):
    if not clients:
        await message.reply("❌ Нет доступных клиентов!")
        return
    
    target_folder = random.choice(clients)["name"]
    target_path = os.path.join("Session", target_folder, file_name)
    
    if os.path.exists(target_path):
        await message.reply(f"❌ Файл {file_name} уже существует в папке {target_folder}!")
        return
    
    with open(target_path, 'wb') as new_file:
        new_file.write(downloaded_file.getvalue())
    
    session_name = os.path.splitext(file_name)[0]
    json_file = os.path.join("Session", target_folder, f"{session_name}.json")
    
    client_data = next((c for c in clients if c["name"] == target_folder), None)
    
    if not os.path.exists(json_file):
        with open(json_file, 'w') as f:
            json.dump({
                "name": session_name,
                "status": "Свободна",
                "api_id": client_data["api_id"] if client_data else "",
                "api_hash": client_data["api_hash"] if client_data else ""
            }, f, indent=4)
    
    await message.reply(f"✅ {file_name} добавлен в папку {target_folder}!")

async def process_archive_file(downloaded_file, file_ext, message):
    temp_file = f"temp_archive{file_ext}"
    with open(temp_file, 'wb') as f:
        f.write(downloaded_file.getvalue())
    
    try:
        session_files = []
        if file_ext == '.zip':
            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                session_files = [f for f in zip_ref.namelist() if f.endswith('.session')]
                zip_ref.extractall("temp_extracted")
        elif file_ext == '.rar':
            with rarfile.RarFile(temp_file, 'r') as rar_ref:
                session_files = [f for f in rar_ref.namelist() if f.endswith('.session')]
                rar_ref.extractall("temp_extracted")
        
        if not session_files:
            await message.reply("❌ В архиве не найдено .session файлов!")
            return
        if not clients:
            await message.reply("❌ Нет доступных клиентов!")
            return
        
        target_folder = random.choice(clients)["name"]
        success_count = 0
        report_message = f"📊 Все сессии будут добавлены в папку: {target_folder}\n\n"
        
        for session_file in session_files:
            file_name = os.path.basename(session_file)
            session_name = os.path.splitext(file_name)[0]
            src_path = os.path.join("temp_extracted", session_file)
            target_path = os.path.join("Session", target_folder, file_name)
            
            if os.path.exists(target_path):
                report_message += f"❌ {file_name} уже существует\n"
                continue
            
            os.rename(src_path, target_path)
            
            json_file = os.path.join("Session", target_folder, f"{session_name}.json")
            client_data = next((c for c in clients if c["name"] == target_folder), None)
            
            if not os.path.exists(json_file):
                with open(json_file, 'w') as f:
                    json.dump({
                        "name": session_name,
                        "status": "Свободна",
                        "api_id": client_data["api_id"] if client_data else "",
                        "api_hash": client_data["api_hash"] if client_data else ""
                    }, f, indent=4)
            
            report_message += f"✅ {file_name}\n"
            success_count += 1
        
        report_message += f"\nВсего файлов: {len(session_files)}\nУспешно добавлено: {success_count}"
        await message.reply(report_message)
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if os.path.exists("temp_extracted"):
            for root, dirs, files in os.walk("temp_extracted", topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir("temp_extracted")

@dp.callback_query_handler(text='delete_sessionOsn', state='*')
async def delete_session_osn(callback: types.CallbackQuery, state: FSMContext):
    main_folder = "Session"  
    if not os.path.exists(main_folder):
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption="<b>❌ Папка Session не найдена!</b>",
            parse_mode="HTML"
        )
        return
    
    folders = [f for f in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, f))]
    
    if not folders:
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption="<b>❌ В папке Session нет подпапок!</b>",
            parse_mode="HTML"
        )
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for folder in folders:
        folder_path = os.path.join(main_folder, folder)
        try:
            session_files = [f for f in os.listdir(folder_path) 
                          if os.path.isfile(os.path.join(folder_path, f)) and f.endswith('.session')]
            session_count = len(session_files)
            button_text = f"{folder} [{session_count}]"
        except Exception as e:
            print(f"Error counting sessions in {folder}: {e}")
            button_text = folder  
        
        keyboard.insert(types.InlineKeyboardButton(button_text, callback_data=f"del_folder:{folder}"))
    
    keyboard.row(types.InlineKeyboardButton("🔙 Назад", callback_data="sessionOsn_menu"))
    
    try:
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption="<b>📂 Выберите папку с сессиями:</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Error editing message: {e}")
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="<b>📂 Выберите папку с сессиями:</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    await DeleteSessionStates.SELECT_FOLDER.set()
    await callback.answer()

PAGE_SIZE = 8 

@dp.callback_query_handler(lambda c: c.data.startswith('del_folder:'), state=DeleteSessionStates.SELECT_FOLDER)
async def select_folder(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "cancel_delete":
        await state.finish()
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption="<b>❌ Действие отменено.</b>",
            parse_mode="HTML"
        )
        return
    
    folder_name = callback.data.split(":")[1]
    await state.update_data(selected_folder=folder_name, current_page=0)  
    
    main_folder = "Session"
    folder_path = os.path.join(main_folder, folder_name)
    session_files = [f for f in os.listdir(folder_path) if f.endswith('.session')]
    
    if not session_files:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("🔙 Назад", callback_data="delete_sessionOsn"))
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption=f"<b>❌ В папке {folder_name} нет .session файлов!</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await state.finish()
        return
    
    await show_sessions_page(callback, folder_name, session_files, 0, state)
    await DeleteSessionStates.SELECT_SESSION.set()
    await callback.answer()

async def show_sessions_page(callback: types.CallbackQuery, folder_name: str, session_files: list, page: int, state: FSMContext):
    total_pages = (len(session_files) + PAGE_SIZE - 1) // PAGE_SIZE
    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    current_sessions = session_files[start_idx:end_idx]
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    for session_file in current_sessions:
        keyboard.insert(types.InlineKeyboardButton(session_file, callback_data=f"del_session:{session_file}"))
    if total_pages > 1:
        nav_buttons = []
        
        if page == 0:
            if total_pages > 1:
                nav_buttons.append(types.InlineKeyboardButton("⏩️", callback_data="session_page:fast_forward"))
                nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data="session_page:next"))
        elif page == total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton("⏪️", callback_data="session_page:fast_back"))
            nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data="session_page:prev"))
        else:
            nav_buttons.append(types.InlineKeyboardButton("⏪️", callback_data="session_page:fast_back"))
            nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data="session_page:prev"))
            nav_buttons.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
            nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data="session_page:next"))
            nav_buttons.append(types.InlineKeyboardButton("⏩️", callback_data="session_page:fast_forward"))
        
        keyboard.row(*nav_buttons)
    keyboard.row(types.InlineKeyboardButton("🔙 Назад", callback_data="delete_sessionOsn"))
    
    await state.update_data(current_page=page, session_files=session_files)
    
    await bot.edit_message_caption(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        caption=f"<b>📄 Выберите сессию для удаления из папки {folder_name}</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.callback_query_handler(lambda c: c.data.startswith('session_page:'), state=DeleteSessionStates.SELECT_SESSION)
async def handle_session_pagination(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_files = data.get('session_files', [])
    current_page = data.get('current_page', 0)
    folder_name = data.get('selected_folder')
    total_pages = (len(session_files) + PAGE_SIZE - 1) // PAGE_SIZE
    
    action = callback.data.split(":")[1]
    
    if action == "next" and current_page < total_pages - 1:
        current_page += 1
    elif action == "prev" and current_page > 0:
        current_page -= 1
    elif action == "fast_forward":
        current_page = total_pages - 1
    elif action == "fast_back":
        current_page = 0
    
    await show_sessions_page(callback, folder_name, session_files, current_page, state)
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "delete_sessionOsn", state=[DeleteSessionStates.SELECT_SESSION, DeleteSessionStates.CONFIRM_DELETE])
async def back_to_folders(callback: types.CallbackQuery, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    main_folder = "Session"
    folders = [f for f in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, f))]
    
    for folder in folders:
        keyboard.insert(types.InlineKeyboardButton(folder, callback_data=f"del_folder:{folder}"))
    
    keyboard.row(types.InlineKeyboardButton("🔙 Назад", callback_data="cancel_delete"))
    
    await bot.edit_message_caption(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        caption="<b>📂 Выберите папку с сессией для удаления:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await DeleteSessionStates.SELECT_FOLDER.set()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "cancel_delete_session", state=DeleteSessionStates.CONFIRM_DELETE)
async def cancel_delete_session(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    folder_name = data.get('selected_folder')
    session_files = data.get('session_files', [])
    current_page = data.get('current_page', 0)
    
    await show_sessions_page(callback, folder_name, session_files, current_page, state)
    await DeleteSessionStates.SELECT_SESSION.set()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('del_session:'), state=DeleteSessionStates.SELECT_SESSION)
async def select_session(callback: types.CallbackQuery, state: FSMContext):
    session_file = callback.data.split(":")[1]
    await state.update_data(selected_session=session_file)
    
    data = await state.get_data()
    folder_name = data.get('selected_folder')
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("✅ Удалить", callback_data="confirm_delete"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_delete_session")
    )
    
    await bot.edit_message_caption(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        caption=(
            f"<b>❗ Вы уверены, что хотите удалить сессию?</b>\n\n"
            f"<b>📂 Папка:</b> <code>{folder_name}</code>\n"
            f"<b>📄 Файл:</b> <code>{session_file}</code>"
        ),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await DeleteSessionStates.CONFIRM_DELETE.set()
    await callback.answer()

@dp.callback_query_handler(text="confirm_delete", state=DeleteSessionStates.CONFIRM_DELETE)
@dp.callback_query_handler(text="cancel_delete_session", state=DeleteSessionStates.CONFIRM_DELETE)
async def confirm_delete(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "cancel_delete_session":
        data = await state.get_data()
        folder_name = data.get('selected_folder')
        await DeleteSessionStates.SELECT_SESSION.set()  
        
        main_folder = "Session"
        folder_path = os.path.join(main_folder, folder_name)
        session_files = [f for f in os.listdir(folder_path) if f.endswith('.session')]
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        for session_file in session_files:
            keyboard.insert(types.InlineKeyboardButton(session_file, callback_data=f"del_session:{session_file}"))
        
        keyboard.row(types.InlineKeyboardButton("🔙 Назад", callback_data="delete_sessionOsn"))
        
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption=f"<b>📄 Выберите сессию для удаления из папки {folder_name}:</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    folder_name = data.get('selected_folder')
    session_file = data.get('selected_session')
    
    main_folder = "Session"
    session_path = os.path.join(main_folder, folder_name, session_file)
    json_file = os.path.join(main_folder, folder_name, session_file.replace('.session', '.json'))
    
    try:
        if os.path.exists(session_path):
            os.remove(session_path)
        if os.path.exists(json_file):
            os.remove(json_file)
            
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("🔙 Назад", callback_data="delete_sessionOsn"))
        
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption=f"<b>✅ Сессия {session_file} и соответствующий json-файл успешно удалены!</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("🔙 Назад", callback_data="delete_sessionOsn"))
        
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption=f"<b>❌ Ошибка при удалении:</b> <code>{str(e)}</code>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    await state.finish()
    await callback.answer()

def register_delete_session_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(delete_session_osn, text="delete_sessionOsn")  
    dp.register_callback_query_handler(select_folder, state=DeleteSessionStates.SELECT_FOLDER)
    dp.register_callback_query_handler(select_session, state=DeleteSessionStates.SELECT_SESSION)
    dp.register_callback_query_handler(confirm_delete, state=DeleteSessionStates.CONFIRM_DELETE)   


@dp.callback_query_handler(text='create_non_menu', state='*')
async def create_non_menu_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    email_message = """
<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote>
<b>📤 Загрузить .session</b> - Загрузить существующий сессионный файл.
<b>📥 Добавить .sesion</b> - Создать новый сессионный файл.
<b>🗑 Удалить .sesion</b> - Функция удаления сессионный файлов.
<b>📋 Проверить .sesion</b> - Функция проверки sesion 
🔙 <b>Назад</b> - Вернуться в админ панель.
</blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>
"""
    markup = InlineKeyboardMarkup(row_width=2)
    btn_upload_session = InlineKeyboardButton('📤 Загрузить .session', callback_data='upload_non_main_session')
    btn_create_account = InlineKeyboardButton('📥 Добавить .sesion', callback_data='create_non_main_account')
    btn_delete_non_main_session = InlineKeyboardButton('🗑 Удалить .sesion', callback_data='delete_non_main_session')
    btn_list_non_main_session = InlineKeyboardButton('📋 Проверить .sesion', callback_data='list_non_main_session')
    btn_back = InlineKeyboardButton('🔙 Назад', callback_data='admin_panel')

    markup.add(btn_upload_session, btn_create_account)
    markup.add(btn_delete_non_main_session, btn_list_non_main_session)
    markup.add(btn_back)

    try:
        await callback_query.message.edit_caption(
            caption=email_message,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Error editing message: {e}")
        await callback_query.message.answer(
            text=email_message,
            reply_markup=markup,
            parse_mode="HTML"
        )

    await callback_query.answer()

@dp.callback_query_handler(text='upload_non_main_session', state='*')
async def upload_non_main_session_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "📤 Пожалуйста, отправьте мне файл .session или архив (.zip/.rar) с .session файлами для неосновных аккаунтов",
    )
    await state.set_state("waiting_for_non_main_session_file")

@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, state="waiting_for_non_main_session_file")
async def handle_non_main_session_file(message: types.Message, state: FSMContext):
    try:
        non_main_folder = "Не_основные"
        if not os.path.exists(non_main_folder):
            os.makedirs(non_main_folder)
        
        file_id = message.document.file_id
        file_name = message.document.file_name
        file_ext = os.path.splitext(file_name)[1].lower()
        
        file = await bot.get_file(file_id)
        downloaded_file = await bot.download_file(file.file_path)
        
        if file_ext == '.session':
            await process_non_main_single_session(downloaded_file, file_name, message)
        elif file_ext in ('.zip', '.rar'):
            await process_non_main_archive_file(downloaded_file, file_ext, message)
        else:
            await message.reply("❌ Неподдерживаемый формат файла. Пожалуйста, отправьте .session, .zip или .rar файл.")
            
    except Exception as e:
        await message.reply(f"❌ Произошла ошибка: {str(e)}")
    finally:
        await state.finish()

async def process_non_main_single_session(downloaded_file, file_name, message):
    non_main_folder = "Не_основные"
    target_path = os.path.join(non_main_folder, file_name)
    
    if os.path.exists(target_path):
        await message.reply(f"❌ Файл {file_name} уже существует в папке {non_main_folder}!")
        return
    
    with open(target_path, 'wb') as new_file:
        new_file.write(downloaded_file.getvalue())
    
    session_name = os.path.splitext(file_name)[0]
    json_file = os.path.join(non_main_folder, f"{session_name}.json")
    
    if not os.path.exists(json_file):
        with open(json_file, 'w') as f:
            json.dump({
                "name": session_name,
                "status": "Свободна",
                "api_id": 21826549,
                "api_hash": "c1a19f792cfd9e397200d16c7e448160"
            }, f, indent=4)
    
    await message.reply(f"✅ Файл {file_name} успешно добавлен в папку {non_main_folder}!")

async def process_non_main_archive_file(downloaded_file, file_ext, message):
    non_main_folder = "Не_основные"
    temp_file = f"temp_non_main_archive{file_ext}"
    session_files = []
    
    with open(temp_file, 'wb') as f:
        f.write(downloaded_file.getvalue())
    
    try:
        if file_ext == '.zip':
            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                session_files = [f for f in zip_ref.namelist() if f.endswith('.session')]
                zip_ref.extractall("temp_extracted_non_main")
        elif file_ext == '.rar':
            with rarfile.RarFile(temp_file, 'r') as rar_ref:
                session_files = [f for f in rar_ref.namelist() if f.endswith('.session')]
                rar_ref.extractall("temp_extracted_non_main")
        
        if not session_files:
            await message.reply("❌ В архиве не найдено .session файлов!")
            return
        
        success_count = 0
        report_message = "📊 Отчет о добавлении файлов:\n\n"
        
        for session_file in session_files:
            file_name = os.path.basename(session_file)
            session_name = os.path.splitext(file_name)[0]
            src_path = os.path.join("temp_extracted_non_main", session_file)
            target_path = os.path.join(non_main_folder, file_name)
            
            if os.path.exists(target_path):
                report_message += f"❌ Файл {file_name} уже существует\n"
                continue
            
            os.rename(src_path, target_path)
            
            json_file = os.path.join(non_main_folder, f"{session_name}.json")
            if not os.path.exists(json_file):
                with open(json_file, 'w') as f:
                    json.dump({
                        "name": session_name,
                        "status": "Свободна",
                        "api_id": 21826549,
                        "api_hash": "c1a19f792cfd9e397200d16c7e448160"
                    }, f, indent=4)
            
            report_message += f"✅ {file_name}\n"
            success_count += 1
        
        report_message += f"\nВсего файлов: {len(session_files)}\nУспешно добавлено: {success_count}"
        await message.reply(report_message)
        
    except Exception as e:
        await message.reply(f"❌ Ошибка при обработке архива: {str(e)}")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if os.path.exists("temp_extracted_non_main"):
            for root, dirs, files in os.walk("temp_extracted_non_main", topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir("temp_extracted_non_main")

@dp.callback_query_handler(text='delete_non_main_session', state='*')
async def delete_non_main_session_handler(callback: types.CallbackQuery, state: FSMContext):
    main_folder = "Не_основные"
    if not os.path.exists(main_folder):
        await callback.message.edit_caption(
            caption="<b>❌ Папка Не_основные не найдена!</b>",
            parse_mode="HTML"
        )
        return

    session_files = [f for f in os.listdir(main_folder) if os.path.isfile(os.path.join(main_folder, f)) and f.endswith('.session')]

    if not session_files:
        await callback.message.edit_caption(
            caption="<b>❌ В папке Не_основные нет .session файлов!</b>",
            parse_mode="HTML"
        )
        return

    await show_non_main_sessions_page(callback, session_files, 0, state)
    await DeleteNonMainSessionStates.SELECT_SESSION.set()
    await callback.answer()

PAGE_SIZE = 8

async def show_non_main_sessions_page(callback: types.CallbackQuery, session_files: list, page: int, state: FSMContext):
    total_pages = (len(session_files) + PAGE_SIZE - 1) // PAGE_SIZE
    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    current_sessions = session_files[start_idx:end_idx]

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    for session_file in current_sessions:
        keyboard.insert(types.InlineKeyboardButton(session_file, callback_data=f"del_non_main_session_file:{session_file}"))
    if total_pages > 1:
        nav_buttons = []

        if page == 0:
            if total_pages > 1:
                nav_buttons.append(types.InlineKeyboardButton("⏩️", callback_data="non_main_session_page:fast_forward"))
                nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data="non_main_session_page:next"))
        elif page == total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton("⏪️", callback_data="non_main_session_page:fast_back"))
            nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data="non_main_session_page:prev"))
        else:
            nav_buttons.append(types.InlineKeyboardButton("⏪️", callback_data="non_main_session_page:fast_back"))
            nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data="non_main_session_page:prev"))
            nav_buttons.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
            nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data="non_main_session_page:next"))
            nav_buttons.append(types.InlineKeyboardButton("⏩️", callback_data="non_main_session_page:fast_forward"))

        keyboard.row(*nav_buttons)
    keyboard.row(types.InlineKeyboardButton("🔙 Назад", callback_data="create_non_menu"))

    await state.update_data(current_page=page, session_files=session_files)

    await callback.message.edit_caption(
        caption=f"<b>📄 Выберите сессию для удаления из папки Не_основные</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.callback_query_handler(lambda c: c.data.startswith('non_main_session_page:'), state=DeleteNonMainSessionStates.SELECT_SESSION)
async def handle_non_main_session_pagination(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_files = data.get('session_files', [])
    current_page = data.get('current_page', 0)
    total_pages = (len(session_files) + PAGE_SIZE - 1) // PAGE_SIZE

    action = callback.data.split(":")[1]

    if action == "next" and current_page < total_pages - 1:
        current_page += 1
    elif action == "prev" and current_page > 0:
        current_page -= 1
    elif action == "fast_forward":
        current_page = total_pages - 1
    elif action == "fast_back":
        current_page = 0

    await show_non_main_sessions_page(callback, session_files, current_page, state)
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data == "create_non_menu", state=[DeleteNonMainSessionStates.SELECT_SESSION, DeleteNonMainSessionStates.CONFIRM_DELETE])
async def back_to_non_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await create_non_menu_callback(callback, state)


@dp.callback_query_handler(lambda c: c.data.startswith('del_non_main_session_file:'), state=DeleteNonMainSessionStates.SELECT_SESSION)
async def select_non_main_session(callback: types.CallbackQuery, state: FSMContext):
    session_file = callback.data.split(":")[1]
    await state.update_data(selected_session=session_file)

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("✅ Удалить", callback_data="confirm_delete_non_main"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_delete_non_main_session")
    )

    await callback.message.edit_caption(
        caption=(
            f"<b>❗ Вы уверены, что хотите удалить сессию?</b>\n\n"
            f"<b>📂 Папка:</b> <code>Не_основные</code>\n"
            f"<b>📄 Файл:</b> <code>{session_file}</code>"
        ),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await DeleteNonMainSessionStates.CONFIRM_DELETE.set()
    await callback.answer()

@dp.callback_query_handler(text="cancel_delete_non_main_session", state=DeleteNonMainSessionStates.CONFIRM_DELETE)
async def cancel_delete_non_main_session(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_files = data.get('session_files', [])
    current_page = data.get('current_page', 0)

    await show_non_main_sessions_page(callback, session_files, current_page, state)
    await DeleteNonMainSessionStates.SELECT_SESSION.set()
    await callback.answer()


@dp.callback_query_handler(text="confirm_delete_non_main", state=DeleteNonMainSessionStates.CONFIRM_DELETE)
async def confirm_delete_non_main(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_file = data.get('selected_session')

    main_folder = "Не_основные"
    session_path = os.path.join(main_folder, session_file)
    json_file = os.path.join(main_folder, session_file.replace('.session', '.json'))

    try:
        if os.path.exists(session_path):
            os.remove(session_path)
        if os.path.exists(json_file):
            os.remove(json_file)

        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("🔙 Назад", callback_data="delete_non_main_session"))

        await callback.message.edit_caption(
            caption=f"<b>✅ Сессия {session_file} и соответствующий json-файл успешно удалены!</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("🔙 Назад", callback_data="delete_non_main_session"))

        await callback.message.edit_caption(
            caption=f"<b>❌ Ошибка при удалении:</b> <code>{str(e)}</code>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    await state.finish()
    await callback.answer()

async def check_session_with_clients_bot(session_file: str, message: types.Message, state: FSMContext) -> dict:
    session_name = os.path.basename(session_file).replace('.session', '')
    result = {
        "session_name": session_name,
        "status": "Не авторизована",
        "info": [],
        "is_working": False,
        "is_premium": False,
        "is_bot": False,
        "deleted": False
    }

    current_results = await state.get_data()
    total_checked = current_results.get('total_checked', 0)
    working_sessions = current_results.get('working_sessions', 0)
    premium_sessions = current_results.get('premium_sessions', 0)
    
    await state.update_data(total_checked=total_checked + 1)

    def delete_related_files():
        try:
            if os.path.exists(session_file):
                os.remove(session_file)
            json_file = session_file.replace('.session', '.json')
            if os.path.exists(json_file):
                os.remove(json_file)
        except Exception as e:
            print(f"Error deleting files for {session_name}: {e}")

    for client_info in clients:
        client = None
        try:
            client = TelegramClient(SQLiteSession(session_file),
                                client_info["api_id"],
                                client_info["api_hash"],
                                timeout=15)
            await client.connect()

            if not await client.is_user_authorized():
                continue

            me = await client.get_me()
            if not isinstance(me, User):
                continue

            auth_info = f"Авторизован как: {me.first_name} (ID: {me.id})"
            account_type = "Бот" if me.bot else "Пользователь"
            result["is_bot"] = me.bot

            premium_status = "Premium: Нет"
            try:
                full_user = await client(GetFullUserRequest(me))
                if hasattr(full_user, 'premium') and full_user.premium:
                    premium_status = "Premium: Да"
                    result["is_premium"] = True
                elif hasattr(me, 'premium') and me.premium:
                    premium_status = "Premium: Да"
                    result["is_premium"] = True
            except Exception as e:
                try:
                    if hasattr(me, 'premium') and me.premium:
                        premium_status = "Premium: Да"
                        result["is_premium"] = True
                except:
                    premium_status = "Premium: Не удалось проверить"

            username = f"username: @{me.username}" if me.username else "Нет username"
            client_name = f"Клиент: {client_info['name']}"

            session_info_lines = [
                f"<b>Сессия:</b> <code>{session_name}</code>",
                auth_info,
                username,
                premium_status,
                f"Тип аккаунта: {account_type}",
                client_name
            ]
            result["info"] = session_info_lines

            if me.bot:
                result["status"] = "Это бот"
                result["info"].append("Действие: Удаление (это бот)")
                delete_related_files()
                result["deleted"] = True
                return result
            else:
                result["status"] = "Работает"
                result["is_working"] = True
                await state.update_data(working_sessions=working_sessions + 1)
                if result["is_premium"]:
                    await state.update_data(premium_sessions=premium_sessions + 1)
                return result

        except AuthKeyDuplicatedError:
            result["status"] = "Ошибка: Сессия используется под разными IP"
            result["info"].append(f"Клиент: {client_info['name']}")
            result["info"].append("Действие: Удаление")
            delete_related_files()
            result["deleted"] = True
            return result
        except SessionPasswordNeededError:
            result["status"] = "Требуется 2FA"
            result["info"].append(f"Клиент: {client_info['name']}")
            return result
        except (asyncio.TimeoutError, ConnectionError):
            continue
        except Exception as e:
            continue
        finally:
            if client:
                try:
                    await client.disconnect()
                except:
                    pass

    result["info"] = [f"<b>Сессия:</b> <code>{session_name}</code>", "Не удалось авторизоваться ни с одним клиентом"]
    return result

@dp.callback_query_handler(text='list_sessionOsn', state='*')
async def list_session_osn_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()  
    await state.finish()
    await CheckSessionStates.CHECKING.set()

    try:
        initial_message = await callback_query.message.answer(
            text="<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote>\n"
                 "<b>🚀 Начинаю проверку сессий...</b>\n"
                 "</blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>",
            parse_mode="HTML"
        )

        session_dir = "Session"
        session_files = await find_session_files_in_dir(session_dir)
        total_sessions_found = len(session_files)

        await state.update_data(
            initial_message_id=initial_message.message_id,
            total_sessions_found=total_sessions_found,
            total_checked=0,
            working_sessions=0,
            premium_sessions=0
        )

        if not session_files:
            await safe_edit_message(
                initial_message,
                text="<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote>\n"
                     "<b>❌ В папке Session не найдено ни одной сессии.</b>\n"
                     "</blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>",
                parse_mode="HTML"
            )
            return

        for session_file in session_files:
            result = await check_session_with_clients_bot(session_file, initial_message, state)
            current_data = await state.get_data()

            status_icon = get_status_icon(result)
            premium_icon = "💎" if result["is_premium"] else ""

            status_text = f"{status_icon} {premium_icon} <b>{result['session_name']}</b>: {result['status']}"
            if result['info']:
                status_text += "\n" + "\n".join(result['info'][1:])

            await safe_edit_message(
                initial_message,
                text=(
                    f"<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote>\n"
                    f"<b>🚀 Проверяю сессии... ({current_data['total_checked']}/{total_sessions_found})</b>\n\n"
                    f"{status_text}\n"
                    f"</blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>"
                ),
                parse_mode="HTML"
            )
            await asyncio.sleep(0.5)

        final_data = await state.get_data()
        await show_final_results(initial_message, final_data, "основных")

    except Exception as e:
        logger.error(f"Ошибка в list_session_osn_callback: {e}")
    finally:
        await state.finish()

@dp.callback_query_handler(text='list_non_main_session', state='*')
async def list_non_main_session_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer() 
    await state.finish()
    await CheckSessionStates.CHECKING.set()

    try:
        initial_message = await callback_query.message.answer(
            text="<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote>\n"
                 "<b>🚀 Начинаю проверку Не_основных сессий...</b>\n"
                 "</blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>",
            parse_mode="HTML"
        )

        session_dir = "Не_основные"
        session_files = await find_session_files_in_dir(session_dir)
        total_sessions_found = len(session_files)

        await state.update_data(
            initial_message_id=initial_message.message_id,
            total_sessions_found=total_sessions_found,
            total_checked=0,
            working_sessions=0,
            premium_sessions=0
        )

        if not session_files:
            await safe_edit_message(
                initial_message,
                text="<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote>\n"
                     "<b>❌ В папке Не_основные не найдено ни одной сессии.</b>\n"
                     "</blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>",
                parse_mode="HTML"
            )
            return

        for session_file in session_files:
            result = await check_session_with_clients_bot(session_file, initial_message, state)
            current_data = await state.get_data()

            status_icon = get_status_icon(result)
            premium_icon = "💎" if result["is_premium"] else ""

            status_text = f"{status_icon} {premium_icon} <b>{result['session_name']}</b>: {result['status']}"
            if result['info']:
                status_text += "\n" + "\n".join(result['info'][1:])

            await safe_edit_message(
                initial_message,
                text=(
                    f"<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote>\n"
                    f"<b>🚀 Проверяю Не_основные сессии... ({current_data['total_checked']}/{total_sessions_found})</b>\n\n"
                    f"{status_text}\n"
                    f"</blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>"
                ),
                parse_mode="HTML"
            )
            await asyncio.sleep(0.5)

        final_data = await state.get_data()
        await show_final_results(initial_message, final_data, "Не_основных")

    except Exception as e:
        logger.error(f"Ошибка в list_non_main_session_callback: {e}")
    finally:
        await state.finish()

async def safe_edit_message(message: types.Message, text: str, **kwargs):
    try:
        await message.edit_text(text=text, **kwargs)
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
        try:
            await message.answer(f"⚠ Ошибка при обновлении сообщения: {str(e)[:100]}")
        except:
            pass

def get_status_icon(result: dict) -> str:
    if result["is_bot"]:
        return "🤖"
    elif result["deleted"]:
        return "🗑️"
    elif result["status"] == "Требуется 2FA":
        return "🔒"
    return "🟢" if result["is_working"] else "🔴"

async def show_final_results(message: types.Message, data: dict, session_type: str):
    final_message_text = (
        f"<b>───── ⋆⋅☆⋅⋆ ─────</b><blockquote>\n"
        f"<b>✅ Проверка {session_type} сессий завершена!</b>\n\n"
        f"<b>📊 Итого:</b>\n"
        f"  Всего проверено: <code>{data.get('total_checked', 0)}</code>\n"
        f"  Рабочих сессий: <code>{data.get('working_sessions', 0)}</code>\n"
        f"  С Premium: <code>{data.get('premium_sessions', 0)}</code>\n"
        f"  Не авторизованных/Удаленных: <code>{data.get('total_checked', 0) - data.get('working_sessions', 0)}</code>\n"
        f"</blockquote><b>───── ⋆⋅☆⋅⋆ ─────</b>"
    )
    await safe_edit_message(message, final_message_text, parse_mode="HTML")

def register_check_session_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(list_session_osn_callback, text="list_sessionOsn", state="*")
    dp.register_callback_query_handler(list_non_main_session_callback, text="list_non_main_session", state="*")


def register_non_main_delete_session_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(delete_non_main_session_handler, text="delete_non_main_session")
    dp.register_callback_query_handler(select_non_main_session, state=DeleteNonMainSessionStates.SELECT_SESSION)
    dp.register_callback_query_handler(confirm_delete_non_main, text="confirm_delete_non_main", state=DeleteNonMainSessionStates.CONFIRM_DELETE)
    dp.register_callback_query_handler(cancel_delete_non_main_session, text="cancel_delete_non_main_session", state=DeleteNonMainSessionStates.CONFIRM_DELETE)
