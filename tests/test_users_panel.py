import bcrypt
#   Test adding a user
def test_add_user_success(client, mongo):
    mongo.db.users.insert_one({})
    r = client.post('/user/add', data={'first_name': 'FirstName',
                                       'last_name': 'LastName',
                                       'email': 'marta@gmail.com',
                                       'password': 'pass',
                                       'validate_password': 'pass'}, follow_redirects=True)
    assert b'User data saved' in r.data
    result = mongo.db.users.find_one({'first_name': 'FirstName'})
    assert result['first_name'] == "FirstName"
    assert result['last_name'] == "LastName"
    assert result['email'] == "marta@gmail.com"


#   Test adding a user without any of the required fields
def test_add_user_failure(client, mongo):
    mongo.db.users.insert_one({})
    r = client.post('/user/add', data={'first_name': '',
                                       'last_name': '',
                                       'email': '',
                                       'password': '',
                                       'validate_password': ''}, follow_redirects=True)
    assert b'Fill in all of the required fields' in r.data
    result = mongo.db.users.find_one({'first_name': 'FirstName'})
    assert not result


#   Test adding a user without a password
def test_add_user_validation(client, mongo):
    mongo.db.users.insert_one({})
    r = client.post('/user/add', data={'first_name': 'test',
                                       'last_name': 'test',
                                       'email': 'email@email.com',
                                       'password': '',
                                       'validate_password': ''}, follow_redirects=True)
    assert b'''Fill in all of the required fields''' in r.data
    result = mongo.db.users.find_one({'first_name': 'FirstName'})
    assert not result


#   Test editing a user
def test_edit_user_success(client, mongo):
    mongo.db.users.insert_one(
        {'first_name': 'first_name', 'last_name': 'surname', 'email': 'email@email.com',
         'password': 'password'})
    result = mongo.db.users.find_one({'first_name': 'first_name'})
    r = client.post('/user/%s' % str(result['_id']), data={'first_name': 'nameEdit',
                                                           'last_name': 'surnameEdit',
                                                           'email': 'test@test.com',
                                                           'password': '',
                                                           'validate_password': ''}, follow_redirects=True)
    assert b'User data saved' in r.data
    result = mongo.db.users.find_one({'first_name': 'nameEdit'})
    assert result['first_name'] == "nameEdit"
    assert result['last_name'] == "surnameEdit"
    assert result['email'] == "test@test.com"


#   Test editing a user without any of the required fields
def test_edit_user_without_required_fields(client, mongo):
    mongo.db.users.insert_one(
        {'first_name': 'first_name', 'last_name': 'last_name', 'email': 'email@email.com',
         'password': 'password'})
    result = mongo.db.users.find_one({'first_name': 'first_name'})
    r = client.post('/user/%s' % str(result['_id']), data={'first_name': '',
                                                           'last_name': '',
                                                           'email': '',
                                                           'password': '',
                                                           'validate_password': ''}, follow_redirects=True)
    assert b'''Fill in all of the required fields''' in r.data
    result = mongo.db.users.find_one({'first_name': 'first_name'})
    assert result['first_name'] == "first_name"
    assert result['last_name'] == "last_name"
    assert result['email'] == "email@email.com"


#   Test changing a user's email to another existing user's email
def test_edit_user_with_existing_email(client, mongo):
    mongo.db.users.insert_one(
        {'first_name': 'Sofie', 'last_name': 'Stubo', 'email': 'email@email.com',
         'password': 'password'})
    mongo.db.users.insert_one(
        {'first_name': 'Michal', 'last_name': 'Juras', 'email': 'gmail@gmail.com',
         'password': 'password'})
    result = mongo.db.users.find_one({'first_name': 'Michal'})

    r = client.post('/user/%s' % str(result['_id']), data={'first_name': 'Michal',
                                                           'last_name': 'Juras',
                                                           'email': 'email@email.com',
                                                           'password': 'password',
                                                           'validate_password': 'password'}, follow_redirects=True)
    assert b'User with this email already exist' in r.data


#   Test adding a user with an email of an existing user
def test_add_user_with_existing_email(client, mongo):
    mongo.db.users.insert_one(
        {'first_name': 'Sofie', 'last_name': 'Stubo', 'email': 'email@email.com',
         'password': 'password'})
    r = client.post('/user/add', data={'first_name': 'Michal',
                                       'last_name': 'Juras',
                                       'email': 'email@email.com',
                                       'password': 'password',
                                       'validate_password': 'password'}, follow_redirects=True)
    assert b'User with this email already exist' in r.data

    
#   Test adding a user without an id
def test_add_user_get_method_no_id(client, mongo):
    client.get("users/add")


# Test deleting an existing user
def test_user_delete(client, mongo):
    mongo.db.users.insert_one(
        {'first_name': 'first_name', 'last_name': 'last_name', 'email': 'email@email.com',
         'password': 'password'})
    result = mongo.db.users.find_one({'first_name': 'first_name'})
    r = client.get('/user/delete/%s' % str(result['_id']), follow_redirects=True)
    assert b'User was successfully deleted' in r.data
    query = mongo.db.users.find_one({'first_name': 'first_name'})
    assert not query


# Test adding a user with mismatched passwords
def test_password_do_not_match(client, mongo):
    r = client.post('/user/add', data={'first_name': 'test_name',
                                       'last_name': 'test',
                                       'email': 'email@email.com',
                                       'password': 'password',
                                       'validate_password': 'do not match'}, follow_redirects=True)
    assert b'''Passwords do not match''' in r.data
    result = mongo.db.users.find_one({'first_name': 'test_name'})
    assert not result


#   Test editing a users password
def test_edit_password(client, mongo):
    user = mongo.db.users.insert_one(
        {'first_name': 'first_name', 'last_name': 'last_name', 'email': 'email@email.com',
         'password': 'password'})
    r = client.post('/user/%s' % user.inserted_id, data={'first_name': 'first_name',
                                                            'last_name': 'last_name',
                                                            'email': 'email@email.com',
                                                            'password': 'new-password',
                                                            'validate_password': 'new-password'}, follow_redirects=True)
    assert b'User data saved' in r.data
    result = mongo.db.users.find_one({'first_name': 'first_name'})
    assert bcrypt.checkpw('new-password'.encode(), result['password'])


def test_edit_form_values(client, mongo):
    user = mongo.db.users.insert_one({'first_name': 'FirstName', 'last_name': 'LastName', 'email': 'email@email.com',
                               'password': 'password'})
    r = client.get('/user/%s' % user.inserted_id, follow_redirects=True)
    assert b'FirstName' in r.data
    assert b'LastName' in r.data
    assert b'email@email.com' in r.data


