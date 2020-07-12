import logging

import bcrypt
import pymongo
from bson import ObjectId
from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask_login import login_required

from model import mongo
from views.patient.controller import get_regex, safe_get

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

user_panel = Blueprint('user', __name__, url_prefix='/user', template_folder='templates/user',
                       static_folder='static/user')


#   Makes sure string is appropriately formatted to pass to javascript function
@user_panel.app_template_filter()
def split_on_space(input_string):
    try:
        return input_string.strip().split()[0]
    except AttributeError:
        return "-"


#   Adds a new user or updates an existing user with back-end validation of the values entered.
@user_panel.route('/add', defaults={'row_id': None}, methods=['GET', 'POST'])
@user_panel.route('/<row_id>', methods=['GET', 'POST'])
@login_required
def modify(row_id):
    if request.method == 'POST':
        name = request.values.get('first_name')
        surname = request.values.get('last_name')
        email = request.values.get('email')
        password = request.values.get('password')
        validate_password = request.values.get('validate_password')

        user = {'first_name': name, 'last_name': surname, 'email': email}

        required_fields = [name, surname, email]
        if not row_id:
            required_fields.append(password)

        if not all(required_fields):
            flash('Fill in all of the required fields', 'warning')
            return render_template('user.html', user=user, row_id=row_id)

        if password and password != validate_password:
            flash('Passwords do not match', 'warning')
            return render_template('user.html', user=user, row_id=row_id)

        update_query = {'first_name': name, 'last_name': surname, 'email': email}
        if password:
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            update_query['password'] = hashed_password

        try:
            mongo.db.users.update_one({'_id': ObjectId(row_id)}, {'$set': update_query}, upsert=True)
        except pymongo.errors.DuplicateKeyError:
            flash('User with this email already exists', category='warning')
            return render_template('user.html', user=user, row_id=row_id)

        flash('User data saved', category='success')
        return redirect(url_for('user.viewer'))
    if row_id:
        user = mongo.db.users.find_one({'_id': ObjectId(row_id)})
    else:
        user = {'first_name': request.values.get('first_name', ''), 'last_name': request.values.get('last_name', ''),
            'email': request.values.get('email', '')}

    return render_template('user.html', user=user, row_id=row_id)


#     Displays a table of users which can be sorted and searched with page numbers
@user_panel.route('/', defaults={'page': 1, 'field': None, 'order': None}, methods=['GET'])
@user_panel.route('/search/', defaults={'page': 1, 'field': None, 'order': None}, methods=['GET'], endpoint='search')
@user_panel.route('/page/<int:page>', defaults={'field': None, 'order': None}, methods=['GET'])
@user_panel.route('/sort/<order>/<field>', defaults={'page': 1}, methods=['GET'])
@user_panel.route('/page/<int:page>/sort/<order>/<field>', methods=['GET'])
@login_required
def viewer(page, order, field):
    count = 5
    users_col = mongo.db.users
    display_columns = ["first_name", "last_name", "email"]
    searched = request.values.get("search")

    if searched:
        fields = searched.split(' ', 1)
        users = users_col.find({'$or': [{'first_name': get_regex(safe_get(fields, 1)),
                                         'last_name': get_regex(safe_get(fields, 0))},
                                        {'first_name': get_regex(safe_get(fields, 0)),
                                         'last_name': get_regex(safe_get(fields, 1))},
                                        {'email': get_regex(safe_get(fields, 0))}]})

    else:
        users = users_col.find({})

    if field and order:
        direction = {'asc': -1, 'desc': 1}[order]
        if field in ["first_name", "last_name", "email"]:
            users = users.sort(field, direction)
    total_count = users.count()
    if page:
        users.skip(count * (page - 1))

    users.limit(count)

    return render_template('table.html', entries=list(users), display_columns=display_columns, type='user',
                           order=order, page=page, searched=searched, count=count, field=field, total_count=total_count)


#   Deletes a user from the collection.
@user_panel.route("/delete/<row_id>", methods=['GET'])
@login_required
def delete(row_id):
    mongo.db.users.delete_one({'_id': ObjectId(row_id)})
    flash("User was successfully deleted", category='success')
    return redirect(url_for('user.viewer'))
