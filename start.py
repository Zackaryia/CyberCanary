import multiprocessing.process

import psycopg2.sql
import app
import intake
import ai_filter_daemon
import threat_filter_daemon
import time
import multiprocessing
import psycopg2
import sys

print("Make sure to set up reverse ssh")
DB_PARAMS = {
    "dbname": "cybercanary",
    "user": "zack_db",
    "password": "test",
    "host": "127.0.0.1",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_PARAMS)

print("Adds new db stuff")
with open("schema.sql", "r") as f:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.executemany(f.read(), ())
    cur.close()
    conn.commit()
    conn.close()

time.sleep(2)

if len(sys.argv) > 1:
    print("RESETTING")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.executemany(
        """SELECT
            pg_terminate_backend(pid) 
        FROM 
            pg_stat_activity 
        WHERE 
            -- don't kill my own connection!
            pid <> pg_backend_pid()
            -- don't kill the connections to other databases
            AND datname = 'cybercanary';
            
        DROP TABLE posts;
        DROP TABLE projects_impacted;
        DROP TABLE queue;
        DROP TABLE threats;""",
        ()
    )
    cur.close()
    conn.commit()
    conn.close()


multiprocessing.Process(target=app.main).start()
time.sleep(2)
multiprocessing.Process(target=intake.main).start()
time.sleep(2)
multiprocessing.Process(target=ai_filter_daemon.main).start()
time.sleep(2)
multiprocessing.Process(target=threat_filter_daemon.main).start()
