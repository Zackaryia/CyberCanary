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

def process_task_project_relation(task_id, post_id):
    """Dummy function to simulate AI filtering. Replace with your actual AI processing logic."""
    print(f"process_task_project_relation (ID: {task_id}): post_id {post_id}")

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("SELECT * FROM posts WHERE id = %s;", (post_id,))
    post = cursor.fetchone()

    cursor.execute("SELECT * FROM projects;")
    projects = cursor.fetchall()

    for project in projects:
        analysis = run_llama.ai_threat_project_relation(project, post)

        update_query = """
            INSERT INTO projects_impacted(project_id, threat_id, impacted, does_impact_analysis, description_of_relation) VALUES (%s, %s, %s, %s, %s)
        """

        # Execute update query
        cursor.execute(update_query, (
            project['id'],
            post_id,
            analysis["threat_impacts_project"], 
            analysis["analysis"], 
            analysis["description"], 
        ))

    conn.commit()

    cursor.close()
    conn.close()

    mark_task_as_completed(task_id)

MAX_CONCURRENT_TASKS = 12  # Limit concurrent analyses
semaphore = multiprocessing.Semaphore(MAX_CONCURRENT_TASKS)

def process_task_with_semaphore(task_id, data):
    """Wrapper function to acquire semaphore before processing the task."""
    with semaphore:  # Limits concurrent executions
        process_task_project_relation(task_id, data)  # Run task

def process_queue_tasks():
    """Continuously checks for and processes pending AI filter tasks using a process pool."""
    while True:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, data FROM queue WHERE task = 'ai-threat-project-relation' AND status = 'pending' LIMIT 10")
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
    print(f"Using processes.")
    process_queue = multiprocessing.Process(target=process_queue_tasks)
    process_queue.start()
    print("AI filter task processor started.")
    process_queue.join()

if __name__ == "__main__":
    main()