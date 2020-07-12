import logging
from datetime import datetime
import pendulum

from flask import Blueprint, render_template, request
from flask_login import login_required

from model import mongo
from views.patient.controller import get_regex, safe_get

dashboard_panel = Blueprint('dashboard_panel', __name__, url_prefix='/dashboard', template_folder='templates')

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def get_no_results_patients_list(number=None):
    collection = mongo.db.blood_tests
    today = pendulum.today().replace(tzinfo=None)
    pipeline = [
        {
            u"$match": {
                u"results_received_date": {
                    u"$exists": False
                },
                u"due_date": {
                    u"$lt": today
                }
            }
        },
        {
            u"$group": {
                u"_id": u"$patient_id"
            }
        },
        {
            u"$lookup": {
                u"from": u"patients",
                u"localField": u"_id",
                u"foreignField": u"_id",
                u"as": u"patient"
            }
        },
        {
            u"$unwind": {
                u"path": u"$patient",
                u"preserveNullAndEmptyArrays": False
            }
        },
        {
            u"$project": {
                u"first_name": u"$patient.first_name",
                u"last_name": u"$patient.last_name",
                u"email": u"$patient.email",
                u"phone_number": u"$patient.phone_number"
            }
        }
    ]

    if number:
        pipeline.append({u'$limit': number})

    cursor = collection.aggregate(
        pipeline,
        allowDiskUse=False,
        collation={'locale': "en"}
    )

    return list(cursor)


def get_overdue_patients_list(number=None):
    collection = mongo.db.blood_tests
    today = pendulum.today().replace(tzinfo=None)
    pipeline = [
        {
            u"$match": {
                u"done_date": {
                    u"$exists": False
                },
                u"results_received_date": {
                    u"$exists": False
                },
                u"due_date": {
                    u"$lt": today
                }
            }
        },
        {
            u"$group": {
                u"_id": u"$patient_id"
            }
        },
        {
            u"$lookup": {
                u"from": u"patients",
                u"localField": u"_id",
                u"foreignField": u"_id",
                u"as": u"patient"
            }
        },
        {
            u"$unwind": {
                u"path": u"$patient",
                u"preserveNullAndEmptyArrays": False
            }
        },
        {
            u"$project": {
                u"first_name": u"$patient.first_name",
                u"last_name": u"$patient.last_name",
                u"email": u"$patient.email",
                u"phone_number": u"$patient.phone_number"
            }
        }
    ]

    if number:
        pipeline.append({u'$limit': number})

    cursor = collection.aggregate(
        pipeline,
        allowDiskUse=False,
        collation={'locale': "en"}
    )

    return list(cursor)


#   Returns a list of patients that have no scheduled blood tests
def get_patients_without_upcoming_blood_tests(number=None):
    collection = mongo.db.patients
    pipeline = [
        {
            u"$lookup": {
                u"from": u"blood_tests",
                u"localField": u"_id",
                u"foreignField": u"patient_id",
                u"as": u"blood_tests"
            }
        },
        {
            u"$unwind": {
                u"path": u"$blood_tests",
                u"preserveNullAndEmptyArrays": True
            }
        },
        {
            u"$match": {
                u"$or": [
                    {
                        u"blood_tests": {
                            u"$exists": False
                        }
                    },
                    {
                        u"blood_tests.results_received_date": {
                            u"$exists": True
                        }
                    },
                    {
                        u"blood_tests.done_date": {
                            u"$exists": True
                        }
                    }
                ]
            }
        },
        {
            u"$project": {
                u"first_name": 1.0,
                u"last_name": 1.0,
                u"email": 1.0,
                u"phone_number": 1.0
            }
        }
    ]

    if number:
        pipeline.append({u'$limit': number})

    cursor = collection.aggregate(
        pipeline,
        allowDiskUse=False,
        collation={'locale': "en"}
    )

    return list(cursor)


#   Returns the name of the columns which should be displayed in the table.
def get_columns():
    display_columns = ["first_name", "last_name", "email", "phone_number"]
    return display_columns


#   Redirects user to a table of patients whose blood tests have not been received or marked as done.
@dashboard_panel.route("/table/missing")
@login_required
def display_missing_table():
    return render_template('table.html', type='patient', entries=get_no_results_patients_list(),
                           display_columns=get_columns(), dashboard=True, dashboard_table=0, page=1, searched=True)


@dashboard_panel.route("/table/overdue")
@login_required
def display_overdue_table():
    return render_template('table.html', type='patient', entries=get_overdue_patients_list(),
                           display_columns=get_columns(), dashboard=True, dashboard_table=1, page=1, searched=True)


#   Redirects user to a table of patients who do not have any scheduled blood tests.
@dashboard_panel.route("/table/no_upcoming")
@login_required
def display_no_upcoming_table():
    return render_template('table.html', type='patient', entries=get_patients_without_upcoming_blood_tests(),
                           display_columns=get_columns(), dashboard=True, dashboard_table=2,  page=1, searched=True)


#   Creates a dashboard
@dashboard_panel.route("/")
@login_required
def create_dashboard():
    patients_count = mongo.db.patients.count()
    completed_test = 0
    requested_this_week = 0
    present = datetime.now()
    requested_this_month = 0
    completed_this_month = 0
    ratio_tests = 0

    for blood_test in mongo.db.blood_tests.find():
        done_test = blood_test.get('done_date')
        received_test = blood_test.get('results_received_date')
        due_date = blood_test.get('due_date')
        if due_date.isocalendar()[1] == present.isocalendar()[1] and due_date.year == present.year:
            requested_this_week += 1
            if done_test is not None or received_test is not None:
                completed_test += 1
        if requested_this_week == 0:
            ratio_tests = 0
        else:
            ratio_tests = int(completed_test / requested_this_week * 100)

        if due_date.month == present.month:
            requested_this_month += 1
            if done_test is not None or received_test is not None:
                completed_this_month += 1

    under_twelve = 0
    over_twelve = 0

    for patient in mongo.db.patients.find():
        dob = patient.get('date_of_birth')
        year_difference = present.year - dob.year
        if year_difference < 12:
            under_twelve += 1
        else:
            over_twelve += 1

    percent_of_under_twelve = 0
    percent_of_over_twelve = 0

    if patients_count != 0:
        percent_of_under_twelve = under_twelve / patients_count * 100
        percent_of_over_twelve = over_twelve / patients_count * 100

    data = {"completed": completed_test}
    data.update({"requested": requested_this_week})
    data.update({"less_twelve": percent_of_under_twelve})
    data.update({"over_twelve": percent_of_over_twelve})
    data.update({"patient_list_no_results": get_no_results_patients_list(5)})
    data.update({"patient_list_overdue": get_overdue_patients_list(5)})
    data.update({"patient_list_no_upcoming": get_patients_without_upcoming_blood_tests(5)})
    data.update({"display_columns": get_columns()})
    data.update({"completed_this_month": completed_this_month})
    data.update({"requested_this_month": requested_this_month})

    return render_template('dashboard/dashboard.html', patientsCount=patients_count, ratioTests=ratio_tests, data=data)
