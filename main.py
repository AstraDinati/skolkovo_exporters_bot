import telebot
import schedule
import threading
import time
import random
import db

from oauth2client.service_account import ServiceAccountCredentials

from urlextract import URLExtract
import datetime
import httplib2
import googleapiclient.discovery

import profile_

TOKEN = "TOKEN"
bot = telebot.TeleBot(TOKEN)


admins_group_id = "admins_group_id"
profile_config = profile_.make_config()
club_exporters_id = "club_exporters_id"
exporters_help = "exporters_help"
admins = []


def main_mes(message, bot):
    user = message.from_user
    user_id = user.id
    message_id = message.message_id
    chat_id = message.chat.id
    username = user.username or ""
    check_user_exist = db.select("users", "id", user_id)
    if message.forward_from and chat_id > 0:
        us_id = message.forward_from.id
        check = db.select("users", "id", us_id)
        if len(check) > 0 and check[0]["permission"] > 0:
            us_data = check[0]
            if user_id in admins:
                us_data = db.select("users", "id", us_id)[0]
                Pr = profile_.Profile(us_data, profile_config)
                markup = telebot.types.InlineKeyboardMarkup()
                markup.row_width = 1
                markup.add(
                    telebot.types.InlineKeyboardButton(
                        "Удалить участника", callback_data="delete_%s" % us_id
                    )
                )
                return bot.send_message(
                    chat_id=user_id,
                    parse_mode="HTML",
                    reply_markup=markup,
                    text=Pr.get_profile_html(),
                )
            else:
                us_data = db.select("users", "id", us_id)[0]
                return bot.send_message(
                    chat_id=user_id, parse_mode="HTML", text=make_short_profile(us_data)
                )

        return bot.send_message(
            chat_id=chat_id,
            text="Участник еще не авторизовался в боте. Вы можете отправить ему пригласительную ссылку и мы поймем что он пришел от Вас \n\nссылка_на_бота?start=invite_%s"
            % user_id,
        )

    if chat_id < 0:
        if chat_id == club_exporters_id or chat_id == exporters_help:
            print("Debug: Checking new_chat_members")
            print("Debug: message.new_chat_members =", message.new_chat_members)
            if not message.new_chat_members is None:
                for new_member in message.new_chat_members:
                    user_id = new_member.id
                    check = db.select("users", "id", user_id)
                    if len(check) > 0 and check[0]["permission"] > 0:
                        markup = telebot.types.InlineKeyboardMarkup()
                        markup.row_width = 1
                        markup.add(
                            telebot.types.InlineKeyboardButton(
                                "Посмотреть профиль",
                                callback_data="profile_%s" % user_id,
                            )
                        )
                        return bot.send_message(
                            chat_id=chat_id,
                            reply_markup=markup,
                            parse_mode="markdown",
                            text="#приветствие\nВ нашей группе новый участник - *%s*\n*Направление:* %s \n*Страны:* %s \n*Продукт:* %s"
                            % (
                                check[0]["fio"],
                                check[0]["branch"],
                                check[0]["country"],
                                check[0]["product"],
                            ),
                        )
                    else:
                        return 0
        return 0
    if len(check_user_exist) == 0:
        state = ""
        permission = 0
        name = str(user.first_name or "") + " " + str(user.last_name or "")
        db.insert("users", ["id", "tg_name", "username"], [user_id, name, username])
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(
            telebot.types.InlineKeyboardButton(
                "Начать регистрацию", callback_data="register_start"
            )
        )
        check_was = db.select("was", "id", user_id)
        if len(check_was) > 0:
            print("s")
        else:
            if username != "":
                check_was = db.select("was", "username", username)
        if len(check_was) > 0:
            m, l = [], []
            for key, value in check_was[0].items():
                if value != "" and value != "id":
                    m.append(key)
                    l.append(value)
            if len(m) > 0:
                db.update("users", m, l, user_id)
                print("подтянул с кайфом")

        return bot.send_message(
            chat_id=chat_id,
            reply_markup=markup,
            text="Привет! Я Чат-бот помощник Клуба Экспортеров. Я помогу получить доступ в чат экспортеров и использовать все возможности нашего комьюнити. Для того, чтобы вступить в сообщество и стать участником - необходимо заполнить профиль. Чтобы начать регистрацию - нажмите кнопку ниже.",
        )

    text = message.text
    user_data = check_user_exist[0]
    state = user_data["state"]
    permission = user_data["permission"]
    state = user_data["state"].split("_")
    if text == "q":
        a = db.select("users", "state", "wait")
        for us_data in a:
            us_id = us_data["id"]
            Pr = profile_.Profile(us_data, profile_config)
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row_width = 1
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "Эскпортеры клуб", callback_data="approve_%s_1" % us_id
                ),
                telebot.types.InlineKeyboardButton(
                    "Exporters.help", callback_data="approve_%s_2" % us_id
                ),
            )
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "Отклонить", callback_data="decline_%s" % us_id
                )
            )
            bot.send_message(
                chat_id=admins_group_id,
                parse_mode="HTML",
                reply_markup=markup,
                text=Pr.get_profile_html(),
            )

    if text == "/newsletter" and user_id in admins:
        db.update("users", ["state"], ["waiting_for_message"], user_id)
        return bot.send_message(
            chat_id=chat_id,
            parse_mode="markdown",
            text="Введите сообщение для рассылки:",
        )

    if "waiting_for_message" in user_data["state"]:
        message_text = message.text
        db.update("users", ["newsletter_message"], [message_text], user_id)

        markup = telebot.types.InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(
            telebot.types.InlineKeyboardButton(
                "Разослать", callback_data="newsletter_send_%s" % user_id
            )
        )
        markup.add(
            telebot.types.InlineKeyboardButton(
                "Изменить сообщение", callback_data="newsletter_change_%s" % user_id
            )
        )
        markup.add(
            telebot.types.InlineKeyboardButton(
                "Отменить рассылку", callback_data="newsletter_cancel_%s" % user_id
            )
        )
        return bot.send_message(
            chat_id=chat_id,
            reply_markup=markup,
            parse_mode="markdown",
            text="*Ваше сообщение для рассылки:*\n\n" + message_text,
        )

    if text == "qq" and user_id in admins:
        meetups = db.select_column("meetups")
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(
            telebot.types.InlineKeyboardButton(
                "Оставить обратную связь", callback_data="rate_%s" % meetups[0]["id"]
            )
        )
        return bot.send_message(
            chat_id=admins_group_id,
            disable_web_page_preview=True,
            parse_mode="HTML",
            reply_markup=markup,
            text="Дорогие друзья, пожалуйста оставьте обратную связь после посещения мероприятия <b>%s</b> "
            % meetups[0]["name"],
        )

    if "editfield" in state:
        now_attr = profile_config.get_attribute(state[1])
        db.update("users", ["state", now_attr.db_name], ["", text], user_id)
        user_data[now_attr.db_name] = text

        return bot.send_message(
            chat_id=chat_id,
            reply_markup=choosefield(profile_config.get_edited_attributes()),
            parse_mode="HTML",
            text="%s \n\nВыбери поле, которое хочешь редактировть"
            % profile_.Profile(user_data, profile_config).get_profile_html(),
        )

    if user_id in admins and text == "/admin":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(
            telebot.types.InlineKeyboardButton(
                "Обновить таблицы", callback_data="updatetables"
            )
        )
        return bot.send_message(
            chat_id=chat_id,
            reply_markup=markup,
            text="Привет, администратор. Выбери что ты хочешь сделать.",
        )
    if text == "/start":
        if permission == 0:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row_width = 1
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "Начать регистрацию", callback_data="register_start"
                )
            )
            return bot.send_message(
                chat_id=chat_id,
                reply_markup=markup,
                text="Привет! Я Чат-бот помощник Чата Экспортеров. Я помогу получить доступ в чат экспортеров и использовать все возможности нашего комьюнити. Для того, чтобы вступить в сообщество и стать участником - необходимо заполнить профиль. Чтобы начать регистрацию - нажмите кнопку ниже.",
            )
        if permission > 0:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row_width = 1
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "✏️ Редактировать профиль", callback_data="edit"
                )
            )
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "🗓 Календарь мероприятий", callback_data="calendar"
                )
            )
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "🎲 Random Coffee", callback_data="random"
                )
            )
            return bot.send_message(
                chat_id=chat_id,
                reply_markup=markup,
                text="Вы в главном меню. Выберите функцию, которую хотите использовать. ",
            )
    if "register" in state:
        print("state %s" % state)
        now_attr = profile_config.get_attribute(state[1])
        if now_attr.value_type == "contact":
            if message.content_type == "contact":
                text = message.contact.phone_number
                markup = telebot.types.ReplyKeyboardRemove(selective=False)
                bot.send_message(
                    chat_id=chat_id, reply_markup=markup, text="Номер телефона принят"
                )
            else:
                doc = open("1.jpg", "rb")
                markup = telebot.types.ReplyKeyboardMarkup(
                    row_width=1, resize_keyboard=True
                )
                markup.add(
                    telebot.types.KeyboardButton(
                        "Отправить номер", request_contact=True
                    )
                )
                return bot.send_photo(
                    chat_id,
                    doc,
                    reply_markup=markup,
                    caption="Пожалуйста, отправьте именно номер по кнопке чтобы я смог Вас авторизовать.Если кнопка не видна - откройте меню как указано на картинке выше. ",
                )
        next_attr = now_attr.next

        if now_attr.db_name == "company":
            urls = URLExtract().find_urls(text)
            if len(urls) > 0:
                next_attr = next_attr.next
                db.update("users", ["site"], [", ".join(urls)], user_id)
        if now_attr.db_name == "birthday":
            if check_date(text):
                text = check_date(text)
            else:
                return bot.send_message(
                    chat_id=chat_id,
                    text="Пожалуйста, введите дату рождения именно в таком формате дд.мм.гггг",
                )
        if next_attr == "":
            db.update("users", ["state", state[1]], ["wait", text], user_id)
            user_data[state[1]] = text
            Pr = profile_.Profile(user_data, profile_config)
            bot.send_message(
                chat_id=chat_id, parse_mode="HTML", text=Pr.get_profile_html()
            )
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row_width = 1
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "Эскпортеры клуб", callback_data="approve_%s_1" % user_id
                ),
                telebot.types.InlineKeyboardButton(
                    "Exporters.help", callback_data="approve_%s_2" % user_id
                ),
            )
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "Отклонить", callback_data="decline_%s" % user_id
                )
            )
            bot.send_message(
                chat_id=admins_group_id,
                parse_mode="HTML",
                reply_markup=markup,
                text=Pr.get_profile_html(),
            )
            return bot.send_message(
                chat_id=chat_id,
                text="Ваш профиль отправлен на адмисcию. Выше можешь его посмотреть. Как только тебя одобрят - я пришлю тебе уведомление и ссылку на доступ в группу.  ",
            )
        if (
            user_data[next_attr.db_name] != ""
            and not user_data[next_attr.db_name] is None
        ):
            while (user_data[next_attr.db_name]) != "" and not user_data[
                next_attr.db_name
            ] is None:
                next_attr = next_attr.next
        db.update(
            "users",
            ["state", state[1]],
            ["register_" + next_attr.db_name, text],
            user_id,
        )
        markup = ""
        start_text = "Поле %s из %s\n\n" % (
            next_attr.index,
            len(profile_config.attributes),
        )
        added_text = ""
        if next_attr.value_type == "choosesome":
            markup = choose_some(
                next_attr.array_of_values,
                user_data[next_attr.db_name],
                next_attr,
                "register_",
            )
            added_text = next_attr.added_text + user_data[next_attr.db_name]
        elif next_attr.value_type == "chooseoneof":
            markup = choose_one(next_attr.array_of_values, next_attr, "register_")
        elif next_attr.value_type == "contact":
            markup = telebot.types.ReplyKeyboardMarkup(
                row_width=1, resize_keyboard=True
            )
            markup.add(
                telebot.types.KeyboardButton("Отправить номер", request_contact=True)
            )
        return bot.send_message(
            chat_id=chat_id,
            reply_markup=markup,
            text=start_text + next_attr.ask_text + added_text,
        )
    if message.forward_from and permission > 0:
        us_id = message.forward_from.id
        check = db.select("users", "id", us_id)
        if len(check) > 0 and check[0]["permission"] > 0:
            if user_id in admins:
                us_data = db.select("users", "id", us_id)[0]
                Pr = profile_.Profile(us_data, profile_config)
                return bot.send_message(
                    chat_id=user_id, parse_mode="HTML", text=Pr.get_profile_html()
                )

            us_data = db.select("users", "id", us_id)[0]
            return bot.send_message(
                chat_id=user_id, parse_mode="HTML", text=make_short_profile(us_data)
            )
        else:
            return bot.send_message(
                chat_id=chat_id,
                text="Участник еще не авторизовался в боте. Вы можете отправить ему пригласительную ссылку и мы поймем что он пришел от Вас \n\nссылка_на_бота?start=invite_%s"
                % user_id,
            )

    if permission > 0:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(
            telebot.types.InlineKeyboardButton(
                "✏️ Редактировать профиль", callback_data="edit"
            )
        )
        markup.add(
            telebot.types.InlineKeyboardButton(
                "🗓 Календарь мероприятий", callback_data="calendar"
            )
        )
        markup.add(
            telebot.types.InlineKeyboardButton(
                "🎲 Random Coffee", callback_data="random"
            )
        )
        return bot.send_message(
            chat_id=chat_id,
            reply_markup=markup,
            text="Вы в главном меню. Выберите функцию, которую хотите использовать. ",
        )
    if state == "wait":
        return bot.send_message(
            chat_id=chat_id,
            text="Ваш профиль находится на адмиссии. Пожалуйста, подождите немного. Как только Вас одобрят - я пришлю ссылку на чат и дам доступ к основному функционалу. ",
        )


