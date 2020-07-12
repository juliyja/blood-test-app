import logging

import bcrypt
from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user

from model import User
from model import mongo

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

auth_panel = Blueprint('auth_panel', __name__, url_prefix='', static_folder='static/auth', template_folder='templates/')


#   Logs authorised users in to the application
@auth_panel.route('/', methods=['GET'])
@auth_panel.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.values.get('email')
        password = request.values.get('password')

        result = mongo.db.users.find_one({'email': email})
        if result and bcrypt.checkpw(password.encode(), result['password']):
            logger.info('Password fine')
            user = User(str(result['_id']), result['first_name'], result['last_name'], result['email'])
            login_user(user)
            logger.info("Login OK")
            # TODO change to dashboard once its fixed.
            flash('Logged in succesfully', category='success')
            return redirect(url_for('dashboard_panel.create_dashboard'))
        else:
            flash('Incorrect username or password', category='warning')

    if current_user.is_authenticated:
        return redirect(url_for('dashboard_panel.create_dashboard'))

    return render_template('login.html', email=request.values.get('email', ''))


#   Logs out users from the application
@auth_panel.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth_panel.login'))
