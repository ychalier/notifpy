class Model:

    fields = None
    table = None

    def __init__(self, db):
        self.db = db

    def parse(self, row):
        return {
            field: row[i]
            for i, field in enumerate(self.fields)
        }

    def list(self, conditions=[], order=None):
        order_string = ""
        if order is not None:
            order_string = " ORDER BY " + order
        if len(conditions) == 0:
            rows = self.db.execute(
                "SELECT * FROM {table}".format(table=self.table) + order_string,
            ).fetchall()
        else:
            rows = self.db.execute(
                "SELECT * FROM {table} WHERE {ands}".format(
                    table=self.table,
                    ands=" AND ".join([c[0]+"=?" for c in conditions])
                    ) + order_string,
                [c[1] for c in conditions]
            ).fetchall()
        return [self.parse(row) for row in rows]

    def create(self, *values):
        self.db.execute(
            "INSERT INTO {table} ({fields}) VALUES ({placeholders})".format(
                table=self.table,
                fields=", ".join(self.fields),
                placeholders=", ".join(["?" for f in self.fields])
            ),
            values
        )

    def read(self, key):
        return self.parse(self.db.execute(
            "SELECT * FROM {table} WHERE id=?".format(table=self.table),
            (key,)
        ).fetchone())

    def update(self, key, data):
        self.db.execute(
            "UPDATE {table} SET {setters} WHERE id=?".format(
                table=self.table,
                setters=", ".join([d+"=?" for d in data]),
            ),
            list(data.values()) + [key]
        )

    def delete(self, key):
        self.db.execute(
            "DELETE FROM {table} WHERE id=?".format(table=self.table),
            (key,)
        )

    def exists(self, key):
        for item in self.list():
            if str(item["id"]) == str(key):
                return True
        return False
