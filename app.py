import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, url_for, flash, redirect, session, jsonify
from werkzeug.exceptions import abort
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'password'
user = None

DB_PARAMS = {
    "dbname": "cybercanary",
    "user": "zack_db",
    "password": "test",
    "host": "127.0.0.1",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_PARAMS)

def get_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()
    cursor.close()
    conn.close()
    if project is None:
        abort(404)
    return project

@app.route('/posts')
def get_posts ():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT * FROM posts ORDER BY id DESC LIMIT 20;')
    posts = cursor.fetchall()
    posts_content = []
    for post in posts:
        temp = json.loads(post['content'])
        temp['source'] = post['source']
        posts_content.append(temp)
    cursor.close()
    conn.close()
    return jsonify(posts_content)

@app.route('/<int:project_id>/threats')
def get_threats (project_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT posts.threat_title, posts.description, projects_impacted.description_of_relation FROM projects_impacted JOIN posts ON projects_impacted.post_id = posts.id WHERE projects_impacted.project_id = %s;', project_id)
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(posts)

@app.route('/')
def index():
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        userinfo = cursor.fetchone()
        cursor.close()
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        if cursor.fetchone() is None:
            cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
            conn.commit()
        else:
            flash('Username is taken!')
            return render_template('register.html')
        cursor.close()
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
    if 'username' in session and 'user_id' in session:
        account_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM projects WHERE accountID = %s', (account_id,))
        projects = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('projects.html', projects=projects, username=session['username'], user=user)
    return redirect(url_for('login'))

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        stack = request.form['stack']
        if not title:
            flash('Project title is required!')
        else:
            account_id = session['user_id']
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO projects (title, stack, accountID) VALUES (%s, %s, %s)', (title, stack, account_id))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('projects'))
    return render_template('create.html', user=user)

@app.route('/<int:project_id>')
def project(project_id):
    project = get_project(project_id)
    return render_template('project.html', project=project, user=user)

@app.route('/<int:project_id>/edit', methods=['GET', 'POST'])
def edit(project_id):
    project = get_project(project_id)
    if request.method == 'POST':
        title = request.form['title']
        stack = request.form['stack']
        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE projects SET title = %s, stack = %s WHERE id = %s', (title, stack, project_id))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('projects'))
    return render_template('edit.html', project=project, user=user)

def main():
    app.run("127.0.0.1", port=5002, debug=True)

if __name__ == "__main__":
    main()