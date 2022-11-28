#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, request, session
import pymysql.cursors
import bcrypt
import re
from datetime import datetime
import pandas as pd
import numpy as np
from os import listdir
from os.path import isfile, join, isdir
import glob
import os
from bs4 import BeautifulSoup
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import random


now = datetime.now()

#Threshold setting
threshold_1 = 3
threshold_2 = 5

# Preprocessed data
frame = pd.read_csv("./data/problem.csv")
content = pd.read_csv("./data/content.csv")
frame = frame.merge(content, how="left", on="Title")

# Model Training for Array
frame_array = frame.loc[frame['Array']==1].reset_index(drop=True)
column_trans = ColumnTransformer(
                [('categories', OneHotEncoder(dtype='int'),
                                 ['Difficulty']),
                ('tfidf', TfidfVectorizer(), 'problem')],
                remainder='drop', verbose_feature_names_out=False)
frame_arr = frame_array[["Id","Title","Difficulty","problem"]]
column_trans.fit(frame_arr)
column_trans.get_feature_names_out()
X = column_trans.transform(frame_arr).toarray()
model_array = KMeans(n_clusters=3, init='k-means++', max_iter=200, n_init=10)
model_array.fit(X)
labels=model_array.labels_
frame_array["cluster"] = labels 
#print(frame_array)

model_name = {"Array":model_array}
df_name = {"Array":frame_array}

connection = \
    pymysql.connect(host='database-1.czxn7uvkflod.us-west-2.rds.amazonaws.com'
                    , user='admin', password='SJSUSJSU7',
                    database='Masters_Project',
                    cursorclass=pymysql.cursors.DictCursor)
cursor = connection.cursor()
app = Flask(__name__)
app.secret_key = 'yoursecretkey'

def recommend_problem(ds, uid, score):
    while(True):
        ds_df = df_name[ds]
        flag = 0
        if(score>=threshold_1 and score<threshold_2):
            temp_df = ds_df[ds_df["cluster"]==1].reset_index(drop=True)
        elif(score>=threshold_2):
            temp_df = ds_df[ds_df["cluster"]==2].reset_index(drop=True)
        else:
            temp_df = ds_df[ds_df["cluster"]==0].reset_index(drop=True)
        qid = random.choice(temp_df["Id"].tolist())
        cursor.execute('Select * from questions_solved where userId = % s',(uid, ))
        result = cursor.fetchall()
        for r in result:
            if(r["questionId"]==qid):
                flag =1 
        if(flag==0):
            return temp_df[temp_df["Id"]==qid]["Content"].iloc[0]

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
                msg = {"message":"valid login", "uid": account["id"]}
            else:
                msg = {"message": "Invalid Login"}
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

@app.route('/')
@app.route('/get_next_problem', methods=['GET', 'POST'])
def get_next_problem():
    request_data = request.get_json()
    uid = request_data["userId"]
    ds = request_data["dataStructure"]
    cursor.execute("SELECT * FROM user_score WHERE userId = % s AND ds = % s",(uid, ds))
    userScore = cursor.fetchone()
    if(userScore):
        user_score = userScore["score"]
    else:
        user_score = 0
        cursor.execute('INSERT INTO user_score VALUES (% s, % s, % s)', (uid, ds, 0))
        connection.commit()
    content = recommend_problem(ds,uid, user_score)
    return {"Content":content}

@app.route('/get_data_structures', methods=['GET', 'POST'])
def get_data_structure():
    ds = ["Array", "Tree", "String", "Hash Table", "DFS"]
    return ds
    

if __name__ == '__main__':
    app.run(debug=True)