def call_mes(call, bot):
    print("call_mes")
    user = call.from_user
    message_id = call.message.message_id
    user_id = user.id
    call_id = call.id
    callback_data = call.data.split("_")
    callback_id = call.id
    chat_id = user_id
    chatx_id = call.message.chat.id

    check_user_exist = db.select("users", "id", user_id)
    if len(check_user_exist) == 0:
        return bot.answer_callback_query(
            call_id, text="Пожалуйста, пройдите регистрацию в чатботе", show_alert=True
        )
    user_data = check_user_exist[0]
    name = user_data["tg_name"]
    username = user_data["username"]
    state = user_data["state"]
    function = callback_data[0]
    if function == "newsletter":
        newsletter_state = callback_data[1]
        if newsletter_state == "send":
            all_users = db.select_users_with_permission_1_or_2()
            message_text = db.get_newsletter_message_for_user(callback_data[2])
            send_newsletter_to_users(all_users, message_text, bot)

            db.update("users", ["state"], ["menu"], callback_data[2])

            bot.delete_message(chat_id=callback_data[2], message_id=message_id)

            return bot.send_message(
                chat_id=callback_data[2],
                text="Сообщение разослано",
                parse_mode="HTML",
            )
        if newsletter_state == "change":
            bot.delete_message(chat_id=callback_data[2], message_id=message_id)

            return bot.send_message(
                chat_id=callback_data[2],
                text="Введите новое сообщение:",
                parse_mode="HTML",
            )
        if newsletter_state == "cancel":
            db.update("users", ["newsletter_message"], [""], callback_data[2])
            db.update("users", ["state"], ["menu"], callback_data[2])

            bot.answer_callback_query(
                call_id, text="Рассылка отменена", show_alert=True
            )

            bot.delete_message(chat_id=callback_data[2], message_id=message_id)

            return

    if function == "edit":
        return bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=choosefield(profile_config.get_edited_attributes()),
            parse_mode="HTML",
            text="%s \n\nВыбери поле, которое хочешь редактировть"
            % profile_.Profile(user_data, profile_config).get_profile_html(),
        )
    if function == "rate":
        if len(check_user_exist) == 0:
            return bot.answer_callback_query(
                call_id,
                text="Пожалуйста, пройдите сначала регистрацию",
                show_alert=True,
            )
        meet_id = callback_data[1]
        meet_row = db.select("meetups", "id", meet_id)[0]
        meetup_name = meet_row["name"]
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row_width = 1
        r = ""
        for i in range(1, 6):
            r += "⭐️"
            markup.add(
                telebot.types.InlineKeyboardButton(
                    r, callback_data="rate2_%s_%s" % (meet_id, i)
                )
            )
        bot.send_message(
            chat_id=user_id,
            reply_markup=markup,
            parse_mode="HTML",
            text="Пожалуйста, поставьте оценку по мероприятию <b>%s</b>" % meetup_name,
        )
        return bot.answer_callback_query(
            call_id, text="Вам пришло сообщение от бота.", show_alert=True
        )
    if function == "rate2":
        meet_id = callback_data[1]
        meet_row = db.select("meetups", "id", meet_id)[0]
        db.insert(
            "ratings",
            ["meet_id", "user_id", "rate"],
            [meet_id, user_id, int(callback_data[2])],
        )
        return bot.edit_message_text(
            chat_id=chat_id, message_id=message_id, text="Спасибо за Вашу оценку!"
        )
    if function == "editfield":
        now_attr = profile_config.get_attribute(callback_data[1])
        if now_attr.value_type == "choosesome":
            added_text = now_attr.added_text
            if "page" in callback_data:
                return bot.edit_message_text(
                    chat_id=chat_id,
                    reply_markup=choose_some(
                        now_attr.array_of_values,
                        user_data[now_attr.db_name],
                        now_attr,
                        "editfield_",
                        page=int(callback_data[3]),
                    ),
                    text=now_attr.ask_text + added_text + user_data[now_attr.db_name],
                    message_id=message_id,
                )
            elif "save" in callback_data:
                return bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode="HTML",
                    reply_markup=choosefield(profile_config.get_edited_attributes()),
                    text="%s \n\nВыберите поле, которое хотите редактировть"
                    % profile_.Profile(user_data, profile_config).get_profile_html(),
                )
            else:
                user_values = user_data[now_attr.db_name].split(", ")
                if len(callback_data) < 3:
                    markup = choose_some(
                        now_attr.array_of_values,
                        user_data[now_attr.db_name],
                        now_attr,
                        "editfield_",
                    )
                    added_text = now_attr.added_text + user_data[now_attr.db_name]
                    return bot.edit_message_text(
                        chat_id=chat_id,
                        reply_markup=markup,
                        text=now_attr.ask_text
                        + added_text
                        + ", ".join(user_values).strip().strip(","),
                        message_id=message_id,
                    )
                choosen_value = now_attr.array_of_values[int(callback_data[2])]["name"]

                if choosen_value in user_values:
                    user_values.remove(choosen_value)
                else:
                    user_values.append(choosen_value)
                new_values = ", ".join(user_values).strip().strip(",")
                db.update("users", [now_attr.db_name], [new_values], user_id)
                markup = choose_some(
                    now_attr.array_of_values,
                    new_values,
                    now_attr,
                    "editfield_",
                    page=int(callback_data[3]),
                )
                return bot.edit_message_text(
                    chat_id=chat_id,
                    reply_markup=markup,
                    text=now_attr.ask_text
                    + added_text
                    + ", ".join(user_values).strip().strip(","),
                    message_id=message_id,
                )
        elif now_attr.value_type == "chooseoneof":
            if "page" in callback_data:
                markup = choose_one(
                    now_attr.array_of_values,
                    now_attr,
                    "editfield_",
                    page=int(callback_data[3]),
                )
                return bot.edit_message_text(
                    chat_id=chat_id,
                    reply_markup=markup,
                    text=now_attr.ask_text,
                    message_id=message_id,
                )
            else:
                if len(callback_data) < 3:
                    markup = choose_one(
                        now_attr.array_of_values, now_attr, "editfield_", page=0
                    )
                    return bot.edit_message_text(
                        chat_id=chat_id,
                        reply_markup=markup,
                        text=now_attr.ask_text,
                        message_id=message_id,
                    )
                choosen_value = now_attr.array_of_values[int(callback_data[2])]
                db.update("users", [now_attr.db_name], [choosen_value], user_id)
                return bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=choosefield(profile_config.get_edited_attributes()),
                    parse_mode="HTML",
                    text="%s \n\nВыберите поле, которое хочтите редактировть"
                    % profile_.Profile(user_data, profile_config).get_profile_html(),
                )
        else:
            now_attr = profile_config.get_attribute(callback_data[1])
            db.update("users", ["state"], ["editfield_%s" % now_attr.db_name], user_id)
            return bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, text=now_attr.ask_text
            )
    if "register" in callback_data:
        if callback_data[1] == "start":
            now_attr = profile_config.attributes[0]
            if user_data[now_attr.db_name] != "":
                while (user_data[now_attr.db_name]) != "":
                    now_attr = now_attr.next
                    print(now_attr)

            start_text = "Поле %s из %s\n\n" % (
                now_attr.index,
                len(profile_config.attributes),
            )
            db.update("users", ["state"], ["register_" + now_attr.db_name], user_id)
            return bot.edit_message_text(
                chat_id=chat_id,
                text=start_text + now_attr.ask_text,
                message_id=message_id,
            )
        else:
            now_attr = profile_config.get_attribute(callback_data[1])
            start_text = "Поле %s из %s\n\n" % (
                now_attr.index,
                len(profile_config.attributes),
            )
            next_attr = now_attr.next

            if now_attr.value_type == "choosesome":
                added_text = now_attr.added_text
                if "page" in callback_data:
                    return bot.edit_message_text(
                        chat_id=chat_id,
                        reply_markup=choose_some(
                            now_attr.array_of_values,
                            user_data[now_attr.db_name],
                            now_attr,
                            "register_",
                            page=int(callback_data[3]),
                        ),
                        text=start_text
                        + now_attr.ask_text
                        + added_text
                        + user_data[now_attr.db_name],
                        message_id=message_id,
                    )
                elif "save" in callback_data:
                    start_text = "Поле %s из %s\n\n" % (
                        next_attr.index,
                        len(profile_config.attributes),
                    )
                    markup = ""
                    if next_attr == "":
                        db.update("users", ["state"], ["wait"], user_id)
                        Pr = profile_.Profile(user_data, profile_config)
                        bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            parse_mode="HTML",
                            text=Pr.get_profile_html(),
                        )
                        markup = telebot.types.InlineKeyboardMarkup()
                        markup.row_width = 1
                        markup.add(
                            telebot.types.InlineKeyboardButton(
                                "Эскпортеры клуб",
                                callback_data="approve_%s_1" % user_id,
                            ),
                            telebot.types.InlineKeyboardButton(
                                "Exporters.help", callback_data="approve_%s_2" % user_id
                            ),
                        )
                        markup.add(
                            telebot.types.InlineKeyboardButton(
                                "Отклонить", callback_data="decline_%s" % user_id
                            )
                        )
                        bot.send_message(
                            chat_id=admins_group_id,
                            parse_mode="HTML",
                            reply_markup=markup,
                            text=Pr.get_profile_html(),
                        )
                        return bot.send_message(
                            chat_id=chat_id,
                            text="Ваш профиль отправлен на адмиссию. Выше можешь его посмотреть. Как только тебя одобрят - я пришлю тебе уведомление и ссылку на доступ в группу.  ",
                        )

                    if next_attr.value_type == "choosesome":
                        markup = choose_some(
                            next_attr.array_of_values,
                            user_data[next_attr.db_name],
                            next_attr,
                            "register_",
                        )
                    elif next_attr.value_type == "chooseoneof":
                        markup = choose_one(
                            next_attr.array_of_values, next_attr, "register_"
                        )
                    elif next_attr.value_type == "contact":
                        markup = telebot.types.ReplyKeyboardMarkup(
                            row_width=1, resize_keyboard=True
                        )
                        markup.add(
                            telebot.types.KeyboardButton(
                                "Отправить номер", request_contact=True
                            )
                        )
                        db.update(
                            "users",
                            ["state"],
                            ["register_" + next_attr.db_name],
                            user_id,
                        )
                        bot.delete_message(chat_id=chat_id, message_id=message_id)
                        return bot.send_message(
                            chat_id=chat_id,
                            reply_markup=markup,
                            text=start_text + next_attr.ask_text,
                        )
                    db.update(
                        "users", ["state"], ["register_" + next_attr.db_name], user_id
                    )
                    return bot.edit_message_text(
                        chat_id=chat_id,
                        reply_markup=markup,
                        text=start_text + next_attr.ask_text,
                        message_id=message_id,
                    )
                else:
                    user_values = user_data[now_attr.db_name].split(", ")
                    choosen_value = now_attr.array_of_values[int(callback_data[2])][
                        "name"
                    ]
                    if choosen_value in user_values:
                        user_values.remove(choosen_value)
                    else:
                        user_values.append(choosen_value)
                    new_values = ", ".join(user_values).strip().strip(",")
                    db.update("users", [now_attr.db_name], [new_values], user_id)
                    markup = choose_some(
                        now_attr.array_of_values,
                        new_values,
                        now_attr,
                        "register_",
                        page=int(callback_data[3]),
                    )
                    return bot.edit_message_text(
                        chat_id=chat_id,
                        reply_markup=markup,
                        text=start_text
                        + now_attr.ask_text
                        + added_text
                        + ", ".join(user_values).strip().strip(","),
                        message_id=message_id,
                    )
            elif now_attr.value_type == "chooseoneof":
                if "page" in callback_data:
                    markup = choose_one(
                        now_attr.array_of_values,
                        now_attr,
                        "register_",
                        page=int(callback_data[3]),
                    )
                    return bot.edit_message_text(
                        chat_id=chat_id,
                        reply_markup=markup,
                        text=start_text + now_attr.ask_text,
                        message_id=message_id,
                    )
                else:
                    markup = ""
                    choosen_value = now_attr.array_of_values[int(callback_data[2])]
                    if next_attr == "":
                        db.update(
                            "users",
                            [now_attr.db_name, "state"],
                            [choosen_value, "wait"],
                            user_id,
                        )
                        user_data[now_attr.db_name] = choosen_value
                        Pr = profile_.Profile(user_data, profile_config)
                        bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            parse_mode="HTML",
                            text=Pr.get_profile_html(),
                        )
                        markup = telebot.types.InlineKeyboardMarkup()
                        markup.row_width = 1
                        markup.add(
                            telebot.types.InlineKeyboardButton(
                                "Эскпортеры клуб",
                                callback_data="approve_%s_1" % user_id,
                            ),
                            telebot.types.InlineKeyboardButton(
                                "Exporters.help", callback_data="approve_%s_2" % user_id
                            ),
                        )
                        markup.add(
                            telebot.types.InlineKeyboardButton(
                                "Отклонить", callback_data="decline_%s" % user_id
                            )
                        )
                        bot.send_message(
                            chat_id=admins_group_id,
                            parse_mode="HTML",
                            reply_markup=markup,
                            text=Pr.get_profile_html(),
                        )
                        return bot.send_message(
                            chat_id=chat_id,
                            text="Ваш профиль отправлен на адмиссию. Выше можешь его посмотреть. Как только тебя одобрят - я пришлю тебе уведомление и ссылку на доступ в группу.  ",
                        )
                    if user_data[next_attr.db_name] != "":
                        while (user_data[next_attr.db_name]) != "":
                            next_attr = next_attr.next

                    db.update(
                        "users",
                        [now_attr.db_name, "state"],
                        [choosen_value, "register_" + next_attr.db_name],
                        user_id,
                    )

                    start_text = "Поле %s из %s\n\n" % (
                        next_attr.index,
                        len(profile_config.attributes),
                    )
                    if next_attr.value_type == "choosesome":
                        markup = choose_some(
                            next_attr.array_of_values,
                            user_data[next_attr.db_name],
                            next_attr,
                            "register_",
                        )
                    elif next_attr.value_type == "chooseoneof":
                        markup = choose_one(
                            next_attr.array_of_values, next_attr, "register_"
                        )
                    elif next_attr.value_type == "contact":
                        markup = telebot.types.ReplyKeyboardMarkup(
                            row_width=1, resize_keyboard=True
                        )
                        markup.add(
                            telebot.types.KeyboardButton(
                                "Отправить номер", request_contact=True
                            )
                        )
                        bot.delete_message(chat_id=chat_id, message_id=message_id)
                        return bot.send_message(
                            chat_id=chat_id,
                            reply_markup=markup,
                            text=start_text + next_attr.ask_text,
                        )
                    db.update(
                        "users", ["state"], ["register_" + next_attr.db_name], user_id
                    )
                    return bot.edit_message_text(
                        chat_id=chat_id,
                        reply_markup=markup,
                        text=start_text + next_attr.ask_text,
                        message_id=message_id,
                    )
            else:
                now_attr = profile_config.get_attribute(callback_data[1])
                next_attr = now_attr.next
                if user_data[next_attr.db_name] != "":
                    while (user_data[next_attr.db_name]) != "":
                        next_attr = next_attr.next
                if next_attr == "":
                    Pr = profile_.Profile(user_data, profile_config)
                    bot.send_message(
                        chat_id=chat_id, parse_mode="HTML", text=Pr.get_profile_html()
                    )
                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.row_width = 1
                    markup.add(
                        telebot.types.InlineKeyboardButton(
                            "Эскпортеры клуб", callback_data="approve_%s_1" % user_id
                        ),
                        telebot.types.InlineKeyboardButton(
                            "Exporters.help", callback_data="approve_%s_2" % user_id
                        ),
                    )
                    markup.add(
                        telebot.types.InlineKeyboardButton(
                            "Отклонить", callback_data="decline_%s" % user_id
                        )
                    )
                    bot.send_message(
                        chat_id=admins_group_id,
                        parse_mode="HTML",
                        reply_markup=markup,
                        text=Pr.get_profile_html(),
                    )
                    return bot.send_message(
                        chat_id=chat_id,
                        text="Ваш профиль отправлен на адмиссию. Выше можешь его посмотреть. Как только тебя одобрят - я пришлю тебе уведомление и ссылку на доступ в группу.  ",
                    )
                markup = ""
                start_text = "Поле %s из %s\n\n" % (
                    next_attr.index,
                    len(profile_config.attributes),
                )
                added_text = ""
                if next_attr.value_type == "choosesome":
                    markup = choose_some(
                        next_attr.array_of_values,
                        user_data[next_attr.db_name],
                        next_attr,
                        "register_",
                    )
                    added_text = next_attr.added_text + user_data[next_attr.db_name]
                elif next_attr.value_type == "chooseoneof":
                    markup = choose_one(
                        next_attr.array_of_values, next_attr, "register_"
                    )
                elif next_attr.value_type == "contact":
                    markup = telebot.types.ReplyKeyboardMarkup(
                        row_width=1, resize_keyboard=True
                    )
                    markup.add(
                        telebot.types.KeyboardButton(
                            "Отправить номер", request_contact=True
                        )
                    )
                return bot.send_message(
                    chat_id=chat_id,
                    reply_markup=markup,
                    text=start_text + next_attr.ask_text + added_text,
                )

    if function == "register":
        if callback_data[1] == "fio":
            db.update("users", ["state"], ["register_fio"], user_id)
            return bot.edit_message_text(
                chat_id=chat_id,
                parse_mode="markdown",
                text="*Регистрация займет около 10 минут. При регистрации мы запрашиваем подробную информацию о Вашем экспортном бизнесе, чтобы быть Вам наиболее полезным.*\n  \n\nПожалуйста, введи фамилию, имя и отчество.",
                message_id=message_id,
            )
        if callback_data[1] == "money":
            exps = [
                "До 300 млн. руб.",
                "300-800 млн. руб.",
                "800 млн.- 1 млрд. Руб.",
                "Более 1 млрд. руб.",
            ]
            db.update(
                "users",
                ["state", "money"],
                ["register_clientscat", exps[int(callback_data[2])]],
                user_id,
            )
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row_width = 1
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "B2B", callback_data="register_clientscat_0"
                )
            )
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "B2C", callback_data="register_clientscat_1"
                )
            )
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "B2G", callback_data="register_clientscat_2"
                )
            )
            return bot.edit_message_text(
                chat_id=chat_id,
                reply_markup=markup,
                text="Укажите основной тип Ваших клиентов.",
                message_id=message_id,
            )
        if callback_data[1] == "clientscat":
            exps = ["B2B", "B2C", "B2G"]
            db.update(
                "users",
                ["state", "clientscat"],
                ["register_clients", exps[int(callback_data[2])]],
                user_id,
            )
            return bot.edit_message_text(
                chat_id=chat_id,
                text="Расскажите подробнее - какие ключевые клиенты Вашей компании на сегодняшний день. ",
                message_id=message_id,
            )
        if callback_data[1] == "prefer":
            exps = ["Телефон", "Почта"]
            db.update(
                "users",
                ["state", "prefer"],
                ["register_live", exps[int(callback_data[2])]],
                user_id,
            )
            return bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="Напишите в каком городе Вы проживаете большую часть времени.",
            )

        if callback_data[1] == "meetup":
            if callback_data[2] == "0":
                l = "Да"
            else:
                l = "Нет"
            user_data["meetup"] = l
            db.update("users", ["meetup", "state"], [l, "wait"], user_id)
            bot.edit_message_text(
                chat_id=chat_id,
                parse_mode="HTML",
                text=make_profile(user_data),
                message_id=message_id,
            )

            bot.send_message(
                chat_id=chat_id,
                text="Отлично! Ваш профиль заполнен и отправлен на адмиссию. Вы можете посмотреть его Выше. Другим участникам будет доступна о Вас информация из полей: Отрасли, основные продукты и Страны экспорта. Остальные параметры будут доступны только администрации сообщества.  ",
            )
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row_width = 1
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "Эскпортеры клуб", callback_data="approve_%s_1" % user_id
                ),
                telebot.types.InlineKeyboardButton(
                    "Exporters.help", callback_data="approve_%s_2" % user_id
                ),
            )
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "Отклонить", callback_data="decline_%s" % user_id
                )
            )

            return bot.send_message(
                chat_id=admins_group_id,
                parse_mode="HTML",
                reply_markup=markup,
                text="Участник заполнил профиль. %s" % make_profile(user_data),
            )

    if function == "addbranch":
        tags = db.select_column("branch")
        tag_id = int(callback_data[1])
        page = tag_id // 5
        if user_data["branch"] is None:
            user_tags = ""
            tagx = []
        else:
            user_tags = user_data["branch"]
            tagx = user_tags.split(", ")
        tag_name = tags[tag_id]["name"]
        if tag_name in user_tags:
            tagx.remove(tag_name)
            user_tags = ", ".join(tagx)
        else:
            tagx.append(tag_name)
            user_tags = ", ".join(tagx)
        db.update("users", ["branch"], [user_tags.lstrip(", ")], user_id)
        if user_tags == "":
            user_tags = "не указано"
        return bot.edit_message_text(
            chat_id=chat_id,
            reply_markup=make_listing(
                tags, "addbranch", 1, "name", "", page, user_tags
            ),
            text="Твои выбранные отрасли: %s" % user_tags.lstrip(", "),
            message_id=message_id,
        )

    if function == "addbranchpage":
        page = int(callback_data[1])
        tags = db.select_column("branch")
        if user_data["branch"] is None:
            user_tags = "Не указано"
        else:
            user_tags = user_data["branch"]
        if user_tags == "":
            user_tags = "не указано"
        tex = "Твои выбранные отрасли: %s" % user_tags.lstrip(", ")
        return bot.edit_message_text(
            chat_id=chat_id,
            reply_markup=make_listing(
                tags, "addbranch", 1, "name", "", page, user_tags
            ),
            text=tex,
            message_id=message_id,
        )

    if function == "approve":
        us_id = callback_data[1]
        if callback_data[2] == "1":
            url = "url"
            perm = 1
            lm = "#клубэкспортеры"
        else:
            url = bot.export_chat_invite_link(exporters_help)
            perm = 2
            lm = "#exportershelp"
        us_data = db.select("users", "id", us_id)[0]
        db.update("users", ["permission", "state"], [perm, "menu"], us_id)
        bot.edit_message_text(
            chat_id=chatx_id,
            parse_mode="HTML",
            text="%s\nУчастник одобрен by %s\n%s"
            % (lm, user_data["tg_name"], make_profile(us_data)),
            message_id=message_id,
        )
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(telebot.types.InlineKeyboardButton("Перейти в группу", url=url))
        markup.add(telebot.types.InlineKeyboardButton("Меню", callback_data="menu_0"))
        return bot.send_message(
            chat_id=us_id,
            reply_markup=markup,
            text="Ваш профиль одобрен! Теперь Вы можете перейти в основную группу по ссылке ниже. А также в основное меню. Как только Вы вступите в группу - я отправлю сообщение в чат с указанием краткой информации о Вас. ",
        )
    if function == "decline":
        us_id = callback_data[1]
        us_data = db.select("users", "id", us_id)
        if us_data:
            us_data = us_data[0]
        else:
            us_data = {}
        db.update("users", ["permission", "state"], [-1, "decline"], us_id)
        bot.edit_message_text(
            chat_id=chatx_id,
            parse_mode="HTML",
            text="Участник отклонен by %s\n %s"
            % (user_data["tg_name"], make_profile(us_data)),
            message_id=message_id,
        )
        return bot.send_message(
            chat_id=us_id,
            text="К сожалению Ваш профиль не прошел адмиссию. Вы  не можешь вступить в наше комьюнити.",
        )
    if function == "updatetables":
        print("updating")
        update_users_to_google()
        update_meetups_from_table()
        update_raitings_to_google()
        return bot.answer_callback_query(
            call_id, text="Обновил все таблицы.", show_alert=True
        )
    if function == "calendar":
        if len(callback_data) == 1:
            meetup_num = 0
        else:
            meetup_num = int(callback_data[1])
        meetups = db.select_column("meetups")
        return bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            parse_mode="HTML",
            reply_markup=meetup_list(meetups, meetup_num),
            text=meetup_text(meetups[meetup_num]),
        )
    if function == "random":
        if len(callback_data) > 1:
            db.update("users", ["random"], [callback_data[1]], user_id)
            user_data["random"] = int(callback_data[1])
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row_width = 1
        if int(user_data["random"]) == 1:
            ls = "👍 Вы участвуте в знакомствах"
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "🔕 Не хочу участвовать", callback_data="random_0"
                )
            )
        else:
            ls = "🔕 Вы не участвуете в знакомствах"
            markup.add(
                telebot.types.InlineKeyboardButton(
                    "👍 Участвовать", callback_data="random_1"
                )
            )
        markup.add(
            telebot.types.InlineKeyboardButton("Вернуться в меню", callback_data="menu")
        )

        return bot.edit_message_text(
            chat_id=chat_id,
            reply_markup=markup,
            parse_mode="HTML",
            text="Ваш текущий статус:  <b>%s</b>\n\nЧтобы поменять статус - нажмите кнопку ниже"
            % ls,
            message_id=message_id,
        )
    if function == "menu":
        if len(callback_data) > 1:
            tt = """*Пару слов о функциях чатбота:* 

*1)* Вы уже создали свой профиль отвечая на вопросы. Для всех участников чата публична информация о Вашей отрасли и странах, с которыми Вы работаете. Остальная информация доступна только администрации нашего клуба для проработки запросов.  
*2)* Вы сами можете знакомиться с другими участниками и узнавать базовую информацию о них переслав сообщение боту (если у участника не скрытый аккаунт). Я выдам профиль а также дам возможность Вам познакомиться, то есть обменяю Вас контактами. 
*3)* В чатботе реализована функция Random Coffee - популярный формат случайных знакомств, где каждую неделю бот будет предлагать Вам познакомиться с другим участником клуба. По умолчанию Вы участвуете, но если у Вас нет времени или желания - можете отменить участие в главном меню или при следующем знакомстве. 
*4)* В боте отображается календарь ближайших мероприятий, где Вы можете узнать о ближайших встречах и планировать свое время. Это сообщение будет в закрепленных и Вы всегда можете посмотреть его если что-то будет непонятно.  
			"""
            aa = bot.send_message(chat_id=chat_id, parse_mode="markdown", text=tt)
            bot.pin_chat_message(chat_id=user_id, message_id=aa.message_id)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(telebot.types.InlineKeyboardButton("Ссылка на группу", url="url"))
        markup.add(
            telebot.types.InlineKeyboardButton(
                "✏️ Редактировать профиль", callback_data="edit"
            )
        )
        markup.add(
            telebot.types.InlineKeyboardButton(
                "🗓 Календарь мероприятий", callback_data="calendar"
            )
        )
        markup.add(
            telebot.types.InlineKeyboardButton(
                "🎲 Random Coffee", callback_data="random"
            )
        )
        return bot.edit_message_text(
            chat_id=chat_id,
            reply_markup=markup,
            text="Вы в главном меню.",
            message_id=message_id,
        )
    if function == "profile":
        us_id = callback_data[1]
        us_data = db.select("users", "id", us_id)[0]
        bot.answer_callback_query(
            call_id, text="Отправил профиль Вам в личные сообщения", show_alert=True
        )
        return bot.send_message(
            chat_id=user_id, parse_mode="HTML", text=make_short_profile(us_data)
        )
    if function == "delete":
        us_id = callback_data[1]
        db.update("users", ["permission"], [-1], us_id)
        return bot.edit_message_text(
            chat_id=chat_id, message_id=message_id, text="Участник удален. "
        )
    if function == "addmeetup":
        a = callback_data[1]
        t = user_data["fio"]
        check = db.select("meetups", "id", a)[0]
        if check["users2"] == "":
            m = user_data["fio"]
            db.update("meetups", ["users2"], [m], check["id"])
        else:
            r = check["users2"].split(", ")
            if not user_data["fio"] in r:
                r.append(user_data["fio"])
                m = ", ".join(r).strip().strip(",")
                db.update("meetups", ["users2"], [m], check["id"])
        return bot.answer_callback_query(
            call_id, text="Вы записаны в список участников", show_alert=True
        )


