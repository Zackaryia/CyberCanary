import sqlite3

connection = sqlite3.connect('database.db')


with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO posts (title, content) VALUES (?, ?)",
            ('New firewall attack method', 'hacker has found something new about firewalls blah blah ....')
            )

cur.execute("INSERT INTO projects (title, accountID, stack) VALUES (?, ?, ?)",
            ('Google Drive', 1, 'Something secure')
            )

cur.execute("INSERT INTO projects (title, accountID, stack) VALUES (?, ?, ?)",
            ('Gmail', 1, 'Something also secure')
            )

connection.commit()
connection.close()