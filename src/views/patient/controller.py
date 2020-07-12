import logging
from datetime import datetime

from bson import ObjectId
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from pymongo import DESCENDING

from model import mongo
from sender.tasks import send_hospital_notification, send_patient_notification

patient_panel = Blueprint('patient', __name__, url_prefix='/patient', template_folder='templates/',
                          static_folder='static/patient')

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


#   Transforms input of type string into date
def string_to_date(input_string):
    return datetime.strptime(input_string, "%d-%m-%Y")


#   Makes sure string is appropriately formatted to pass to javascript function
@patient_panel.app_template_filter()
def split_on_space(input_string):
    try:
        return input_string.strip().split()[0]
    except AttributeError:
        return "-"


#   Transforms input of type time into string
@patient_panel.app_template_filter()
def time_to_string(input_string):
    try:
        return input_string.strftime("%H:%M:%S")
    except AttributeError:
        return "-"


#   Transforms input of type date into string
@patient_panel.app_template_filter()
def date_to_string(input_string):
    try:
        return input_string.strftime("%d-%m-%Y")
    except AttributeError:
        return "-"


#   Transforms input of type date into value of a field
@patient_panel.app_template_filter()
def date_to_field(date_value):
    try:
        return date_value.strftime("%d-%m-%Y")
    except AttributeError:
        return ""


#   Adds a new patient (with backend validation) or updates information about a current patient
@patient_panel.route('/add', defaults={'row_id': None}, methods=['GET', 'POST'])
@patient_panel.route('/<row_id>', methods=['GET', 'POST'])
@login_required
def modify(row_id):
    hospitals = mongo.db.hospitals.find({}).sort('name', 1)

    if request.method == 'POST':
        first_name = request.values.get("first_name")
        last_name = request.values.get("last_name")
        date_of_birth = request.values.get("date_of_birth")
        sex = request.values.get("sex")
        phone_number = request.values.get("phone_number")
        email = request.values.get("email")
        diagnosis = request.values.get("diagnosis")
        transplant = request.values.get("transplant")
        hospital_number = request.values.get("hospital_number")
        carer_name = request.values.get("carer_name")
        carer_last_name = request.values.get("carer_last_name")
        carer_phone_number = request.values.get("carer_phone_number")
        carer_email = request.values.get("carer_email")

        if request.form.get("is_high_risk"):
            is_high_risk = True
        else:
            is_high_risk = False

        logger.info("HERE")
        logger.info(is_high_risk)

        if hospital_number:
            hospital_number = hospital_number.split(", ")[0]

        dob = date_of_birth
        dob = string_to_date(dob)
        patient_values = {'first_name': first_name, 'last_name': last_name, 'date_of_birth': dob,
                          'sex': sex, 'phone_number': phone_number,
                          'email': email, 'diagnosis': diagnosis, 'transplant': transplant,
                          'is_high_risk': is_high_risk,
                          'hospital_number': hospital_number, 'carer_name': carer_name,
                          'carer_last_name': carer_last_name, 'carer_phone_number': carer_phone_number,
                          'carer_email': carer_email}

        if get_age(dob) < 16:
            required_fields = [first_name, last_name, sex, date_of_birth,
                               carer_name, carer_last_name, carer_phone_number, carer_email, hospital_number]
            if not all(required_fields):
                flash('Fill in all of the required fields! '
                      'The patient is under 16 so the details of their carer are required', 'warning')
                return render_template('patient/modify.html', patient=patient_values, hospitals=hospitals,
                                       row_id=row_id)
        else:
            required_fields = [first_name, last_name, sex, date_of_birth,
                               phone_number, email, hospital_number]
            if not all(required_fields):
                flash('Fill in all of the required fields', 'warning')
                return render_template('patient/modify.html', patient=patient_values, hospitals=hospitals,
                                       row_id=row_id)

        mongo.db.patients.update_one(
            {'_id': ObjectId(row_id)},
            {
                "$set": {"first_name": first_name, "last_name": last_name,
                         "date_of_birth": string_to_date(date_of_birth), "sex": sex,
                         "phone_number": phone_number,
                         "email": email, "diagnosis": diagnosis,
                         "transplant": transplant, 'is_high_risk': is_high_risk, "hospital_number": hospital_number,
                         "carer": {"name": carer_name, "last_name": carer_last_name,
                                   "phone_number": carer_phone_number, "email": carer_email}}
            }, upsert=True)


        if row_id:
            flash('Patient updated successfully', 'success')
        else:
            flash('Patient added successfully', 'success')

        return redirect(url_for('.viewer'))

    if row_id:
        patient = mongo.db.patients.find_one({'_id': ObjectId(row_id)})
    else:
        patient = dict()

    return render_template('patient/modify.html', patient=patient, hospitals=hospitals, row_id=row_id)


