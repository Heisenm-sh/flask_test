from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.db import get_db
from flask import  current_app

bp = Blueprint('auth', __name__, url_prefix='/auth')


class blogRoot(object):
    power = False


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        current_app.logger.debug('2')
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        elif db.execute(
                'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'User {0} is already registered.'.format(username)

        if error is None:
            db.execute(
                'INSERT INTO users (username, password) VALUES(?,?)',
                (username, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        if user is None:
            error = 'Incorrect username'
        elif not check_password_hash(user['password'], password):
            if user['id'] is not 0:
                error = 'Incorrect password'
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            if user['id'] == 0:
                blogRoot.power = True
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    if session['user_id'] == 0:
        blogRoot.power = False
    session.clear()
    return redirect(url_for('index'))
