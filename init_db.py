import sqlite3

connection = sqlite3.connect('database.db')


with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO posts (title, content) VALUES (?, ?)",
            ('New firewall attack method', 'think this is a new way to attack a firewall? ....')
            )
cur.execute("INSERT INTO posts (title, content) VALUES (?, ?)",
            ('DDoS early detection system', 'just created a faster system to detect DDoS threats....')
            )
cur.execute("INSERT INTO posts (title, content) VALUES (?, ?)",
            ('SQL injection large scale', 'discovered an SQL attack on my website that I have not seen before....')
            )
cur.execute("INSERT INTO posts (title, content) VALUES (?, ?)",
            ('Cryptojacking', 'dude I hate crypto bros....')
            )
connection.commit()
connection.close()