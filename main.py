import os
import re
import sqlite3
from crypt import crypt
from hashlib import sha1
from base64 import b64encode
from datetime import datetime
from itertools import groupby
from nkf import nkf
from flask import Flask, request, render_template, redirect, url_for, abort
from dotenv import load_dotenv, find_dotenv
app = Flask(__name__)
load_dotenv(find_dotenv())
conn = sqlite3.connect(os.environ.get('BBS_DB', './bbs.db'))
conn.row_factory = sqlite3.Row


MAX_LENGTH = {
    'title': 64,
    'name': 32,
    'email': 128,
}


class ValidationError(Exception):
    pass


class ThreadDoesNotExist(Exception):
    pass


# helper functions
def validate_thread(title: str) -> None:
    if len(title) <= 0 or len(title) > MAX_LENGTH['title']:
        raise ValidationError('`Subject` must not be empty or longer than '
                              '{} characters.'.format(MAX_LENGTH['title']))


def validate_post(name: str, email: str, text: str) -> None:
    if len(name) <= 0 or len(name) > MAX_LENGTH['name']:
        raise ValidationError('`Name` must not be empty or longer than '
                              '{} characters.'.format(MAX_LENGTH['name']))
    if len(email) > MAX_LENGTH['email']:
        raise ValidationError('`E-mail` must not be longer than '
                              '{} characters.'.format(MAX_LENGTH['email']))


def check_thread_exists(thread_id: int) -> None:
    count = conn.execute('SELECT COUNT(*) FROM threads '
                         'WHERE id = ?', (thread_id,))
    if count == 0:
        raise ThreadDoesNotExist()


def post_thread(title: str) -> int:
    '''
    Creates a thread and posts. Returns an integer representing the ID of it.
    '''
    created_at = datetime.now()

    c = conn.execute('INSERT INTO threads (title, created_at, updated_at) '
                     'VALUES (?, DATETIME("NOW"), DATETIME("NOW"))', (title,))
    thread_id = c.lastrowid

    return thread_id


def create_post(thread_id: int, name: str, email: str, text: str) -> int:
    c = conn.execute('INSERT INTO posts '
                     '(thread_id, name, email, text, created_at) '
                     'VALUES (?, ?, ?, ?, DATETIME("NOW"))',
                     (thread_id, name, email, text,))
    if email != 'sage':
        update_thread_timestamp(thread_id)

    return c.lastrowid


def list_threads():
    threads = [dict(x) for x in conn.execute('SELECT * FROM threads '
                                             'ORDER BY updated_at '
                                             'DESC').fetchall()]
    posts_groupby = groupby(conn.execute('SELECT * FROM posts ORDER BY '
                                         'thread_id ASC').fetchall(),
                            key=lambda x: x['thread_id'])
    posts = {k: list(v) for k, v in posts_groupby}
    for i, thread in enumerate(threads):
        threads[i]['posts'] = list(posts[thread['id']])
    return threads


def get_posts(thread_id):
    return conn.execute('SELECT * FROM posts WHERE thread_id = ? '
                        'ORDER BY created_at ASC', (thread_id,)).fetchall()


def get_title(thread_id):
    return conn.execute('SELECT title FROM threads WHERE id = ?',
                        (thread_id,)).fetchone()['title']


def update_thread_timestamp(thread_id):
    conn.execute('UPDATE threads SET updated_at = DATETIME("NOW") '
                 'WHERE id = ?', (thread_id,))


def generate_trip(tripstr: str) -> str:
    tripstr = nkf('s', tripstr).decode('shiftjis')
    if len(tripstr) >= 12:
        mark = tripstr[0]
        if mark == '#' or mark == '$':
            m = re.match(r'^#([0-9a-fA-F]{16})([\./0-9A-Za-z]{0,2})$', tripstr)
            if m:
                trip = crypt(str(int(m.group(1))), m.group(2) + '..')[-10:]
            else:
                trip = '???'
        else:
            m = sha1()
            m.update(tripstr)
            trip = str(b64encode(m.hexdigest))[:12]
            trip = trip.replace('+', '.')
    else:
        tripkey = tripstr[1:]
        salt = (tripkey + "H.")[1:3]
        salt = re.sub(r'[^\.-z]', '.', salt)
        salt = salt.translate(str.maketrans(':;<=>?@[\\]^_`', 'ABCDEFGabcdef'))
        trip = crypt(tripkey, salt)
        trip = trip[-10:]
    trip = '◆' + trip
    return trip
# end helper functions


@app.route('/')
def index():
    return render_template('index.html', threads=list_threads())


@app.route('/threads/create', methods=['GET', 'POST'])
def create_thread():
    if request.method == 'GET':
        return render_template('create_thread.html', max_length=MAX_LENGTH)
    elif request.method == 'POST':
        title = request.form['title']
        name = request.form['name']
        email = request.form['email']
        text = request.form['text']

        try:
            validate_thread(title)
            validate_post(name, email, text)
        except ValidationError:
            return redirect(url_for('create_thread'))
        else:
            # transaction
            try:
                with conn:
                    thread_id = post_thread(title)
                    create_post(thread_id, name, email, text)
                    return redirect(url_for('show_thread',
                                            thread_id=thread_id))
            except sqlite3.IntegrityError:
                return redirect(url_for('index'))


@app.route('/threads/<int:thread_id>', methods=['GET'])
def show_thread(thread_id):
    return render_template('show_thread.html', posts=get_posts(thread_id),
                           title=get_title(thread_id), max_length=MAX_LENGTH,
                           thread_id=thread_id)


@app.route('/threads/<int:thread_id>', methods=['POST'])
def post_to_thread(thread_id):
    name = request.form['name']
    email = request.form['email']
    text = request.form['text']
    try:
        validate_post(name, email, text)
        check_thread_exists(thread_id)
    except ValidationError:
        return redirect(url_for('show_thread', thread_id=thread_id))
    except ThreadDoesNotExist:
        abort(400)
    else:
        try:
            with conn:
                create_post(thread_id, name, email, text)
                return redirect(url_for('show_thread', thread_id=thread_id))
        except sqlite3.IntegrityError:
            return redirect(url_for('show_thread', thread_id=thread_id))


if __name__ == '__main__':
    app.run(port=os.environ.get('BBS_PORT', 8080))