def send_newsletter_to_users(users, message_text, bot):
    for user in users:
        try:
            bot.send_message(
                chat_id=user["id"],
                parse_mode="markdown",
                text=message_text,
            )
        except telebot.apihelper.ApiException as e:
            if "Chat not found" in str(e):
                print(f"User1 ({user['id']}) не в чате с ботом.")
            else:
                print(f"Ошибка при отправке сообщения пользователю {user['id']}: {e}")


def make_listing(listx, button_name, width, name1, name2, page=0, rowx=""):
    markup2 = telebot.types.InlineKeyboardMarkup()
    markup2.row_width = width
    list_len = len(listx)
    for row in range(5):
        buttons = []
        for column in range(width):
            ll = page * width * 5 + row * 1 + column
            if ll < list_len:
                rs = str(listx[ll][name1])
                if rs in rowx:
                    rs = "✔️" + rs
                buttons.append(
                    telebot.types.InlineKeyboardButton(
                        rs, callback_data=button_name + "_" + str(ll)
                    )
                )
        markup2.row(*buttons)
    buttons = []
    if page > 0:
        buttons.append(
            telebot.types.InlineKeyboardButton(
                "⬅️", callback_data=button_name + "page_" + str(page - 1)
            )
        )
    if (page + 1) < (list_len // (width * 5)):
        buttons.append(
            telebot.types.InlineKeyboardButton(
                "➡️", callback_data=button_name + "page_" + str(page + 1)
            )
        )
    markup2.row(*buttons)
    buttons = []
    buttons.append(
        telebot.types.InlineKeyboardButton(
            "Сохранить👌", callback_data="%ssave" % button_name
        )
    )
    markup2.row(*buttons)

    return markup2


def check_date(text):
    if len(text) != 10:
        print("format")
        return False
    year = int(text[6:])
    month = int(text[3:5])
    day = int(text[0:2])
    if year < 1900 or year > 2100:
        print("year")
        return False
    if month > 12 or month < 1:
        print("month")
        return False
    if day > 31 or day < 1:
        print("day")
        return False
    return "%s-%s-%s" % (year, str(month).zfill(2), str(day).zfill(2))


def make_profile(data):
    tex = "<b>Профиль:</b> \n"
    key_mas = {
        "fio": "ФИО",
        "company": "Компания",
        "site": "Сайт",
        "education": "Образование",
        "branch": "Направление",
        "product": "Основные продукты",
        "country": "Страны экспорта",
        "plans": "Приоритетные направления",
        "clients": "Клиенты",
        "money": "Оборот",
        "clientscat": "Категория клиентов",
        "birthday": "День рождения",
        "email": "E-mail",
        "phone": "Телефон",
        "live": "Город проживания",
        "meetup": "Готовность встреч в Москве",
    }
    if data["username"] != "":
        tex += "\n@%s" % data["username"]
    tex += "\n<a href='tg://user?id=%s'>%s</a>" % (data["id"], data["fio"])

    for name in key_mas.keys():
        tex += "\n<b>%s:</b> %s" % (key_mas[name], data[name])
    return tex


def make_short_profile(data):
    tex = "<b>Профиль:</b> \n"
    key_mas = {
        "fio": "ФИО",
        "branch": "Направление",
        "product": "Основные продукты",
        "country": "Страны экспорта",
        "site": "Сайт",
    }
    if data["username"] != "":
        tex += "\n@%s" % data["username"]
    tex += "\n<a href='tg://user?id=%s'>%s</a>" % (data["id"], data["fio"])

    for name in key_mas.keys():
        tex += "\n<b>%s:</b> %s" % (key_mas[name], data[name])
    return tex


def make_coffee_profile(data):
    tex = "<b>Профиль вашего партнёра по кофе ☕️:</b> \n"
    key_mas = {
        "fio": "ФИО",
        "branch": "Направление",
        "product": "Основные продукты",
        "country": "Страны экспорта",
        "site": "Сайт",
    }
    if data["username"] != "":
        tex += "\n@%s" % data["username"]
    tex += "\n<a href='tg://user?id=%s'>%s</a>" % (data["id"], data["fio"])

    for name in key_mas.keys():
        tex += "\n<b>%s:</b> %s" % (key_mas[name], data[name])
    return tex + "\nВаш партнёр получил такой же профиль о Вас"


def update_raitings_to_google():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "kkey.json", scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    httpAuth = credentials.authorize(httplib2.Http())
    service = googleapiclient.discovery.build("sheets", "v4", http=httpAuth)
    SAMPLE_SPREADSHEET_ID = "SAMPLE_SPREADSHEET_ID"
    range_name = "Обратная связь!A2:D"

    ratings_data = db.get_ratings_data()
    meetups_data = db.get_meetups_data()
    users_data = db.get_users_data()
    transformed_data = transform_ratings_data(ratings_data, meetups_data, users_data)

    values = []
    for item in transformed_data:
        values.append([item["Id"], item["Событие"], item["Участник"], item["Оценка"]])

    clear_values_request = {"ranges": [range_name]}
    service.spreadsheets().values().batchClear(
        spreadsheetId=SAMPLE_SPREADSHEET_ID, body=clear_values_request
    ).execute()

    update_values_request = {"values": values}
    service.spreadsheets().values().update(
        spreadsheetId=SAMPLE_SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body=update_values_request,
    ).execute()

    print("Данные успешно обновлены в Google Sheets.")


def update_users_to_google():
    values = []
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "kkey.json", ["https://www.googleapis.com/auth/spreadsheets"]
    )
    httpAuth = credentials.authorize(httplib2.Http())
    service = googleapiclient.discovery.build("sheets", "v4", http=httpAuth)
    SAMPLE_SPREADSHEET_ID = "SAMPLE_SPREADSHEET_ID"
    sheet = service.spreadsheets()
    values = []
    user_row = []
    key_mas = {
        "username": "Юзернейм",
        "fio": "ФИО",
        "company": "Компания",
        "site": "Сайт",
        "education": "Образование",
        "branch": "Направление",
        "product": "Основные продукты",
        "country": "Страны экспорта",
        "plans": "Приоритетные направления",
        "clients": "Клиенты",
        "money": "Оборот",
        "clientscat": "Категория клиентов",
        "birthday": "День рождения",
        "email": "E-mail",
        "phone": "Телефон",
        "live": "Город проживания",
        "meetup": "Готовность встреч в Москве",
    }
    for name in key_mas:
        user_row.append(key_mas[name])
    values.append(user_row)
    for user in db.select_column("users"):
        user_row = []
        for name in key_mas:
            user_row.append(str(user[name]))
        values.append(user_row)

    body = {"values": values}
    print(values)
    nums = len(values) + 1
    range_is = "Пользователи!A1:Q%s" % nums
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=range_is,
            valueInputOption="RAW",
            body=body,
        )
        .execute()
    )
    return 0


