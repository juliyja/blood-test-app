from flask import Flask
from flask.cli import FlaskGroup
from pymongo import IndexModel, DESCENDING

configs = {
    'test': 'config/testing.py',
    'prod': 'config/config.py',
    'default': 'config/config.py'
}


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_pyfile('config/config.py')
    app.config.from_envvar('API_CONFIG', silent=True)
    app.config.update(config or {})

    from model import mongo
    mongo.init_app(app, connect=False)

    from views.user.controller import user_panel
    app.register_blueprint(user_panel)

    from views.settings.controller import settings_panel
    app.register_blueprint(settings_panel)

    from views.patient.controller import patient_panel
    app.register_blueprint(patient_panel)

    from views.hospital.controller import hospital_panel
    app.register_blueprint(hospital_panel)

    from views.dashboard.controller import dashboard_panel
    app.register_blueprint(dashboard_panel)

    from views.authentication.controller import auth_panel
    app.register_blueprint(auth_panel)

    from model import login_manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth_panel.login'
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'warning'

    return app


cli = FlaskGroup(create_app=create_app)


@cli.command()
def initdb():
    from model import mongo

    mongo.db.patients.create_indexes([
        IndexModel([("due_date", DESCENDING)]),
        IndexModel([("results_received_date", DESCENDING)]),
        IndexModel([("first_name", DESCENDING)]),
        IndexModel([("last_name", DESCENDING)]),
        IndexModel([("date_of_birth", DESCENDING)]),
        IndexModel([("done_date", DESCENDING)])])

    mongo.db.blood_tests.create_indexes([
        IndexModel([("first_name", DESCENDING)]),
        IndexModel([("last_name", DESCENDING)])])

    mongo.db.hospitals.create_indexes([
        IndexModel([("name", DESCENDING)]),
        IndexModel([("hospital_number", DESCENDING)])])

    mongo.db.users.create_indexes([
        IndexModel([("email", DESCENDING), ("password", DESCENDING)])])

    mongo.db.users.create_index([("email", DESCENDING)], unique=True)


if __name__ == '__main__':
    import logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    cli()



