import redis

from datetime import datetime
from flask import (g, jsonify, request, render_template,
                   session, redirect, url_for)

from retwis import app


def init_db():
    db = redis.StrictRedis(
        host=app.config['DB_HOST'],
        port=app.config['DB_PORT'],
        db=app.config['DB_NO'])
    return db


@app.before_request
def before_request():
    g.db = init_db()


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'GET':
        return render_template('signup.html', error=error)
    username = request.form['username']
    password = request.form['password']
    user_id = str(g.db.incrby('next_user_id', 1000))
    g.db.hmset('user:' + user_id, dict(username=username, password=password))
    g.db.hset('users', username, user_id)
    session['username'] = username
    return redirect(url_for('home'))


@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'GET':
        return render_template('login.html', error=error)
    username = request.form['username']
    password = request.form['password']
    user_id = g.db.hget('users', username)
    if not user_id:
        error = 'No such user'
        return render_template('login.html', error=error)
    if password != g.db.hget('user:' + str(user_id), 'password'):
        error = 'Incorrect password'
        return render_template('login.html', error=error)
    session['username'] = username
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/home', methods=['GET', 'POST'])
def home():
    if not session:
        return redirect(url_for('login'))

    user_id = g.db.hget('users', session['username'])
    if request.method == 'GET':
        return render_template('home.html', timeline=_get_timeline(user_id))
    text = request.form['tweet']
    post_id = str(g.db.incr('next_post_id'))
    g.db.hmset('post:' + post_id, dict(user_id=user_id,
                                       ts=datetime.utcnow(), text=text))
    g.db.lpush('posts:' + user_id, post_id)
    g.db.lpush('timeline:' + user_id, post_id)
    g.db.ltrim('timeline:' + user_id, 0, 100)
    return render_template('home.html', timeline=_get_timeline(user_id))


def _get_timeline(user_id):
    posts = g.db.lrange('timeline:' + user_id, 0, -1)
    timeline = []
    for post_id in posts:
        post = g.db.hgetall('post:' + post_id)
        timeline.append(dict(
            username=g.db.hget('user:' + post['user_id'], 'username'),
            ts=post['ts'],
            text=post['text']))
    return timeline
