#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, request, session
import pymysql.cursors
import bcrypt
import re
from datetime import datetime
now = datetime.now()

connection = \
    pymysql.connect(host='database-1.czxn7uvkflod.us-west-2.rds.amazonaws.com'
                    , user='admin', password='SJSUSJSU7',
                    database='Masters_Project',
                    cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()
app = Flask(__name__)
app.secret_key = 'yoursecretkey'

@app.route('/')
@app.route('/get_problems', methods=['GET', 'POST'])
def get_problems():
    sql = 'Select * from Problems'
    cursor.execute(sql)
    result = cursor.fetchall()
    return result


@app.route('/get_problem_by_title', methods=['GET', 'POST'])
def get_problem_by_title():
    request_data = request.get_json()
    if request.method == 'POST' and 'title' in request_data:
        title = request_data['title']

        cursor.execute('SELECT * FROM Problems WHERE Title = % s',
                       (title, ))
        result = cursor.fetchone()
        return result
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""
    request_data = request.get_json()
    if request.method == "POST":
        if "username" in request_data and "password" in request_data:
            username = request_data["username"]
            password = request_data["password"]
            # hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "SELECT * FROM users WHERE username = % s AND password = % s",
                (username, password),
            )
            account = cursor.fetchone()
            if account:
                session["loggedin"] = True
                session["id"] = account["id"]
                session["username"] = account["username"]
                msg = "Valid Login"
            else:
                msg = "Invalid Login"
    return msg

@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ""
    request_data = request.get_json()
    if request.method == "POST":
        if 'username' in request_data and 'password' in request_data and 'email' in request_data :
            username = request_data['username']
            password = request_data['password']
            email = request_data['email']
            cursor.execute('SELECT * FROM users WHERE username = % s', (username, ))
            account = cursor.fetchone()
            cursor.execute('SELECT count(id) FROM Masters_Project.users')
            usersCount = cursor.fetchone()
            userId = usersCount["count(id)"] + 100000
            if account:
                msg = 'Account already exists !'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address !'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers !'
            elif not username or not password or not email:
                msg = 'Please fill out the form !'
            else:
                cursor.execute('INSERT INTO users VALUES (% s, % s, % s, % s, % s)', (userId, username, password, email, now))
                connection.commit()
                msg = 'You have successfully registered !'
        elif request.method == 'POST':
            msg = 'Please fill out the form !'
        return msg

if __name__ == '__main__':
    app.run(debug=True)
