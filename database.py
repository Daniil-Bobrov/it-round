import sqlite3
import datetime


def create_db():
    """Вспомогательная функция для создания таблиц БД """
    db = connect_db()
    with app.open_resource('sql_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


class DataBase:
    def __init__(self, database=None):
        if database is None:
            database = sqlite3.connect("database.db")
            database.row_factory = sqlite3.Row
        self.__db = database
        self.__cur = database.cursor()

    def create_user(self):
        try:
            self.__cur.execute("INSERT INTO users VALUES (NULL, ?)", ("",))
            self.__db.commit()
            self.__cur.execute(
                f"""SELECT MAX(id) FROM users"""
            )
            return self.__cur.fetchone()[0]
        except Exception as e:
            print('Ошибка добавления в БД', e)
            return False

    def add_deduction(self, deduction, deduction_type, user_id, *fields):
        try:
            self.__cur.execute("INSERT INTO deductions VALUES (NULL, ?, ?, ?, ?)",
                               (",".join(fields), str(deduction), str(deduction_type),
                                str(datetime.datetime.now())))
            self.__db.commit()
            # создали расчет
            self.__cur.execute(
                f"""SELECT MAX(id) FROM deductions"""
            )
            deduction_id = str(self.__cur.fetchall()[0][0])
            # взяли id этого расчета
            self.__cur.execute(
                f"""SELECT * FROM users WHERE id='{int(user_id)}'"""
            )
            # нашли нашего user
            user = self.__cur.fetchone()
            deductions = [deduction_id for deduction_id in user["deductions"].split(",") if deduction_id != ""]
            deductions.append(deduction_id)
            deductions = ",".join(deductions)
            self.__cur.execute(f"UPDATE users SET deductions='{deductions}' WHERE id={user_id}")
            self.__db.commit()
            # добавили пользователю расчет
            return deduction_id
        except Exception as e:
            print('Ошибка добавления в БД', e)
            return False

    def get_deductions(self, user_id):
        try:
            self.__cur.execute(
                f"""SELECT deductions FROM users WHERE id='{user_id}'"""
            )
            deductions = self.__cur.fetchall()[0][0].split(",")
            return [Deduction(str(deduction_id)) for deduction_id in deductions]
        except Exception as e:
            print('Ошибка чтения в БД', e)
            return False

    def f(self):
        self.__cur.execute(
            f"""ALTER TABLE deductions ADD COLUMN type"""
        )


class Deduction:
    def __init__(self, deduction_id, database=None):
        if database is None:
            database = sqlite3.connect("database.db")
            database.row_factory = sqlite3.Row
        self.__db = database
        self.__cur = database.cursor()

        self.__cur.execute(
            f"""SELECT * FROM deductions WHERE id='{deduction_id}'"""
        )
        deduction = self.__cur.fetchone()
        self.id = deduction["id"]
        self.type = deduction["type"]
        self.time = deduction["time"]
        self.fields = deduction["fields"].split(",")
        self.deduction = deduction["deduction"]


if __name__ == "__main__":
    # from app import app, connect_db
    #
    # create_db()
    DataBase().create_user()
    pass
