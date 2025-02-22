import sqlite3

connection = sqlite3.connect('database.db')


with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO projects (title, accountID, stack) VALUES (?, ?, ?)",
            ('Manhattan Project', 1, 'Something secure')
            )

cur.execute("INSERT INTO projects (title, accountID, stack) VALUES (?, ?, ?)",
            ('Some Project', 1, 'Something less secure')
            )

connection.commit()
connection.close()