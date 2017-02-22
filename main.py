import os
import sqlite3
from datetime import datetime
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
        raise ValidationError('`title` must not be empty or longer than '
                              '{} characters.'.format(MAX_LENGTH['title']))


def validate_post(name: str, email: str, text: str) -> None:
    if len(name) <= 0 or len(name) > MAX_LENGTH['name']:
        raise ValidationError('`name` must not be empty or longer than '
                              '{} characters.'.format(MAX_LENGTH['name']))
    if len(email) > MAX_LENGTH['email']:
        raise ValidationError('`email` must not be empty or longer than '
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

    return c.lastrowid


def list_threads():
    threads = conn.execute('SELECT * FROM threads ORDER BY updated_at DESC').fetchall()
    for i, thread in enumerate(threads):
        threads[i] = dict(threads[i])
        threads[i]['posts'] = conn.execute('SELECT * FROM posts '
                                           'WHERE thread_id = ? '
                                           'ORDER BY created_at ASC LIMIT 5',
                                           (thread['id'],)).fetchall()
    return threads


def get_posts(thread_id):
    return conn.execute('SELECT * FROM posts WHERE thread_id = ? '
                        'ORDER BY created_at ASC', (thread_id,)).fetchall()


def get_title(thread_id):
    return conn.execute('SELECT title FROM threads WHERE id = ?',
                        (thread_id,)).fetchone()['title']
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
