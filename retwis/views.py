import redis

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

@app.route('/signup', methods=['GET','POST'])
def signup():
    error = None
    if request.method == 'GET':
        return render_template('signup.html', error=error)
    username = request.form['username']
    password = request.form['password']
    user_id = str(g.db.incrby('next_user_id', 1000))
    g.db.hmset('user:'+user_id, dict(username=username, password=password))
    g.db.hset('users', username, user_id)
    session['username'] = username
    return jsonify(**g.db.hgetall('user:'+user_id))

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
    if password != g.db.hget('user:'+str(user_id), 'password'):
        error = 'Incorrect password'
        return render_template('login.html', error=error)
    session['username'] = username
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/home', methods=['GET'])
def home():
    app.logger.debug('Session %s', session)
    if not session['username']:
        return redirect(url_for('login'))
    return render_template('home.html')
