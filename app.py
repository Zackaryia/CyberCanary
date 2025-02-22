import sqlite3
from flask import Flask, render_template
from werkzeug.exceptions import abort

app = Flask(__name__)

@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/login/')
def logIn():
    return 'This is a placeholder for the sign in/make new account screen'

@app.route('/projects/')
def projects():
    account_id: int = get_account_id()
    conn = get_db_connection()
    projects = conn.execute('SELECT * FROM projects WHERE accountID = ?',(account_id,)).fetchall()
    conn.close()
    return render_template('projects.html', projects=projects)

@app.route('/<int:project_id>')
def project(project_id):
    project = get_project(project_id)
    return render_template('project.html', project=project)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_project(project_id):
    conn = get_db_connection()
    project = conn.execute('SELECT * FROM projects WHERE id = ?',(project_id,)).fetchone()
    conn.close()
    if project is None:
        abort(404)
    return project

def get_account_id():
    #placeholder until I figure out how to fetch account id from login
    return 1