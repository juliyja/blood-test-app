import bcrypt
import pytest
from conftest import login
from flask_login import current_user


#   Helper function used in tests
#   Logs out a user
def logout(client):
    return client.get('/logout', follow_redirects=True)


#   Helper function used in tests
#   Authenticates a user
@pytest.fixture()
def auth(mongo, client):
    email = "test@test"
    pwd = "1234"
    hashed_password = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())
    mongo.db.users.insert_one(
        {'first_name': "test", "last_name": 'test_surname', "email": email, "password": hashed_password})
    r = login(client, email, pwd)
    return {'client': client, 'response': r}


#   Tests unsuccessful login
def test_user_unsuccesful_login(client, mongo):
    r = login(client, "wrong", "wrong")
    assert b"Incorrect username or password" in r.data


#   Tests successful login
def test_user_succesful_login(auth):
    assert current_user.is_authenticated
    assert b'Logged in succesfully' in auth['response'].data


#   Tests security of a route
def test_secure_route_success(auth, mongo):
    mongo.db.settings.insert_one({'name': 'notifications'})
    r = auth['client'].get('/settings', follow_redirects=True)
    assert b"Settings" in r.data


#   Tests if a user was successfully logged out
def test_logout_success(auth):
    # LOGIN first
    assert current_user.is_authenticated
    assert b'Logged in succesfully' in auth['response'].data
    # logout
    auth['client'].get("/logout")
    # check if session deactivated
    assert not current_user.is_authenticated
    r = auth['client'].get('/settings', follow_redirects=True)
    assert b"Please login to access this page" in r.data


#   Tests if a user us redirected correctly after logging in
def test_redirect_on_login(auth):
    r = auth['client'].get('/', follow_redirects=True)
    assert current_user.is_authenticated
    assert b'Completed Blood Tests' in r.data
