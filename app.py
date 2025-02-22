import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect, session
from werkzeug.exceptions import abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'password'

@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        user = conn.execute('SELECT * FROM User WHERE username = ?',(username,)).fetchone()
        conn.commit()
        conn.close()
        print(user, username, password)
        if user and user['password'] == password:
            session['username'] = user['username']
            session['user_id'] = user['id']
            return redirect(url_for('projects'))
        else:
            return 'Invalid username or password' #add page later to go back to login
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE username = ?',(username,))
        user = cursor.fetchone()
        print(user, username, password)
        if user is None:
            cursor.execute('INSERT INTO User (username, password) VALUES (?, ?)',(username, password))
        else:
            return 'Username is taken' #add a page later with button to go back
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/projects')
def projects():
    if 'username' and 'user_id' in session:
        account_id = session['user_id']
        conn = get_db_connection()
        projects = conn.execute('SELECT * FROM projects WHERE accountID = ?',(account_id,)).fetchall()
        conn.close()
        return render_template('projects.html', projects=projects, username=session['username'], accountID=session['user_id'])
    else:
        return redirect(url_for('login'))

@app.route('/<int:project_id>')
def project(project_id):
    project = get_project(project_id)
    return render_template('project.html', project=project)

@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        stack = request.form['stack']

        if not title:
            flash('Name of project is required!')
        else:
            account_id = session['user_id']
            conn = get_db_connection()
            conn.execute('INSERT INTO projects (title, stack, accountID) VALUES (?, ?, ?)',(title, stack, account_id))
            conn.commit()
            conn.close()
            return redirect(url_for('projects'))
    return render_template('create.html')

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    project = get_project(id)

    if request.method == 'POST':
        title = request.form['title']
        stack = request.form['stack']

        if not title:
            flash('Title is required!')
        else:
            account_id = session['user_id']
            conn = get_db_connection()
            conn.execute('UPDATE projects SET title = ?, stack = ? WHERE id = ?',(title, stack, account_id))
            conn.commit()
            conn.close()
            return redirect(url_for('projects'))

    return render_template('edit.html', project=project)

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