#   Deletes a current patient
@patient_panel.route("/delete/<row_id>", methods=['GET'])
@login_required
def delete(row_id):
    mongo.db.patients.delete_one({'_id': ObjectId(row_id)})
    flash("The patient was deleted", category="success")
    return redirect(url_for('.viewer'))


#   Returns 4 categories of blood tests
@patient_panel.route("/blood_tests/<row_id>/", methods=['GET', 'POST'])
@login_required
def get_blood_tests(row_id):
    if request.method == 'POST':
        mongo.db.blood_tests.insert_one(
            {"patient_id": ObjectId(row_id), "due_date": string_to_date(request.values.get("next_date"))}
        )
    patient = mongo.db.patients.find_one({'_id': ObjectId(row_id)})
    upcoming_blood_tests = mongo.db.blood_tests.find(
        {'patient_id': ObjectId(row_id), "done_date": {"$exists": False},
         "results_received_date": {"$exists": False}}).sort("due_date", -1)
    done_blood_tests = mongo.db.blood_tests.find(
        {'patient_id': ObjectId(row_id), "done_date": {"$exists": True},
         "results_received_date": {"$exists": False}}).sort(
        "due_date", -1)
    to_review_blood_tests = mongo.db.blood_tests.find(
        {'patient_id': ObjectId(row_id), "results_received_date": {"$exists": True},
         "reviewed": {"$exists": False}}).sort("due_date", -1)
    past_blood_tests = mongo.db.blood_tests.find(
        {'patient_id': ObjectId(row_id), "reviewed": {"$exists": True}}).sort("due_date", -1)
    return render_template('patient/blood_tests.html', patient=patient, upcoming_blood_tests=upcoming_blood_tests,
                           done_blood_tests=done_blood_tests, to_review_blood_tests=to_review_blood_tests,
                           past_blood_tests=past_blood_tests)


#   Marks a blood test with a due date as done (done_date)
@patient_panel.route("/blood-tests/done/<row_id>/", defaults={'blood_test_id': None}, methods=['POST'])
@patient_panel.route("/blood-tests/done/<row_id>/<blood_test_id>", methods=['POST'])
@login_required
def mark_done(row_id, blood_test_id):
    if blood_test_id:
        mongo.db.blood_tests.update_one(
            {'_id': ObjectId(blood_test_id)},
            {'$set': {'done_date': string_to_date(request.values.get("done_date"))}})
        return redirect(url_for('.get_blood_tests', row_id=row_id))
    else:
        return "Missing blood test id", 400


#   Marks that the results for a particular blood test have been received (received_date)
@patient_panel.route("/blood-tests/received/<row_id>/", defaults={'blood_test_id': None}, methods=['POST'])
@patient_panel.route("/blood-tests/received/<row_id>/<blood_test_id>", methods=['POST'])
@login_required
def mark_received(row_id, blood_test_id):
    if blood_test_id:
        mongo.db.blood_tests.update_one(
            {'_id': ObjectId(blood_test_id)},
            {'$set': {'results_received_date': string_to_date(request.values.get("received_date"))}})
        return redirect(url_for('.get_blood_tests', row_id=row_id))
    else:
        return "Missing blood test id", 400


#   Marks that the results for a particular blood test have been reviewed
@patient_panel.route("/blood-tests/reviewed/<row_id>/", defaults={'blood_test_id': None}, methods=['GET'])
@patient_panel.route("/blood-tests/reviewed/<row_id>/<blood_test_id>", methods=['GET'])
@login_required
def mark_reviewed(row_id, blood_test_id):
    if blood_test_id:
        mongo.db.blood_tests.update_one(
            {'_id': ObjectId(blood_test_id)},
            {'$set': {'reviewed': True}})
        return redirect(url_for('.get_blood_tests', row_id=row_id))
    else:
        return "Missing blood test id", 400


