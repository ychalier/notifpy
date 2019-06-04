import sqlite3


class Database:

    INIT_SCRIPT_FILE = "notifpy/db/init.sql"

    def __init__(self, path):
        self.path = path
        self.connection = sqlite3.connect(path)
        cursor = self.connection.cursor()
        with open(Database.INIT_SCRIPT_FILE) as file:
            for statement in file.read().split(";"):
                cursor.execute(statement)
        self.connection.commit()

    def execute(self, query, values=tuple()):
        cursor = self.connection.cursor()
        cursor.execute(query, values)
        self.connection.commit()
        return cursor

    def close(self):
        self.connection.close()
