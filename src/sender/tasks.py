import datetime
import os
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bson import ObjectId
from celery import Celery
from pymongo import MongoClient

from string import Template
from celery.utils.log import get_task_logger

from twilio.rest import Client

logging.getLogger('twilio.http_client').setLevel(logging.WARNING)

mongo = MongoClient(os.environ['MONGODB_URI'], connect=False)
app = Celery(broker=os.environ['MONGODB_URI'])

SMTP_PASSWORD = os.getenv('smtpPassword')
SMTP_EMAIL = 'bloodtestdiary@gmail.com'

account_sid = os.getenv('twilioAccount')
auth_token = os.getenv('twilioToken')
client = Client(account_sid, auth_token)

mongo.db = mongo.get_database()

logger = get_task_logger(__name__)

port = 465
context = ssl.create_default_context()


def age(born):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def create_notification(test_id, kind):
    notification = mongo.db.notifications.insert_one({
        'timestamp': datetime.datetime.now()
    })
    mongo.db.blood_tests.update_one(
        {'_id': ObjectId(test_id)},
        {'$push': {'notifications.%s' % kind: notification.inserted_id}})

    return str(notification.inserted_id)


def update_notification_status(notification_id, message, kind):
    mongo.db.notifications.update_one({'_id': ObjectId(notification_id)},
                                      {'$set': {'%s' % kind: {'timestamp': datetime.datetime.now(),
                                                              'content': message}}})


def template_message(patient, test_date, kind):
    template = mongo.db.settings.find_one({'name': 'notifications'})['templates'][kind]

    result = {}
    for type in template:
        t = Template(template[type])
        result[type] = t.safe_substitute(name=patient['first_name'], surname=patient['last_name'], date=test_date)

    return result


def format_time(date_obj):
    return date_obj.strftime("%d.%m.%Y")


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(30, check_send.s(), name='Check notifications that need to be send')


@app.task
def check_send():
    base_query = {'results_received_date': {'$exists': False},
                  'due_date': {'$lte': datetime.datetime.now() + datetime.timedelta(weeks=1)}}

    patient_query = {**base_query,
                     'done_date': {'$exists': False},
                     'notifications.patient': {'$exists': False}}

    remainders_for_patient = mongo.db.blood_tests.find(patient_query)
    for test in remainders_for_patient:
        send_patient_notification.delay(str(test['_id']))

    hospital_query = {**base_query,
                      'done_date': {'$exists': True},
                      'notifications.hospital': {'$exists': False}}

    remainders_for_hospitals = mongo.db.blood_tests.find(hospital_query)
    for test in remainders_for_hospitals:
        send_hospital_notification.delay(str(test['_id']))


@app.task
def send_patient_notification(test_id):
    test = mongo.db.blood_tests.find_one(ObjectId(test_id))
    patient = mongo.db.patients.find_one(ObjectId(test['patient_id']))
    due_date = format_time(test['due_date'])

    point_of_contact = patient
    if age(patient['date_of_birth']) < 16:
        point_of_contact = patient['carer']

    phone_number = point_of_contact.get('phone_number')
    email = point_of_contact.get('email')

    message = template_message(patient, due_date, 'patient')
    notification_id = create_notification(test_id, 'patient')

    send_sms.delay(notification_id, phone_number, message['text'])
    send_email.delay(notification_id, email, message['email'])


@app.task
def send_hospital_notification(test_id):
    test = mongo.db.blood_tests.find_one(ObjectId(test_id))
    patient = mongo.db.patients.find_one(ObjectId(test['patient_id']))

    done_date = format_time(test['done_date'])

    hospital_number = patient['hospital_number']
    hospital = mongo.db.hospitals.find_one({'hospital_number': hospital_number})
    email = hospital['email']

    notification_id = create_notification(test_id, 'hospital')

    message = template_message(patient, done_date, 'hospital')
    send_email.delay(notification_id, email, message['email'])


@app.task
def send_sms(notification_id, phone_number, message):
    client.messages.create(
        from_='+447427537241',
        body=message,
        to=phone_number
    )
    update_notification_status(notification_id, message, 'sms')


@app.task
def send_email(notification_id, email_address, message):
    email = MIMEMultipart('alternative')
    email['Subject'] = 'Blood test remainder'
    email.attach(MIMEText(message, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', port, context=context) as server:
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, email_address, email.as_string())

    update_notification_status(notification_id, message, 'email')

