import os

import bcrypt
import mongomock as mongomock
import pytest

from main import create_app

os.environ['MONGODB_URI'] = 'mongodb://127.0.0.1/testdb'


@pytest.fixture(scope="session")
def app():
    app = create_app({"ENV": 'development',
                      "DEBUG": True,
                      "TESTING": True})

    return app


@pytest.fixture(scope="session")
def client(app):
    client = app.test_client()
    with client as c:
        yield c


@pytest.fixture()
def mongo(app, monkeypatch):
    with app.app_context():
        from model import mongo
        monkeypatch.setattr(mongo, 'cx', mongomock.MongoClient())
        monkeypatch.setattr(mongo, 'db', mongo.cx['testdb'])

        runner = app.test_cli_runner()
        from main import initdb
        runner.invoke(initdb)

        yield mongo


@pytest.fixture(autouse=True)
def auth(mongo, client):
    email = "test@test"
    pwd = "1234"
    hashed_password = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())
    mongo.db.users.insert_one(
        {'first_name': "test", "last_name": 'test_surname', "email": email, "password": hashed_password})
    r = login(client, email, pwd)
    return {'client': client, 'response': r}


def login(client, email, password):
    return client.post('/login', data={
        'email': email,
        'password': password}, follow_redirects=True)
