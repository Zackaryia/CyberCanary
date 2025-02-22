import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect, session
from werkzeug.exceptions import abort
import json
import multiprocessing
import multiprocessing.process
import time
import feedparser
import requests
import os
import psycopg2
from psycopg2 import sql
import psycopg2.extras
from jetstream import jetstream
from hashlib import sha256
import pypandoc
import mimetypes
import re
from bs4 import BeautifulSoup

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

def get_postgresdb_connection():
    conn = psycopg2.connect(**DB_PARAMS)
    return conn

def setup_database():
    conn = get_postgresdb_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            title TEXT,
            accountID INTEGER,
            stack TEXT
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()


def project_exists(cid):
    conn = get_postgresdb_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM projects WHERE id = %s", (cid,))
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists

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
        conn = get_postgresdb_connection()
        cursor = conn.cursor(row_factory=psycopg2.extras.RealDictCursor)
        projects = cursor.execute('SELECT * FROM projects WHERE accountID = %s',(account_id,)).fetchall()
        cursor.close()
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
            conn = get_postgresdb_connection()
            conn.execute('INSERT INTO projects (title, stack, accountID) VALUES (%s, %s, %s)',(title, stack, account_id))
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
            conn = get_postgresdb_connection()
            conn.execute('UPDATE projects SET title = %s, stack = %s WHERE id = %s',(title, stack, account_id))
            conn.commit()
            conn.close()
            return redirect(url_for('projects'))

    return render_template('edit.html', project=project, user=user)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_project(project_id):
    conn = get_postgresdb_connection()
    project = conn.execute('SELECT * FROM projects WHERE id = %s',(project_id,)).fetchone()
    conn.close()
    if project is None:
        abort(404)
    return project

def relevant(project_id, threat):
    conn = get_postgresdb_connection()
    cursor = conn.cursor(row_factory=psycopg2.extras.RealDictCursor)
    project = cursor.execute('SELECT * FROM projects WHERE id = %s',(project_id,)).fetchone()
    if (project == None or threat == None):
        return False
    stack = project['stack']
    conn.close()
    return threat['title'].lower() in stack.lower()


if __name__ == "__main__":
    print("run app")
    app.run("0.0.0.0", port=5000, debug=True)