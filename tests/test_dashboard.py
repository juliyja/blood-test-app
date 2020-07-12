from datetime import datetime, timedelta

from mongomock import ObjectId


#   Helper function used in tests
#   Adds a patient under 12 years old
def add_patient_under_12(client, first_name, last_name, carer_info):
    sex = "Female"
    date_of_birth = "11-03-2008"
    hospital_number = "123"
    carer_name = "Erik"
    carer_last_name = "Stuboe"
    carer_phone_number = "1231231231"
    carer_email = "erik@erik.com"
    if carer_info:
        return client.post("/patient/add", data={'first_name': first_name,
                                                 'last_name': last_name,
                                                 'sex': sex,
                                                 'date_of_birth': date_of_birth,
                                                 'hospital_number': hospital_number,
                                                 'carer_name': carer_name,
                                                 'carer_last_name': carer_last_name,
                                                 'carer_phone_number': carer_phone_number,
                                                 'carer_email': carer_email}, follow_redirects=True)
    else:
        return client.post("/patient/add", data={'first_name': first_name,
                                                 'last_name': last_name,
                                                 'sex': sex,
                                                 'date_of_birth': date_of_birth,
                                                 'hospital_number': hospital_number}, follow_redirects=True)


#   Helper function used in tests
#   Adds a patient above 12 years old
def add_patient_over_12(client, first_name, last_name):
    sex = "Female"
    date_of_birth = "11-03-2000"
    hospital_number = "123"
    phone_number = "123123123"
    email = "sofie@sofie.com"

    return client.post("/patient/add", data={'first_name': first_name,
                                             'last_name': last_name,
                                             'sex': sex,
                                             'date_of_birth': date_of_birth,
                                             'hospital_number': hospital_number,
                                             'phone_number': phone_number,
                                             'email': email}, follow_redirects=True)


#   Helper function used in tests
#   Adds a blood test scheduled for today
def add_blood_test_for_today(client, mongo):
    add_patient_over_12(client, "John", "Doe")
    patient = mongo.db.patients.find_one({'first_name': "John"})
    patient_id = patient['_id']
    mongo.db.blood_tests.insert_one({"patient_id": ObjectId(patient_id), "due_date": datetime.now()})


#   Helper function used in tests
#   Marks a blood test as completed today
def add_blood_test_for_today_completed(client, mongo):
    add_patient_over_12(client, "Jessica", "Johnson")
    patient = mongo.db.patients.find_one({'first_name': "John"})
    patient_id = patient['_id']
    blood = mongo.db.blood_tests.insert_one({"patient_id": ObjectId(patient_id), "due_date": datetime.now()})
    client.post(f"patient/blood-tests/done/{patient_id}/{blood.inserted_id}", data={'done_date': "30-03-2002"},
                follow_redirects=True)


def add_blood_test_for_yesterday(client, mongo):
    add_patient_over_12(client, "Pam", "Beesly")
    patient = mongo.db.patients.find_one({'first_name': "Pam"})
    patient_id = patient['_id']
    mongo.db.blood_tests.insert_one(
        {"patient_id": ObjectId(patient_id), "due_date": datetime.now() - timedelta(days=1)})


def add_blood_test_for_yesterday_completed(client, mongo):
    add_patient_over_12(client, "Jim", "Halpert")
    patient = mongo.db.patients.find_one({'first_name': "Jim"})
    patient_id = patient['_id']
    blood = mongo.db.blood_tests.insert_one(
        {"patient_id": ObjectId(patient_id), "due_date": datetime.now() - timedelta(days=1)})
    client.post(f"patient/blood-tests/done/{patient_id}/{blood.inserted_id}",
                data={'done_date': datetime.now().strftime("%d-%m-%Y")},
                follow_redirects=True)


def add_blood_test_for_yesterday_received(client, mongo):
    add_patient_over_12(client, "Dwight", "Schrute")
    patient = mongo.db.patients.find_one({'first_name': "Dwight"})
    patient_id = patient['_id']
    blood = mongo.db.blood_tests.insert_one(
        {"patient_id": ObjectId(patient_id), "due_date": datetime.now() - timedelta(days=1)})
    client.post(f"patient/blood-tests/received/{patient_id}/{blood.inserted_id}",
                data={'received_date': datetime.now().strftime("%d-%m-%Y")},
                follow_redirects=True)


#   Testing if adding a patient increases the number of patients displayed
def test_increase_patients_number(client, mongo):
    add_patient_over_12(client, "John", "Doe")
    result = client.get("/dashboard/", follow_redirects=True)
    assert b'<p class="card-text patient-count">1</p>' in result.data


#   Testing if adding a blood test for a patient increases the ratio of blood tests for current week and month
def test_ratio_undelivered_tests(client, mongo):
    add_blood_test_for_today(client, mongo)
    result = client.get("/dashboard/", follow_redirects=True)
    assert b'<span class="completed-to-requested-week">0 / 1 &nbsp</span>' in result.data
    assert b'<span class="completed-to-requested-month">0 / 1 &nbsp</span>' in result.data


#   Testing if a correct age ratio is displayed
def test_patients_age_ratio(client, mongo):
    add_patient_over_12(client, "Julia", "Doe")
    add_patient_under_12(client, "Ann", "Marie", True)
    result = client.get("/dashboard/", follow_redirects=True)
    assert b'less-than-twelve" role="progressbar" aria-valuemin="0"\n' \
           b'                             ' \
           b'aria-valuemax="100" style="width:50.0' in result.data
    assert b'over-twelve" role="progressbar" aria-valuemin="0"\n' \
           b'                             ' \
           b'aria-valuemax="100" style="width:50.0'


#   Check if only patients with blood tests that have past due date and no done date or no results scheduled are added to the table
def test_display_patients_overdue_tests(client, mongo):
    add_blood_test_for_today(client, mongo)
    add_blood_test_for_yesterday(client, mongo)
    add_blood_test_for_yesterday_completed(client, mongo)
    add_blood_test_for_yesterday_received(client, mongo)
    result = client.get("/dashboard/table/overdue", follow_redirects=True)
    print(result.data)
    assert b'Pam' in result.data
    assert b'Jim' not in result.data
    assert b'Dwight' not in result.data
    assert b'John' not in result.data


#   Check if only patients with blood tests that have past due date and no results scheduled are added to the table
def test_display_patients_missing_tests(client, mongo):
    add_blood_test_for_today(client, mongo)
    add_blood_test_for_yesterday(client, mongo)
    add_blood_test_for_yesterday_completed(client, mongo)
    add_blood_test_for_yesterday_received(client, mongo)
    result = client.get("/dashboard/table/missing", follow_redirects=True)
    print(result.data)
    assert b'Pam' in result.data
    assert b'Jim' in result.data
    assert b'Dwight' not in result.data
    assert b'John' not in result.data

#   Check if only patients with blood tests that have past due date and no results scheduled are added to the table
def test_display_patients_no_upcoming_tests(client, mongo):
    add_patient_over_12(client, "Angela", "Martin")  # - yes
    add_blood_test_for_today(client, mongo) #john - not
    add_blood_test_for_yesterday_received(client, mongo) #dwight - yes
    result = client.get("/dashboard/table/no_upcoming", follow_redirects=True)
    print(result.data)
    assert b'Angela' in result.data
    assert b'Dwight' in result.data
    assert b'John' not in result.data
