import pymysql
import pymysql.cursors


def select(table, where, what, order=""):
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    query = "SELECT * FROM " + str(table) + " WHERE `" + str(where) + "` = %s"
    if order != "":
        query += " ORDER BY `%s` ASC" % (order)
    print(query)
    cur = connection.cursor()
    cur.execute(query, (what))
    rows = cur.fetchall()
    cur.close()
    return rows


def select_like(table, where, what):
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    query = "SELECT * FROM `%s` WHERE `%s` LIKE" % (table, where) + "'%" + what + "%' "
    print(query)
    cur = connection.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    return rows


def select_some(table, where, what):
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    mystr = ""
    for i in range(len(where)):
        if i != 0:
            mystr += " AND "
        mystr += "`" + where[i] + "` = '" + str(what[i]) + "'"

    query = "SELECT * FROM " + str(table) + " WHERE " + mystr
    print(query)
    cur = connection.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    return rows


def select_ids(table, where, what, order=""):
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    query = "SELECT id FROM " + str(table) + " WHERE `" + str(where) + "` = %s"
    if order != "":
        query += " ORDER BY `%s` ASC" % (order)
    print(query)
    cur = connection.cursor()
    cur.execute(query, (what,))
    rows = [row["id"] for row in cur.fetchall()]
    cur.close()
    return rows


def get_ratings_data():
    db_connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT id, meet_id, user_id, rate FROM ratings")
        return cursor.fetchall()


def get_meetups_data():
    db_connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM meetups")
        return {row["id"]: row["name"] for row in cursor.fetchall()}


def get_users_data():
    db_connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT id, fio FROM users")
        return {row["id"]: row["fio"] for row in cursor.fetchall()}


def select_users_with_permission_1_or_2():
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

    query = "SELECT * FROM users WHERE permission IN (%s, %s)"
    values = (1, 2)

    cur = connection.cursor()
    cur.execute(query, values)
    rows = cur.fetchall()
    cur.close()

    return rows


def get_newsletter_message_for_user(user_id):
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

    query = "SELECT newsletter_message FROM users WHERE id = %s"

    cur = connection.cursor()
    cur.execute(query, (user_id,))
    result = cur.fetchone()
    cur.close()

    if result:
        return result["newsletter_message"]
    else:
        return None


def insert(table, list1, list2):
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    mystr = " ("
    mystr2 = " VALUES ("
    for i in range(len(list1)):
        if i != 0:
            mystr += ", "
            mystr2 += ", "
        mystr += "`"
        mystr += str(list1[i])
        mystr += "`"
        if (i + 1) > len(list2) or str(list2[i]) == "" or str(list2[i]) == "None":
            mystr2 += "''"
        else:
            mystr2 += "'"
            mystr2 += str(list2[i])
            mystr2 += "'"

    mystr += ")"
    mystr2 += ")"
    query = "INSERT INTO " + table + mystr + mystr2
    print(query)
    cur = connection.cursor()
    cur.execute(query)
    connection.commit()
    a = cur.lastrowid
    cur.close()
    return a


def select_column(table, list1=None, where="", what=""):
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    mystr = ""
    if list1 is None:
        mystr = "*"
    else:
        for i in range(len(list1)):
            if i != 0:
                mystr += ", "
            mystr += "`" + list1[i] + "`"
    if where == "":
        query = "SELECT " + mystr + " FROM " + table
    else:
        query = (
            "SELECT "
            + mystr
            + " FROM "
            + table
            + " WHERE `"
            + str(where)
            + "`= "
            + "'"
            + str(what)
            + "'"
        )
    print(query)
    cur = connection.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    return rows


def delete(table, where, what):
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    query = "DELETE FROM " + table + " WHERE `" + where + "`= '" + str(what) + "'"
    print(query)
    cur = connection.cursor()
    cur.execute(query)
    connection.commit()
    cur.close()
    return True


def update(table, list1, list2, id_is, keyword="id"):
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    mystr = ""
    for i in range(len(list1)):
        if i != 0:
            mystr += ", "
        if (i + 1) > len(list2):
            list2.append("")
        mystr += "`" + str(list1[i]) + "` = '" + str(list2[i]) + "'"

    query = (
        "UPDATE "
        + table
        + " SET "
        + mystr
        + " WHERE `"
        + keyword
        + "` = '"
        + str(id_is)
        + "'"
    )
    print(query)
    cur = connection.cursor()
    cur.execute(query)
    connection.commit()
    cur.close()
    return True


def update_coffee(what, user_id):
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    query = "UPDATE users SET coffee_partners = '{}' WHERE id = {}".format(
        what, user_id
    )
    print(query)
    cur = connection.cursor()
    cur.execute(query)
    connection.commit()
    cur.close()


def clear_table(table):
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    query = "TRUNCATE TABLE `%s` " % table
    print(query)
    cur = connection.cursor()
    cur.execute(query)
    connection.commit()
    cur.close()
    return True


def get_coffee_partners_dict():
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

    query = "SELECT id, coffee_partners FROM users"

    cur = connection.cursor()
    cur.execute(query)

    coffee_partners_dict = {}

    for row in cur.fetchall():
        user_id = row["id"]
        coffee_partners_str = row["coffee_partners"]

        if coffee_partners_str is not None:
            coffee_partners_set = set(map(int, coffee_partners_str.split(",")))
            coffee_partners_dict[user_id] = coffee_partners_set
        else:
            coffee_partners_dict[user_id] = set()

    cur.close()
    connection.close()

    return coffee_partners_dict


def free_sql(query):
    connection = pymysql.connect(
        host="host",
        user="user",
        password="password",
        db="db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = connection.cursor()
    a = cur.execute(query)
    cur.close()
    return a
