import re
import requests
import io
from aiogram import types
from aiogram.dispatcher import FSMContext
from config import dp
from бот import VK_TOKEN, MAX_CAPTION_LENGTH
from datetime import datetime

async def get_vk_user_info_raw(vk_user_id, VK_TOKEN):
    VK_API_URL = "https://api.vk.com/method/users.get"
    params = {
        "access_token": VK_TOKEN,
        "v": "5.131",
        "user_ids": vk_user_id,
        "fields": "first_name,last_name,status,sex,bdate,city,country,photo_max_orig,last_seen,domain,education,universities,schools,relatives,relation,career,military,home_town,connections,exports,wall_comments,activities,interests,music,movies,tv,books,games,about,quotes,personal,political,langs,people_main,life_main,smoking,alcohol,inspired_by,verified,timezone,mobile_phone,home_phone,site,can_post,can_see_all_posts,can_see_audio,can_write_private_message,can_send_friend_request,is_friend,friend_status,exports,counters"
    }
    try:
        response = requests.get(VK_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        return []
    except ValueError:
        return []
    if "response" not in data or not data["response"]:
        return []
    user = data["response"][0]
    if "deactivated" in user:
        return []
    return [user]

async def get_vk_user_info(vk_user_id, VK_TOKEN):
    VK_API_URL = "https://api.vk.com/method/users.get"
    params = {
        "access_token": VK_TOKEN,
        "v": "5.131",
        "user_ids": vk_user_id,
        "fields": "first_name,last_name,status,sex,bdate,city,country,photo_max_orig,last_seen,domain,education,universities,schools,relatives,relation,career,military,home_town,connections,exports,wall_comments,activities,interests,music,movies,tv,books,games,about,quotes,personal,political,langs,people_main,life_main,smoking,alcohol,inspired_by,verified,timezone,mobile_phone,home_phone,site,can_post,can_see_all_posts,can_see_audio,can_write_private_message,can_send_friend_request,is_friend,friend_status,exports,counters"
    }
    try:
        response = requests.get(VK_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        return []
    except ValueError:
        return []
    if "response" not in data or not data["response"]:
        return []
    user = data["response"][0]
    if "deactivated" in user:
        return []
    return format_results([user])

def clean_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def format_results(users, html_format=True):
    formatted = []
    for user in users:
        full_text_parts = []
        if html_format:
            full_text_parts.append("<b>───── ⋆⋅☆⋅⋆ ─────</b>\n\n") # Removed <blockquote>
            full_text_parts.append("<b>👤 ВКонтакте:</b>\n")
            line_prefix = "├ <b>"
            line_suffix = "</b>: "
            sub_line_prefix = "  "
            end_block_html = "<b>───── ⋆⋅☆⋅⋆ ─────</b>" # Removed </blockquote>
        else:
            full_text_parts.append("───── ⋆⋅☆⋅⋆ ─────\n\n")
            full_text_parts.append("👤 ВКонтакте:\n")
            line_prefix = "├ "
            line_suffix = ": "
            sub_line_prefix = "  "
            end_block_html = "\n───── ⋆⋅☆⋅⋆ ─────"

        full_text_parts.append(f"{line_prefix}Имя{line_suffix}{user.get('first_name', 'Неизвестно')}\n")
        full_text_parts.append(f"{line_prefix}Фамилия{line_suffix}{user.get('last_name', 'Неизвестно')}\n")
        full_text_parts.append(f"{line_prefix}ID{line_suffix}{user.get('id', 'Неизвестно')}\n")

        if user.get('screen_name'):
            full_text_parts.append(f"{line_prefix}Короткое имя страницы{line_suffix}{user['screen_name']}\n")
        if user.get('domain'):
            full_text_parts.append(f"{line_prefix}Ссылка{line_suffix}vk.com/{user['domain']}\n")
        if user.get('verified') is not None:
            full_text_parts.append(f"{line_prefix}Верифицирован{line_suffix}{'Да' if user['verified'] else 'Нет'}\n")
        if user.get('last_seen'):
            last_seen = datetime.fromtimestamp(user['last_seen']['time']).strftime('%Y-%m-%d %H:%M:%S')
            full_text_parts.append(f"{line_prefix}Был онлайн{line_suffix}{last_seen}\n")
        if user.get('timezone') is not None:
            full_text_parts.append(f"{line_prefix}Часовой пояс{line_suffix}UTC{user['timezone']:+}\n")
        if user.get('city') and user['city'].get('title'):
            full_text_parts.append(f"{line_prefix}Город{line_suffix}{user['city']['title']}\n")
        if user.get('country') and user['country'].get('title'):
            full_text_parts.append(f"{line_prefix}Страна{line_suffix}{user['country']['title']}\n")
        if user.get('status'):
            full_text_parts.append(f"{line_prefix}Статус{line_suffix}{user['status']}\n")

        sex_map = {1: "Ж", 2: "М"}
        if user.get('sex') in sex_map:
            full_text_parts.append(f"{line_prefix}Пол{line_suffix}{sex_map[user['sex']]}\n")

        if user.get('bdate'):
            full_text_parts.append(f"{line_prefix}Дата рождения{line_suffix}{user['bdate']}\n")
        if user.get('mobile_phone'):
            full_text_parts.append(f"{line_prefix}Мобильный телефон{line_suffix}{user['mobile_phone']}\n")
        if user.get('home_phone'):
            full_text_parts.append(f"{line_prefix}Домашний телефон{line_suffix}{user['home_phone']}\n")
        if user.get('site'):
            full_text_parts.append(f"{line_prefix}Сайт{line_suffix}{user['site']}\n")
        if user.get('about'):
            full_text_parts.append(f"{line_prefix}О себе{line_suffix}{user['about']}\n")
        if user.get('activities'):
            full_text_parts.append(f"{line_prefix}Деятельность{line_suffix}{user['activities']}\n")
        if user.get('interests'):
            full_text_parts.append(f"{line_prefix}Интересы{line_suffix}{user['interests']}\n")
        if user.get('books'):
            full_text_parts.append(f"{line_prefix}Любимые книги{line_suffix}{user['books']}\n")
        if user.get('games'):
            full_text_parts.append(f"{line_prefix}Любимые игры{line_suffix}{user['games']}\n")
        user_music = user.get('music')
        if user_music:
            if isinstance(user_music, str):
                full_text_parts.append(f"{line_prefix}Любимая музыка{line_suffix}{user_music}\n")
        if user.get('tv'):
            full_text_parts.append(f"{line_prefix}Любимые телешоу{line_suffix}{user['tv']}\n")
        if user.get('movies'):
            full_text_parts.append(f"{line_prefix}Любимые фильмы{line_suffix}{user['movies']}\n")
        if user.get('quotes'):
            full_text_parts.append(f"{line_prefix}Любимые цитаты{line_suffix}{user['quotes']}\n")

        relation_map = {
            1: "Не женат/не замужем", 2: "Есть друг/есть подруга", 3: "Помолвлен/помолвлена",
            4: "Женат/замужем", 5: "Всё сложно", 6: "В активном поиске",
            7: "Влюблён/влюблена", 8: "В гражданском браке"
        }
        if user.get('relation') is not None:
            full_text_parts.append(f"{line_prefix}Семейное положение{line_suffix}{relation_map.get(user['relation'], 'Неизвестно')}\n")

        personal = user.get("personal", {})
        political_map = {
            1: "Коммунистические", 2: "Социалистические", 3: "Умеренные",
            4: "Либеральные", 5: "Консервативные", 6: "Монархические",
            7: "Ультраконсервативные", 8: "Индифферентные", 9: "Либертарианские"
        }
        if personal.get('political') is not None:
            full_text_parts.append(f"{line_prefix}Политические предпочтения{line_suffix}{political_map.get(personal['political'], 'Неизвестно')}\n")
        if personal.get('religion'):
            full_text_parts.append(f"{line_prefix}Религия{line_suffix}{personal['religion']}\n")
        if personal.get('inspired_by'):
            full_text_parts.append(f"{line_prefix}Вдохновляется{line_suffix}{personal['inspired_by']}\n")

        people_main_map = {
            1: "Ум и креативность", 2: "Доброта и честность", 3: "Красота и здоровье",
            4: "Власть и богатство", 5: "Смелость и упорство", 6: "Юмор и жизнелюбие"
        }
        if personal.get('people_main') is not None:
            full_text_parts.append(f"{line_prefix}Главное в людях{line_suffix}{people_main_map.get(personal['people_main'], 'Неизвестно')}\n")

        life_main_map = {
            1: "Семья и дети", 2: "Карьера и деньги", 3: "Развлечения и отдых",
            4: "Наука и исследования", 5: "Совершенствование мира", 6: "Саморазвитие",
            7: "Красота и искусство", 8: "Слава и влияние"
        }
        if personal.get('life_main') is not None:
            full_text_parts.append(f"{line_prefix}Главное в жизни{line_suffix}{life_main_map.get(personal['life_main'], 'Неизвестно')}\n")

        smoking_map = {
            1: "Резко негативное", 2: "Негативное", 3: "Компромиссное",
            4: "Нейтральное", 5: "Положительное"
        }
        if personal.get('smoking') is not None:
            full_text_parts.append(f"{line_prefix}Отношение к курению{line_suffix}{smoking_map.get(personal['smoking'], 'Неизвестно')}\n")

        alcohol_map = {
            1: "Резко негативное", 2: "Негативное", 3: "Компромиссное",
            4: "Нейтральное", 5: "Положительное"
        }
        if personal.get('alcohol') is not None:
            full_text_parts.append(f"{line_prefix}Отношение к алкоголю{line_suffix}{alcohol_map.get(personal['alcohol'], 'Неизвестно')}\n")
        if personal.get('langs'):
            full_text_parts.append(f"{line_prefix}Языки{line_suffix}{', '.join(personal['langs'])}\n")

        counters = user.get("counters", {})
        if counters.get("followers") is not None and counters.get("followers") != 0:
            full_text_parts.append(f"{line_prefix}Количество подписчиков{line_suffix}{counters['followers']}\n")
        if counters.get("friends") is not None and counters.get("friends") != 0:
            full_text_parts.append(f"{line_prefix}Количество друзей{line_suffix}{counters['friends']}\n")
        if counters.get("photos") is not None and counters.get("photos") != 0:
            full_text_parts.append(f"{line_prefix}Количество фотографий{line_suffix}{counters['photos']}\n")
        if counters.get("videos") is not None and counters.get("videos") != 0:
            full_text_parts.append(f"{line_prefix}Количество видео{line_suffix}{counters['videos']}\n")
        if counters.get("audios") is not None and counters.get("audios") != 0:
            full_text_parts.append(f"{line_prefix}Количество аудиозаписей{line_suffix}{counters['audios']}\n")
        if counters.get("notes") is not None and counters.get("notes") != 0:
            full_text_parts.append(f"{line_prefix}Количество заметок{line_suffix}{counters['notes']}\n")
        if counters.get("gifts") is not None and counters.get("gifts") != 0:
            full_text_parts.append(f"{line_prefix}Количество подарков{line_suffix}{counters['gifts']}\n")
        if counters.get("articles") is not None and counters.get("articles") != 0:
            full_text_parts.append(f"{line_prefix}Количество статей{line_suffix}{counters['articles']}\n")
        if counters.get("clips") is not None and counters.get("clips") != 0:
            full_text_parts.append(f"{line_prefix}Количество клипов{line_suffix}{counters['clips']}\n")
        if counters.get("podcasts") is not None and counters.get("podcasts") != 0:
            full_text_parts.append(f"{line_prefix}Количество подкастов{line_suffix}{counters['podcasts']}\n")
        if counters.get("groups") is not None and counters.get("groups") != 0:
            full_text_parts.append(f"{line_prefix}Группы{line_suffix}{counters['groups']}\n")
        if counters.get("albums") is not None and counters.get("albums") != 0:
            full_text_parts.append(f"{line_prefix}Альбомы{line_suffix}{counters['albums']}\n")
        if counters.get("docs") is not None and counters.get("docs") != 0:
            full_text_parts.append(f"{line_prefix}Документы{line_suffix}{counters['docs']}\n")
        if counters.get("online_friends") is not None and counters.get("online_friends") != 0:
            full_text_parts.append(f"{line_prefix}Друзья онлайн{line_suffix}{counters['online_friends']}\n")
        if counters.get("mutual_friends") is not None and counters.get("mutual_friends") != 0:
            full_text_parts.append(f"{line_prefix}Общие друзья{line_suffix}{counters['mutual_friends']}\n")

        if user.get('can_post') is not None:
            full_text_parts.append(f"{line_prefix}Может публиковать на стене{line_suffix}{'Да' if user['can_post'] == 1 else 'Нет'}\n")
        if user.get('can_see_all_posts') is not None:
            full_text_parts.append(f"{line_prefix}Может видеть все записи на стене{line_suffix}{'Да' if user['can_see_all_posts'] == 1 else 'Нет'}\n")
        if user.get('can_see_audio') is not None:
            full_text_parts.append(f"{line_prefix}Может видеть аудиозаписи{line_suffix}{'Да' if user['can_see_audio'] == 1 else 'Нет'}\n")
        if user.get('can_write_private_message') is not None:
            full_text_parts.append(f"{line_prefix}Может писать личные сообщения{line_suffix}{'Да' if user['can_write_private_message'] == 1 else 'Нет'}\n")
        if user.get('can_send_friend_request') is not None:
            full_text_parts.append(f"{line_prefix}Может отправлять запросы в друзья{line_suffix}{'Да' if user['can_send_friend_request'] == 1 else 'Нет'}\n")
        if user.get('is_friend') is not None:
            full_text_parts.append(f"{line_prefix}В друзьях{line_suffix}{'Да' if user['is_friend'] == 1 else 'Нет'}\n")

        friend_status_map = {
            0: "Не друг", 1: "Исходящая заявка", 2: "Входящая заявка", 3: "Друзья"
        }
        if user.get('friend_status') is not None:
            full_text_parts.append(f"{line_prefix}Статус дружбы{line_suffix}{friend_status_map.get(user['friend_status'], 'Неизвестно')}\n")
        if user.get('wall_comments') is not None:
            full_text_parts.append(f"{line_prefix}Может комментировать стену{line_suffix}{'Да' if user['wall_comments'] == 1 else 'Нет'}\n")

        if user.get("career"):
            full_text_parts.append(f"{line_prefix}Карьера:{line_suffix}\n")
            for i, job in enumerate(user["career"]):
                prefix = "├" if i < len(user["career"]) - 1 else "└"
                if not html_format:
                    prefix = prefix.replace('├', '|').replace('└', '`')

                company_info = []
                if job.get("company"):
                    company_info.append(f"Компания: {job['company']}")
                if job.get("position"):
                    company_info.append(f"Должность: {job['position']}")
                if job.get("from"):
                    company_info.append(f"Год начала: {job['from']}")
                if job.get("until"):
                    company_info.append(f"Год окончания: {job['until']}")

                if company_info:
                    full_text_parts.append(f"{sub_line_prefix}{prefix} {', '.join(company_info)}\n")

        if user.get("military"):
            full_text_parts.append(f"{line_prefix}Военная служба:{line_suffix}\n")
            for i, service in enumerate(user["military"]):
                prefix = "├" if i < len(user["military"]) - 1 else "└"
                if not html_format:
                    prefix = prefix.replace('├', '|').replace('└', '`')
                military_info = []
                if service.get("unit"):
                    military_info.append(f"Отряд: {service['unit']}")
                if service.get("unit_id"):
                    military_info.append(f"ID отряда: {service['unit_id']}")
                if service.get("from"):
                    military_info.append(f"Год начала: {service['from']}")
                if service.get("until"):
                    military_info.append(f"Год окончания: {service['until']}")

                if military_info:
                    full_text_parts.append(f"{sub_line_prefix}{prefix} {', '.join(military_info)}\n")

        if user.get("education"):
            full_text_parts.append(f"{line_prefix}Образование:{line_suffix}\n")
            education_info = []
            if user["education"].get("university_name"):
                education_info.append(f"Университет: {user['education']['university_name']}")
            if user["education"].get("faculty_name"):
                education_info.append(f"Факультет: {user['education']['faculty_name']}")
            if user["education"].get("graduation"):
                education_info.append(f"Год окончания: {user['education']['graduation']}")

            if education_info:
                full_text_parts.append(f"{sub_line_prefix}└ {', '.join(education_info)}\n")


        if user.get("schools"):
            full_text_parts.append(f"{line_prefix}Школы:{line_suffix}\n")
            for i, school in enumerate(user["schools"]):
                prefix = "├" if i < len(user["schools"]) - 1 else "└"
                if not html_format:
                    prefix = prefix.replace('├', '|').replace('└', '`')
                school_info = []
                if school.get("name"):
                    school_info.append(f"Название: {school['name']}")
                if school.get("year_from"):
                    school_info.append(f"Год начала: {school['year_from']}")
                if school.get("year_to"):
                    school_info.append(f"Год окончания: {school['year_to']}")
                if school.get("type_str"):
                    school_info.append(f"Тип: {school['type_str']}")

                if school_info:
                    full_text_parts.append(f"{sub_line_prefix}{prefix} {', '.join(school_info)}\n")

        if user.get("universities"):
            full_text_parts.append(f"{line_prefix}Вузы:{line_suffix}\n")
            for i, university in enumerate(user["universities"]):
                prefix = "├" if i < len(user["universities"]) - 1 else "└"
                if not html_format:
                    prefix = prefix.replace('├', '|').replace('└', '`')
                university_info = []
                if university.get("name"):
                    university_info.append(f"Название: {university['name']}")
                if university.get("faculty_name"):
                    university_info.append(f"Факультет: {university['faculty_name']}")
                if university.get("chair_name"):
                    university_info.append(f"Кафедра: {university['chair_name']}")
                if university.get("graduation"):
                    university_info.append(f"Год окончания: {university['graduation']}")
                if university.get("education_form"):
                    university_info.append(f"Форма обучения: {university['education_form']}")
                if university.get("education_status"):
                    university_info.append(f"Статус: {university['education_status']}")

                if university_info:
                    full_text_parts.append(f"{sub_line_prefix}{prefix} {', '.join(university_info)}\n")

        if user.get("relatives"):
            full_text_parts.append(f"{line_prefix}Родственники:{line_suffix}\n")
            for i, relative in enumerate(user["relatives"]):
                prefix = "├" if i < len(user["relatives"]) - 1 else "└"
                if not html_format:
                    prefix = prefix.replace('├', '|').replace('└', '`')
                relation_type = relative.get('type')
                if relation_type == 'child':
                    relation_type = 'Ребёнок'
                elif relation_type == 'sibling':
                    relation_type = 'Брат/Сестра'
                elif relation_type == 'parent':
                    relation_type = 'Родитель'
                elif relation_type == 'grandparent':
                    relation_type = 'Бабушка/Дедушка'
                elif relation_type == 'grandchild':
                    relation_type = 'Внук/Внучка'
                elif relation_type == 'partner':
                    relation_type = 'Партнёр'
                else:
                    relation_type = relative.get('type', 'Неизвестно')


                name = relative.get('name', 'Неизвестно')
                full_text_parts.append(f"{sub_line_prefix}{prefix} {relation_type}: {name} (ID: {relative.get('id', 'Неизвестно')})\n")

        if user.get("connections"):
            full_text_parts.append(f"{line_prefix}Подключения к другим сервисам:{line_suffix}\n")
            for service, username in user["connections"].items():
                full_text_parts.append(f"{sub_line_prefix}├ {service.capitalize()}: {username}\n")

        if user.get("exports"):
            full_text_parts.append(f"{line_prefix}Экспорт в другие сервисы:{line_suffix}\n")
            for service, export_info in user["exports"].items():
                if isinstance(export_info, dict) and export_info.get('wall_post') is not None:
                    full_text_parts.append(f"{sub_line_prefix}├ {service.capitalize()}: Публикация на стене {'включена' if export_info['wall_post'] == 1 else 'отключена'}\n")
        last_line_index = -1
        for i in reversed(range(len(full_text_parts))):
            if full_text_parts[i].strip().startswith('├') and ": " in full_text_parts[i]:
                last_line_index = i
                break

        if last_line_index != -1:
            if html_format:
                full_text_parts[last_line_index] = full_text_parts[last_line_index].replace('├', '└', 1)
            else:
                full_text_parts[last_line_index] = full_text_parts[last_line_index].replace('├', '`', 1)

        full_text = "".join(full_text_parts)

        if user.get('photo_max_orig'):
            formatted.append({
                'text': full_text,
                'photo': user['photo_max_orig'],
                'user_id': user.get('id', 'unknown')
            })
        else:
            formatted.append({
                'text': full_text,
                'user_id': user.get('id', 'unknown')
            })
    return formatted[0] if formatted else None

async def search_vk(query, VK_TOKEN):
    try:
        id_match = re.match(r'^(?:id)?(\d+)$', query, re.IGNORECASE)
        if id_match:
            user_id = id_match.group(1)
            return await get_vk_user_info(user_id, VK_TOKEN)

        if 'vk.com/' in query.lower():
            screen_name = query.split('/')[-1].split('?')[0]
            if screen_name:
                return await get_vk_user_info(screen_name, VK_TOKEN)

        name_parts = [part for part in query.split() if part]
        if name_parts:
            search_params = {
                'count': 1,
                'fields': 'first_name,last_name,photo_max_orig,domain,last_seen,status,sex,bdate,city,country,counters,education,universities,schools,relatives,relation,career,military,home_town,connections,exports,wall_comments,activities,interests,music,movies,tv,books,games,about,quotes,personal,political,langs,people_main,life_main,smoking,alcohol,inspired_by,verified,timezone,mobile_phone,home_phone,site,can_post,can_see_all_posts,can_see_audio,can_write_private_message,can_send_friend_request,is_friend,friend_status,exports,counters'
            }

            if len(name_parts) == 1:
                search_params['q'] = name_parts[0]
            elif len(name_parts) >= 2:
                search_params['q'] = ' '.join(name_parts)

            url = f"https://api.vk.com/method/users.search?access_token={VK_TOKEN}&v=5.131"
            response = requests.get(url, params=search_params).json()

            if 'response' in response and 'items' in response['response']:
                return format_results(response['response']['items'])

    except Exception as e:
        print(f"Ошибка при поиске в VK: {e}")
    return []

@dp.callback_query_handler(lambda c: c.data == 'osint_vk', state='*')
async def osint_vk_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer("🔍Введите ID, ссылку VK или User для поиска:")
    await state.set_state("waiting_for_vk_query")

@dp.message_handler(state="waiting_for_vk_query")
async def process_vk_query(message: types.Message, state: FSMContext):
    query = message.text.strip()

    try:
        user_data_list = await get_vk_user_info_raw(query, VK_TOKEN)

        if not user_data_list:
            await message.answer("Ничего не найдено. Попробуйте другой запрос.")
            await state.finish()
            return

        user_data = user_data_list[0] # Take the first user data from the list

        if user_data.get('deactivated'):
            reason = user_data['deactivated']
            if reason == 'deleted':
                await message.answer("❌ Этот аккаунт ВКонтакте был удален.")
            elif reason == 'banned':
                await message.answer("🚫 Этот аккаунт ВКонтакте заблокирован.")
            await state.finish()
            return

        if user_data.get('is_closed', False) and not user_data.get('can_access_closed', False):
            await message.answer("🔒 Этот профиль ВКонтакте приватный, и у бота нет доступа к информации.")
            await state.finish()
            return

        try:
            # Pass a list containing the single user_data dictionary
            formatted_message_data = format_results([user_data], html_format=True)
            formatted_file_data = format_results([user_data], html_format=False)

            if not formatted_message_data or not formatted_file_data:
                await message.answer("⚠ Не удалось обработать данные профиля.")
                await state.finish()
                return

            caption_text_for_message = formatted_message_data.get('text', '')
            photo_url = formatted_message_data.get('photo', None)

            caption_text_for_file = formatted_file_data.get('text', '')

            if len(caption_text_for_message) > MAX_CAPTION_LENGTH:
                file_name = f"vk_info_{user_data.get('id', 'unknown')}.txt"
                text_file = io.BytesIO(caption_text_for_file.encode('utf-8'))
                await message.answer_document(
                    document=types.InputFile(text_file, filename=file_name),
                    caption="📄 Информация о пользователе ВКонтакте (слишком много текста для сообщения)"
                )
            else:
                if photo_url:
                    await message.answer_photo(
                        photo=photo_url,
                        caption=caption_text_for_message,
                        parse_mode='HTML'
                    )
                else:
                    await message.answer(
                        text=caption_text_for_message,
                        parse_mode='HTML'
                    )

        except Exception as format_error:
            await message.answer("⚠ Произошла ошибка при форматировании данных.")
            print(f"Ошибка форматирования: {format_error}")

    except Exception as vk_error:
        await message.answer("⚠ Произошла ошибка при запросе к ВКонтакте. Попробуйте позже.")
        print(f"Ошибка API ВК: {vk_error}")

    await state.finish()