# Creates a view of patients that will populate the table (different categories)
@patient_panel.route('/', defaults={'page': 1, 'field': None, 'order': None}, methods=['GET'])
@patient_panel.route('/search/', defaults={'page': 1, 'field': None, 'order': None}, methods=['GET'], endpoint='search')
@patient_panel.route('/page/<int:page>', defaults={'field': None, 'order': None}, methods=['GET'])
@patient_panel.route('/sort/<order>/<field>', defaults={'page': 1}, methods=['GET'])
@patient_panel.route('/page/<int:page>/sort/<order>/<field>', methods=['GET'])
@login_required
def viewer(page, order, field):
    count = 5
    patients_col = mongo.db.patients
    display_columns = ["first_name", "last_name", "sex", "date_of_birth"]
    searched = request.values.get("search")
    age_filter = request.values.get("age")

    if age_filter:
        age = age_filter.lower()
    else:
        age = "all"

    query = {}
    if searched:
        fields = searched.split(' ', 1)
        query = {'$or': [{'first_name': get_regex(safe_get(fields, 0)),
                          'last_name': get_regex(safe_get(fields, 1))},
                         {'first_name': get_regex(safe_get(fields, 1)),
                          'last_name': get_regex(safe_get(fields, 0))}]}
    if age != "all":
        dt = datetime.now()
        dt = dt.replace(year=dt.year - 12)
        if age == 'under 12':
            query['date_of_birth'] = {'$gte': dt}
        elif age == '12 and over':
            query['date_of_birth'] = {'$lt': dt}


    logger.info(query)
    patients = patients_col.find(query)

    if field and order:
        direction = {'asc': -1, 'desc': 1}[order]
        if field in ["first_name", "last_name", "date_of_birth"]:
            patients = patients.sort(field, direction)

    total_count = patients.count()

    if page:
        patients.skip(count * (page - 1))

    patients.limit(count)

    return render_template('table.html', entries=list(patients), display_columns=display_columns, type='patient',
                           order=order, page=page, searched=searched, count=count, field=field, age=age, total_count=total_count)


#   Sends a notification to either patient of hospital
@patient_panel.route("/send-notification/<row_type>/<row_id>/<test_id>", methods=['GET'])
@login_required
def send_notification(row_type, row_id, test_id):
    if row_type == 'hospital':
        send_hospital_notification.delay(test_id)
    elif row_type == 'patient':
        send_patient_notification.delay(test_id)
    else:
        return 'Invalid type', 400

    flash('Notification to the %s sent successfully' % row_type, 'info')
    return redirect(url_for('.get_blood_tests', row_id=row_id))


#   Returns a log history of all notifications sent for a particaular blood test
@patient_panel.route("/get-notifications/<row_id>/<test_id>")
@login_required
def get_notification_log(row_id, test_id):
    patient = mongo.db.patients.find_one({'_id': ObjectId(row_id)})
    blood_test = mongo.db.blood_tests.find_one({'_id': ObjectId(test_id)})
    hospital = mongo.db.hospitals.find_one({'hospital_number': patient.get('hospital_number')})

    notifications = mongo.db.blood_tests.find_one({'_id': ObjectId(test_id)}).get('notifications', {})
    patient_notification_ids = notifications.get('patient', [])
    hospital_notification_ids = notifications.get('hospital', [])

    patient_log_sms = [x.get('sms', {}) for x in
                       mongo.db.notifications.find({"_id": {"$in": patient_notification_ids}}, {'sms': 1}).sort(
                           [('sms.timestamp', DESCENDING)])]
    patient_log_email = [x.get('email', {}) for x in
                         mongo.db.notifications.find({"_id": {"$in": patient_notification_ids}}).sort(
                             [('email.timestamp', DESCENDING)])]

    hospital_log_email = [x.get('email', '') for x in
                          mongo.db.notifications.find({"_id": {"$in": hospital_notification_ids}}).sort(
                              [('email.timestamp', DESCENDING)])]

    return render_template('patient/notifications_log.html', blood_test=blood_test, hospital=hospital, patient=patient,
                           patient_log_sms=patient_log_sms, patient_log_email=patient_log_email,
                           hospital_log_email=hospital_log_email)


#   Injects a current date
@patient_panel.context_processor
def inject_today_date():
    return {'today_date': datetime.today()}


#   Returns an age (in years) from a date passed as an argument
def get_age(dob):
    today = datetime.today()
    years = today.year - dob.year
    if today.month < dob.month or (today.month == dob.month and today.day < dob.day):
        years -= 1
    return years


#  Safely gets an element of an array without exceptions
def safe_get(array, index, default=''):
    return array[index] if len(array) > index else default


#   Returns a regex
def get_regex(field):
    return {"$regex": ".*" + field + ".*", '$options': 'i'}