def update_meetups_from_table():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "kkey.json", ["https://www.googleapis.com/auth/spreadsheets"]
    )
    httpAuth = credentials.authorize(httplib2.Http())
    service = googleapiclient.discovery.build("sheets", "v4", http=httpAuth)
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    SAMPLE_SPREADSHEET_ID = "SAMPLE_SPREADSHEET_ID"
    flag = True
    counter = 0
    sheet = service.spreadsheets()
    SAMPLE_RANGE_NAME = "События!A2:F100"
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
        .execute()
    )
    values = result.get("values", [])
    values2 = []
    for meetup in values:
        num = meetup[0]
        check = db.select("meetups", "id", num)
        l = meetup[4]
        print(l)
        meetup[4] = check_date(l)
        print(meetup)
        if len(check) == 0:
            db.insert(
                "meetups",
                [
                    "id",
                    "name",
                    "description",
                    "users",
                    "date",
                    "time",
                    "link",
                    "users2",
                ],
                meetup,
            )
        else:
            db.update(
                "meetups",
                ["name", "description", "users", "date", "time", "link", "users2"],
                meetup[1:],
                num,
            )
            values2.append([check[0]["users2"]])
    range_is = "События!H2:P%s" % str(len(values2) + 1)
    print(values2)
    body = {"values": values2}
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=range_is,
            valueInputOption="RAW",
            body=body,
        )
        .execute()
    )
    return True


