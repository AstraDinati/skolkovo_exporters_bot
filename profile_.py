import telebot
import db


class Profile_attribute:
    def __init__(
        self,
        name,
        db_name="",
        value_type="string",
        filter="",
        array_of_values=[],
        ask_text="",
        added_text="",
    ):
        self.name = name
        self.value_type = value_type
        self.db_name = db_name
        if ask_text == "":
            self.ask_text = "Выбери значение поля %s" % name
        else:
            self.ask_text = ask_text
        self.inline = False

        if value_type == "string":
            self.content_type = "text"
        elif value_type == "photo":
            self.content_type = "photo"
        elif value_type == "document":
            self.content_type = "document"
        elif value_type == "contact":
            self.content_type = "contact"
        elif value_type == "chooseoneof":
            self.inline = True
            self.array_of_values = array_of_values
            self.added_text = added_text
        elif value_type == "choosesome":
            self.inline = True
            self.array_of_values = array_of_values
            self.added_text = added_text
        self.last = ""
        self.next = ""
        self.index = 0


class Configuration:
    DB_NAME = "test_exporters"

    def __init__(self):
        self.attributes = []

    def add_attribute(self, db, attr):
        check_column = db.free_sql(
            """ SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' 
    AND TABLE_NAME = 'users'
    AND COLUMN_NAME = '%s'
"""
            % (self.DB_NAME, attr.db_name)
        )
        if check_column == 0:
            db.free_sql(
                "ALTER TABLE `users` ADD `%s` VARCHAR(500) NOT NULL DEFAULT '' AFTER `id`"
                % attr.db_name
            )
        if len(self.attributes) > 0:
            m = self.attributes[-1]
            attr.last = m
            m.next = attr
            self.attributes[-1] = m
        attr.index = len(self.attributes) + 1
        self.attributes.append(attr)

    def get_attribute(self, name):
        for i in self.attributes:
            print("имя %s" % name)
            print(i)
            if i.db_name == name:
                return i
        raise Exception("нет такого класса")

    def print_config(self):
        for i in self.attributes:
            print(i)

    def get_attributes_db(self):
        m = []
        for i in self.attributes:
            m.append(i.db_name)
        return m

    def get_edited_attributes(self):
        m = dict()
        for i in self.attributes:
            if not i.db_name in ["phone", "birthday"]:
                m[i.name] = i.db_name
        return m


class Profile:
    def __init__(self, user_data, config):
        self.config = config
        self.user_data = user_data

    def get_profile_html(self):
        attr = self.config.attributes
        user_data = self.user_data
        tex = "<b>Профиль:</b> "
        if user_data["username"] != "":
            tex += "\n@" + user_data["username"]
        for field in attr:
            tex += "\n<b>%s:</b> %s" % (field.name, user_data[field.db_name])
        return tex

    def print_profile(self):
        for i in self.config:
            if self.user_data[i.db_name] is None:
                print("Параметр %s не задан" % self.user_data[i.name])
            else:
                print("Поле %s значение - %s" % (i.name, self.user_data[i.db_name]))


def make_config():
    Config = Configuration()
    a = Profile_attribute("ФИО", "fio", ask_text="Напишите свои ФИО")
    Config.add_attribute(db, a)

    a = Profile_attribute(
        "Компания",
        "company",
        ask_text="Укажите название Вашей компании. Можете перечислить несколько",
    )
    Config.add_attribute(db, a)

    a = Profile_attribute("Сайт", "site", ask_text="Напишите сайт своей компании")
    Config.add_attribute(db, a)

    a = Profile_attribute(
        "Образование",
        "education",
        ask_text="Зафиксировал! Скажите, какую образовательную программу Вы закончили в МШУ «Сколково»?",
    )
    Config.add_attribute(db, a)

    a = Profile_attribute(
        "Отрасль",
        "branch",
        ask_text="Укажите Вашу основную отраслевую направленность и дополнительные",
    )
    Config.add_attribute(db, a)

    a = Profile_attribute(
        "Ключевой продукт",
        "product",
        ask_text="Расскажите о Вашем ключевом экспортном продукте. Что именно Вы экспортируете?",
    )
    Config.add_attribute(db, a)

    exps = [
        "До 300 млн. руб.",
        "300-800 млн. руб.",
        "800 млн.- 1 млрд. Руб.",
        "Более 1 млрд. руб.",
    ]
    a = Profile_attribute(
        "Размер бизнеса",
        "money",
        array_of_values=exps,
        value_type="chooseoneof",
        ask_text="Укажите Размер Вашего бизнеса (отметьте диапазон)",
    )
    Config.add_attribute(db, a)

    exps = ["B2B", "B2C", "B2G"]
    a = Profile_attribute(
        "Тип клиентов",
        "clienttype",
        array_of_values=exps,
        value_type="chooseoneof",
        ask_text="Укажите основной тип Ваших клиентов.",
    )
    Config.add_attribute(db, a)

    a = Profile_attribute(
        "Клиенты",
        "clients",
        ask_text="Расскажите подробнее - какие ключевые клиенты Вашей компании на сегодняшний день.",
    )
    Config.add_attribute(db, a)

    a = Profile_attribute(
        "Страны",
        "country",
        ask_text="Расскажите, в какие страны Вы экспортируете свои продукты? С какими странами есть опыт работы. По каким странам, по Вашему мнению, Ваш опыт и налаженные связи могли бы быть полезны другим экспортерам",
    )
    Config.add_attribute(db, a)

    a = Profile_attribute(
        "Приоритет",
        "priority",
        ask_text="И последнее - какую страну/страны Вы считаете более приоритетными? Возможно куда Вы хотите эскпортировать в будущем.",
    )
    Config.add_attribute(db, a)

    a = Profile_attribute(
        "Дата рождения",
        "birthday",
        ask_text="Отлично! Теперь я задам пару вопросов для уточнения административной деятельности нашего комьюнити. Укажите дату своего рождения в формате дд.мм.гггг.",
    )
    Config.add_attribute(db, a)

    a = Profile_attribute(
        "E-mail",
        "email",
        ask_text="Укажите свою актуальную электронную почту для связи.",
    )
    Config.add_attribute(db, a)

    a = Profile_attribute(
        "Телефон",
        "phone",
        ask_text="Отправьте свой контактный телефон для связи по кнопке ниже.",
        value_type="contact",
    )
    Config.add_attribute(db, a)

    a = Profile_attribute(
        "Город проживания", "city", ask_text="Скажите, в каком городе Вы проживаете?"
    )
    Config.add_attribute(db, a)

    a = Profile_attribute(
        "Посещение встреч",
        "meetup",
        ask_text="Планируете посещать наши встречи в Москве?",
        value_type="chooseoneof",
        array_of_values=["Да", "нет"],
    )
    Config.add_attribute(db, a)

    return Config
