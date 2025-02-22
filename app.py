import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect, session
from werkzeug.exceptions import abort

#Task list:
#make stuff prettier (again)
#threat classes for each project, and threat class pages
#figure out how to relate threat classes to multiple projects "the sql way"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'password'
user = None

@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()
    return render_template('index.html', posts=posts, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        userinfo = conn.execute('SELECT * FROM User WHERE username = ?',(username,)).fetchone()
        conn.commit()
        conn.close()
        if userinfo and userinfo['password'] == password:
            session['username'] = userinfo['username']
            session['user_id'] = userinfo['id']
            global user
            user = userinfo['id']
            return redirect(url_for('projects'))
        else:
            flash('Invalid username or password')
            return render_template('login.html')
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
            flash('Username is taken!')
            return render_template('register.html')
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    global user
    user = None
    return redirect(url_for('login'))

@app.route('/projects')
def projects():
    if 'username' and 'user_id' in session:
        account_id = session['user_id']
        conn = get_db_connection()
        projects = conn.execute('SELECT * FROM projects WHERE accountID = ?',(account_id,)).fetchall()
        conn.close()
        return render_template('projects.html', projects=projects, username=session['username'], accountID=session['user_id'], user=user)
    else:
        return redirect(url_for('login'))

@app.route('/<int:project_id>')
def project(project_id):
    project = get_project(project_id)
    conn = get_db_connection()
    threatsTemp = conn.execute('SELECT * FROM threats').fetchall()
    threats = []
    for threat in threatsTemp:
        if relevant(project_id, threat):
            threats.append(threat)
    conn.close()
    return render_template('project.html', project=project, user=user, threats=threats)

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
    return render_template('create.html', user=user)

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

    return render_template('edit.html', project=project, user=user)

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

def relevant(project_id, threat):
    conn = get_db_connection()
    project = conn.execute('SELECT * FROM projects WHERE id = ?',(project_id,)).fetchone()
    if (project == None or threat == None):
        return False
    stack = project['stack']
    conn.close()
    return threat['title'].lower() in stack.lower()