def meetup_list(meetups, meetup_num):
    project_id = meetups[meetup_num]["id"]
    count_of_projects = len(meetups)
    markup2 = telebot.types.InlineKeyboardMarkup()
    markup2.row_width = 1
    buttons = []
    if meetup_num > 0:
        buttons.append(
            telebot.types.InlineKeyboardButton(
                "⬅️", callback_data="calendar_" + str(meetup_num - 1)
            )
        )
    if meetup_num < (count_of_projects - 1):
        buttons.append(
            telebot.types.InlineKeyboardButton(
                "➡️", callback_data="calendar_" + str(meetup_num + 1)
            )
        )
    markup2.row(*buttons)
    markup2.row(
        telebot.types.InlineKeyboardButton(
            "Хочу пойти", callback_data="addmeetup_%s" % project_id
        )
    )
    markup2.row(
        telebot.types.InlineKeyboardButton("Вернуться в меню", callback_data="menu")
    )
    return markup2


def meetup_text(meetup):
    tex = "⚡️ <b>%s</b>" % meetup["name"]
    tex += "\n🗓 <b>Когда:</b> %s" % beautiful_time(meetup["date"])
    tex += "\n⏰ <b>Начало:</b> %s" % meetup["time"]
    if meetup["link"]:
        tex += "\n<b>Ссылка:</b> %s" % meetup["link"]

    tex += "\n%s" % meetup["description"]
    return tex


