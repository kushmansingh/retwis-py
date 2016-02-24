import redis

from flask import g, jsonify, request, render_template

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
    return jsonify(**g.db.hgetall('user:'+user_id))

@app.route('/login')
def login():
    return jsonify(test='yes')