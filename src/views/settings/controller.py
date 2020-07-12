import logging

import html2text as html2text
from flask import Blueprint, render_template, request, flash
from flask_login import login_required

from model import mongo

settings_panel = Blueprint('settings', __name__, url_prefix='/settings', static_folder='static/settings',
                           template_folder='templates/settings')
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


#   Edits the text of an email or a text message
@settings_panel.route("/", defaults={'category': None}, methods=['GET', 'POST'])
@settings_panel.route("/<category>", methods=['POST', 'GET'])
@login_required
def edit_message(category):
    if request.method == 'POST':
        email_message = request.values.get('email_editor_%s' % category)
        SMS_in_html = request.values.get('SMS_editor_%s' % category)
        text_message = html2text.html2text(str(SMS_in_html))
        mongo.db.settings.update_one({'name': 'notifications'},
                                     {"$set":
                                         {'templates.%s' % category: {
                                             'email': email_message,
                                             'text': ' '.join(text_message.splitlines())
                                         }}}, upsert=True)
        flash("Messages were updated", category='success')

    try:
        templates = mongo.db.settings.find_one({'name': 'notifications'})['templates']
    except (TypeError, KeyError):
        templates = {}

    hospital_template = templates.get('hospital', {})
    patient_template = templates.get('patient', {})

    return render_template('settings.html', patient=patient_template, hospital=hospital_template)