def update_happy_birthday(user_id, value):
    db.update("users", ["happy_birthday"], [value], user_id)


def reset_happy_birthday():
    all_users = db.select_all("users")
    for user in all_users:
        update_happy_birthday(user["id"], "Need")


def happy_birthday(bot):
    now = datetime.datetime.now()
    group_id = admins_group_id
    us_data = db.select_column("users")
    for us in us_data:
        a = us["birthday"]
        if (
            a
            and a.day == now.day
            and a.month == now.month
            and us["happy_birthday"] == "Need"
            and us["permission"] > 0
        ):
            bot.send_message(
                chat_id=group_id,
                parse_mode="HTML",
                text="<a href = 'tg://user?id=%s' >%s</a> поздравляем Вас с Днем Рождения! Успехов и развития в бизнесе!."
                % (us["id"], us["fio"]),
            )
            update_happy_birthday(us["id"], "Done")
    return 0


def make_anons(bot):
    now = datetime.datetime.now()
    group_id = admins_group_id
    t = now.strftime("%Y-%m-%d")
    meetups_today = db.select("meetups", "date", t)

    for meetup in meetups_today:
        meetup_date_time = datetime.datetime.strptime(
            f"{meetup['date']} {meetup['time']}", "%Y-%m-%d %H:%M:%S"
        )
        if (
            now >= meetup_date_time - datetime.timedelta(days=1)
            and meetup["reminder"] == "Need"
        ):
            bot.send_message(
                chat_id=group_id,
                parse_mode="HTML",
                text="Напоминаем, что завтра у нас состоится мероприятие %s"
                % meetup_text(meetup),
            )
            db.update("meetups", ["reminder"], ["Done"], meetup["id"])

    return 0


