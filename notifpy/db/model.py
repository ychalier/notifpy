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

    def list(self, conditions=[], search=[], order=None, limit=None, offset=None):
        sql = "SELECT * FROM {table}".format(table=self.table)
        if len(conditions) + len(search) > 0:
            sql += " WHERE "
        if len(conditions) > 0:
            sql += " AND ".join([c[0]+"=?" for c in conditions])
            if len(search) > 0:
                sql += " AND "
        if len(search) > 0:
            sql += " AND ".join([c[0]+" LIKE ?" for c in search])
        if order is not None:
            sql += " ORDER BY {order}".format(order=order)
        if limit is not None:
            sql += " LIMIT {limit}".format(limit=limit)
        if offset is not None:
            sql += " OFFSET {offset}".format(offset=offset)
        rows = self.db.execute(sql, [c[1] for c in conditions + search])
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
