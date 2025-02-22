import json
import multiprocessing
import psycopg2
import psycopg2.extras
import time
from base64 import urlsafe_b64decode

# Database connection
DB_PARAMS = {
    "dbname": "cybercanary",
    "user": "zack_db",
    "password": "test",
    "host": "127.0.0.1",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_PARAMS)

def mark_task_as_processing(task_id):
    """Marks a task as processing in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE queue SET status = 'processing' WHERE id = %s", (task_id,))
    conn.commit()
    cursor.close()
    conn.close()

def mark_task_as_completed(task_id):
    """Marks a task as completed in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE queue SET status = 'completed' WHERE id = %s", (task_id,))
    conn.commit()
    cursor.close()
    conn.close()

def process_ai_filter_task(task_id, task_data):
    """Dummy function to simulate AI filtering. Replace with your actual AI processing logic."""
    print(f"Processing AI filter task (ID: {task_id}): {task_data}")

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("SELECT * FROM posts WHERE uid = %s;", (task_data,))
    post = cursor.fetchone()
    
    linked_to_files = {}
    for file in post['html_snapshots']:
        if file.endswith(".md"):
            filename = file.split("/")[1]
            file_url = urlsafe_b64decode(filename.split(".")[0])
            with open(filename) as f:
                linked_to_files[file_url] = f.read()
    
    
    print(post, linked_to_files)
    cursor.close()
    conn.close()


    print(f"Finished processing AI filter task (ID: {task_id}): {task_data}")
    mark_task_as_completed(task_id)

def process_queue_tasks():
    """Continuously checks for and processes pending AI filter tasks using a process pool."""
    while True:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, data FROM queue WHERE task = 'ai-filter-for-threats' AND status = 'pending' LIMIT 10")
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        if tasks:
            for task in tasks:
                mark_task_as_processing(task[0]) #mark tasks as processing before starting
                multiprocessing.Process(target=process_ai_filter_task, args=task).start()
            # Use starmap to pass multiple arguments to the processing function

        else:
            time.sleep(5)  # Wait for 5 seconds before checking again

if __name__ == "__main__":
    print(f"Using processes.")
    process_queue = multiprocessing.Process(target=process_queue_tasks)
    process_queue.start()
    print("AI filter task processor started.")
    process_queue.join()