def beautiful_time(strx):
    months = [
        "Января",
        "Января",
        "Февраля",
        "Марта",
        "Апреля",
        "Мая",
        "Июня",
        "Июля",
        "Августа",
        "Сентября",
        "Октября",
        "Ноября",
        "Декабря",
    ]
    return "%s %s %s" % (strx.day, months[strx.month], strx.year)


def choose_some(array_of_values, user_value, attribute, button_name, width=2, page=0):
    button_name = button_name + attribute.db_name
    markup2 = telebot.types.InlineKeyboardMarkup()
    markup2.row_width = width
    list_len = len(array_of_values)
    for row in range(5):
        buttons = []
        for column in range(width):
            ll = page * width * 5 + row * 2 + column
            if ll < list_len:
                rs = str(array_of_values[ll]["name"])
                if rs in user_value:
                    rs = "✔️" + rs
                buttons.append(
                    telebot.types.InlineKeyboardButton(
                        rs, callback_data=button_name + "_" + str(ll) + "_" + str(page)
                    )
                )
        markup2.row(*buttons)
    buttons = []
    if page > 0:
        buttons.append(
            telebot.types.InlineKeyboardButton(
                "⬅️", callback_data=button_name + "_page_" + str(page - 1)
            )
        )
    if page < (list_len // (width * 5)):
        buttons.append(
            telebot.types.InlineKeyboardButton(
                "➡️", callback_data=button_name + "_page_" + str(page + 1)
            )
        )
    markup2.row(*buttons)
    buttons = []
    buttons.append(
        telebot.types.InlineKeyboardButton(
            "Сохранить👌", callback_data="%s_save" % button_name
        )
    )
    markup2.row(*buttons)

    return markup2


def choose_one(array_of_values, attribute, button_name, width=2, page=0):
    button_name = button_name + attribute.db_name
    markup2 = telebot.types.InlineKeyboardMarkup()
    markup2.row_width = width
    list_len = len(array_of_values)
    for row in range(5):
        buttons = []
        for column in range(width):
            ll = page * width * 5 + row * 2 + column
            if ll < list_len:
                rs = str(array_of_values[ll])
                buttons.append(
                    telebot.types.InlineKeyboardButton(
                        rs, callback_data=button_name + "_" + str(ll)
                    )
                )
        markup2.row(*buttons)
    buttons = []
    if page > 0:
        buttons.append(
            telebot.types.InlineKeyboardButton(
                "⬅️", callback_data=button_name + "_page_" + str(page - 1)
            )
        )
    if page < (list_len // (width * 5)):
        buttons.append(
            telebot.types.InlineKeyboardButton(
                "➡️", callback_data=button_name + "_page_" + str(page + 1)
            )
        )
    markup2.row(*buttons)
    return markup2


def google_get():
    CREDENTIALS_FILE = "kkey.json"
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE, ["https://www.googleapis.com/auth/spreadsheets"]
    )
    httpAuth = credentials.authorize(httplib2.Http())
    service = googleapiclient.discovery.build("sheets", "v4", http=httpAuth)
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    SAMPLE_SPREADSHEET_ID = "SAMPLE_SPREADSHEET_ID"
    sheet = service.spreadsheets()
    SAMPLE_RANGE_NAME = "СУЩЕСТВУЮЩИЕ ПОЛЬЗОВАТЕЛИ!A2:R100"
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
        .execute()
    )
    values = result.get("values", [])
    counter = 1
    for row in values:
        counter += 1
        attributes = []
        attributes.append("user_id")
        attributes.append("username")
        while len(row) < 17:
            row.append("")
        attributes.extend(profile_config.get_attributes_db())
        check = db.select("was", "user_id", row[0])
        if len(check) > 0:
            print("уже есть")
            print(check)
            continue
        print(counter)
        try:
            db.insert("was", attributes, row)
        except:
            print("не добавил")
            print(row)
            continue


