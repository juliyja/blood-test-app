from bson import ObjectId
from flask import Blueprint, render_template, request, redirect, url_for, flash
import logging

from flask_login import login_required

from model import mongo

hospital_panel = Blueprint('hospital', __name__, url_prefix='/hospital', template_folder='templates')

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


#   Makes sure string is appropriately formatted to pass to javascript function
@hospital_panel.app_template_filter()
def split_on_space(input_string):
    try:
        return input_string.strip().split()[0]
    except AttributeError:
        return "-"


#   Adds a new hospital or updates an existing one
@hospital_panel.route('/add', defaults={'row_id': None}, methods=['GET', 'POST'])
@hospital_panel.route('/<row_id>', methods=['GET', 'POST'])
@login_required
def modify(row_id):
    if request.method == 'POST':
        name = request.form.get('institution_name')
        hospital_number = request.form.get('hospital_number')
        phone = request.form.get('phone')
        location = request.form.get('location')
        postcode = request.form.get('postcode')
        email = request.form.get('email')

        mongo.db.hospitals.update_one(
            {'_id': ObjectId(row_id)},
            {'$set':
                 {"name": name, "hospital_number": hospital_number, "phone": phone, "location": location,
                  "email": email,
                  "postcode": postcode}
             }, upsert=True)
        flash('Hospital updated successfully', 'success')
        return redirect(url_for('.viewer'))

    if row_id:
        hospital = mongo.db.hospitals.find_one({'_id': ObjectId(row_id)})
    else:
        hospital = dict()

    return render_template('hospital/modify.html', hospital=hospital, row_id=row_id)


#   Creates a view of hospitals that will populate the table (different categories)
@hospital_panel.route('/', defaults={'page': 1, 'field': None, 'order': None}, methods=['GET'])
@hospital_panel.route('/search/', defaults={'page': 1, 'field': None, 'order': None}, methods=['GET'], endpoint='search')
@hospital_panel.route('/page/<int:page>', defaults={'field': None, 'order': None}, methods=['GET'])
@hospital_panel.route('/sort/<order>/<field>', defaults={'page': 1}, methods=['GET'])
@hospital_panel.route('/page/<int:page>/sort/<order>/<field>', methods=['GET'])
@login_required
def viewer(page, order, field):
    count = 5
    hospitals_col = mongo.db.hospitals
    display_columns = ["name", "hospital_number", "phone", "email", "location"]
    searched = request.values.get("search")

    if searched:
        hospitals = hospitals_col.find({"$or": [{"name": {"$regex": ".*" + searched + ".*", '$options': 'i'}},
                                                 {"hospital_number": {"$regex": ".*" + searched + ".*",
                                                                      '$options': 'i'}},
                                                 {"location": {"$regex": ".*" + searched + ".*", '$options': 'i'}}, ]})

    else:
        hospitals = hospitals_col.find({})

    if field and order:
        direction = {'asc': -1, 'desc': 1}[order]
        if field in ["name", "hospital_number"]:
            hospitals = hospitals.sort(field, direction)

    total_count = hospitals.count()

    if page:
        hospitals.skip(count * (page-1))

    hospitals.limit(count)

    return render_template('table.html', entries=list(hospitals), display_columns=display_columns, type='hospital',
                           order=order, page=page, searched=searched, count=count, field=field, total_count=total_count)



@hospital_panel.route("/delete/<row_id>", methods=['GET'])
@login_required
def delete(row_id):
    mongo.db.hospitals.delete_one({'_id': ObjectId(row_id)})
    flash("The institution was deleted", category="success")
    return redirect(url_for('.viewer'))
