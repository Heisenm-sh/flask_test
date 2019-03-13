from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort
import functools
from flaskr.db import get_db
from flask import current_app
from flaskr.auth import blogRoot as admin

bp = Blueprint('blog', __name__)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        '''SELECT post.id, title ,body, created, author_id, username
           FROM post LEFT OUTER JOIN users ON post.author_id = users.id
           ORDER BY created DESC'''
    ).fetchall()
    return render_template('blog/index.html', posts=posts, admin=admin.power)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None
        if not title:
            error = 'Title is required'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post(title,body,author_id)'
                'VALUES(?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))
    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        '''SELECT post.id,title, body ,created,author_id,username
         FROM post LEFT OUTER JOIN users ON post.author_id = users.id
         WHERE post.id = ?''',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist ".format(id))

    if (check_author and post['author_id'] != g.user['id']) and not admin.power:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title =?, body=?'
                'WHERE id = ?',
                (title, body, id)

            )
            db.commit()
            return redirect(url_for('blog.index'))
    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@login_required
@bp.route("/<int:id>/article")
def article(id):
    db = get_db()
    post = db.execute(
        '''SELECT username,title,body,created from users,post 
        Where users.id=post.author_id and post.id=? ''',
        (id,)
    ).fetchone()
    return render_template("blog/article.html", post=post)


@bp.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id =?', (user_id,)
        ).fetchone()