def choosefield(array_of_values):
    page = 0
    button_name = "editfield"
    width = 2
    markup2 = telebot.types.InlineKeyboardMarkup()
    markup2.row_width = width
    list_len = len(array_of_values.keys())
    for row in range(7):
        buttons = []
        for column in range(width):
            ll = page * width * 6 + row * 2 + column
            if ll < list_len:
                rs = list(array_of_values.keys())[ll]
                buttons.append(
                    telebot.types.InlineKeyboardButton(
                        rs, callback_data=button_name + "_" + array_of_values[rs]
                    )
                )
        markup2.row(*buttons)
    buttons = []

    markup2.row(*buttons)
    markup2.add(
        telebot.types.InlineKeyboardButton("Вернуться в меню", callback_data="menu")
    )
    return markup2


def send_coffee_offer(user1, user2):
    text_for_user1 = make_coffee_profile(user2)
    try:
        bot.send_message(chat_id=user1["id"], parse_mode="HTML", text=text_for_user1)
    except telebot.apihelper.ApiException as e:
        if "Chat not found" in str(e):
            print(f"User1 ({user1['id']}) не в чате с ботом.")
        else:
            print(f"Ошибка при отправке сообщения пользователю {user1['id']}: {e}")

    text_for_user2 = make_coffee_profile(user1)
    try:
        bot.send_message(chat_id=user2["id"], parse_mode="HTML", text=text_for_user2)
    except telebot.apihelper.ApiException as e:
        if "Chat not found" in str(e):
            print(f"User2 ({user2['id']}) не в чате с ботом.")
        else:
            print(f"Ошибка при отправке сообщения пользователю {user2['id']}: {e}")


def transform_ratings_data(ratings_data, meetups_data, users_data):
    transformed_data = []
    for rating in ratings_data:
        meet_id = rating["meet_id"]
        user_id = rating["user_id"]
        transformed_data.append(
            {
                "Id": rating["id"],
                "Событие": meetups_data.get(meet_id, ""),
                "Участник": users_data.get(user_id, ""),
                "Оценка": rating["rate"],
            }
        )
    return transformed_data


want_coffee = [5585191692, 417884911]


def find_random_coffee_partner():
    want_coffee = db.select("users", "random", 1)
    want_coffee_ids = db.select_ids("users", "random", 1)
    users_with_coffee = set()
    random.shuffle(want_coffee)
    for user in want_coffee:
        if user["id"] in users_with_coffee:
            continue
        if len(users_with_coffee) + 1 == len(want_coffee):
            str_coffee_partners = user["coffee_partners"]
            set_coffee_partners = (
                set(str_coffee_partners.split(","))
                if str_coffee_partners is not None
                else set()
            )
            not_met_yet = set(want_coffee_ids).difference(set_coffee_partners)
            not_met_yet.remove(user["id"])
            coffee_partner = random.choice(list(not_met_yet))
            coffee_partner_obj = db.select("users", "id", coffee_partner)[0]
            update_coffee_partners(user, coffee_partner_obj)
            send_coffee_offer(user, coffee_partner_obj)
            break

        str_coffee_partners = user["coffee_partners"]
        set_coffee_partners = (
            set(str_coffee_partners.split(","))
            if str_coffee_partners is not None
            else set()
        )
        not_met_yet = set(want_coffee_ids).difference(set_coffee_partners)
        not_met_yet.remove(user["id"])
        available_users = not_met_yet.difference(users_with_coffee)
        if available_users:
            coffee_partner = random.choice(list(available_users))
            users_with_coffee.add(user["id"])
            users_with_coffee.add(coffee_partner)
            coffee_partner_obj = db.select("users", "id", coffee_partner)[0]
            update_coffee_partners(user, coffee_partner_obj)
            send_coffee_offer(user, coffee_partner_obj)
        else:
            break


def update_coffee_partners(user1, user2):
    current_coffee_partners1 = str(user1["coffee_partners"] or "")
    current_coffee_partners2 = str(user2["coffee_partners"] or "")

    new_coffee_partners1 = current_coffee_partners1 + str(user2["id"]) + ", "
    new_coffee_partners2 = current_coffee_partners2 + str(user1["id"]) + ", "

    db.update_coffee(new_coffee_partners1, user1["id"])
    db.update_coffee(new_coffee_partners2, user2["id"])


@bot.message_handler(
    func=lambda message: True,
    chat_types=["group", "supergroup"],
    content_types=["new_chat_members"],
)
def new_chat_members(message):
    main_mes(message, bot)


@bot.message_handler(content_types=["contact"])
def handle_contact(contact):
    main_mes(contact, bot)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    main_mes(message, bot)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    call_mes(call, bot)


def run_bot():
    bot.polling(none_stop=True)


bot_thread = threading.Thread(target=run_bot)
bot_thread.start()


schedule.every().day.at("13:00").do(make_anons, bot=bot)
schedule.every().day.at("18:00").do(happy_birthday, bot=bot)
schedule.every(7).days.at("19:00").do(find_random_coffee_partner)


while True:
    now = datetime.datetime.now()
    if now.month == 1 and now.day == 1 and now.hour == 0 and now.minute == 0:
        reset_happy_birthday()
    schedule.run_pending()
    time.sleep(1)
