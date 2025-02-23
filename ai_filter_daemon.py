import json
import multiprocessing
import pathlib
import psycopg2
import psycopg2.extras
import time
import os
from base64 import urlsafe_b64decode
import run_llama

from helper import json_serial


# Database connection
DB_PARAMS = {
    "dbname": "cybercanary",
    "user": "zack_db",
    "password": "test",
    "host": "127.0.0.1",
    "port": "5432"
}

script_dir = os.path.dirname(os.path.abspath(__file__))


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
    
    post['html_snapshot'] = json.loads(post['html_snapshot'])
    linked_to_files = {}
    for file in post['html_snapshot']:
        if file is not None and file.endswith(".md"):
            filename = file.split("/")[1]
            file_url = urlsafe_b64decode(filename.split(".")[0]).decode()
            
            with open(os.path.join(script_dir, file), "r") as f:
                linked_to_files[file_url] = f.read(3000) # limit context size
    
    
    threat_description = f"""
    The following is a {post['source']} sourced intellegence report, it could be a user's post, a write up, an article, an RSS feed entry, or anything.

    {json.dumps(post, default=json_serial)}

    Below are any urls accessed that had scrapeable content, Note: Some may not have relevant information or may not have the correct information scraped propperly.
    Its in the format of a dictionary, with the key being the URL accessed, and the value being the retrieved information cleaned up into a .md like format.

    {json.dumps(linked_to_files, default=json_serial)}
    """

    analysis = run_llama.ai_threat_analysis(threat_description)

    update_query = """
        UPDATE posts
        SET is_threat_reasoning = %s,
            is_threat = %s,
            description = %s,
            threat_title = %s
        WHERE uid = %s;
    """

    # Execute update query
    cursor.execute(update_query, (
        analysis["analysis"], 
        analysis["isThreat"], 
        analysis["description"], 
        analysis["title"], 
        task_data
    ))

    if analysis["isThreat"]:
        cursor.execute("INSERT INTO queue(data, task) VALUES (%s, %s)", (post['id'], "ai-threat-project-relation"))

    conn.commit()

    cursor.close()
    conn.close()


    print(f"Finished processing AI filter task (ID: {task_id}): {task_data}")
    mark_task_as_completed(task_id)

MAX_CONCURRENT_TASKS = 12  # Limit concurrent analyses
semaphore = multiprocessing.Semaphore(MAX_CONCURRENT_TASKS)

def process_task_with_semaphore(task_id, data):
    """Wrapper function to acquire semaphore before processing the task."""
    with semaphore:  # Limits concurrent executions
        process_ai_filter_task(task_id, data)  # Run task

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
            for task_id, data in tasks:
                mark_task_as_processing(task_id)  # Mark as processing before starting
                p = multiprocessing.Process(target=process_task_with_semaphore, args=(task_id, data))
                p.start()

        else:
            time.sleep(5)  # Wait before checking again

def main():
    print(f"Starting threat filter.")
    process_queue = multiprocessing.Process(target=process_queue_tasks)
    process_queue.start()
    print("AI filter task processor started.")
    process_queue.join()

if __name__ == "__main__":
    main()