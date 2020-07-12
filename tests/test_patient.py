from datetime import datetime
from views.patient.controller import get_age

from bson import ObjectId


# Helper function for test_patient
# Adds a patient under 16 to the database
def add_patient_under_16(client, first_name, last_name, carer_info=True, date_of_birth="11-03-2004"):
    sex = "Female"
    first_blood_test = "07-03-2019"
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
                                                 'first_blood_test': first_blood_test,
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
                                                 'first_blood_test': first_blood_test,
                                                 'hospital_number': hospital_number}, follow_redirects=True)

# Helper function for test_patient
# Adds a patient over 16
def add_patient_over_16(client, first_name, last_name, date_of_birth="11-03-2000", is_high_risk=False):
    sex = "Female"
    first_blood_test = "07-03-2019"
    hospital_number = "123"
    phone_number = "123123123"
    email = "sofie@sofie.com"

    return client.post("/patient/add", data={'first_name': first_name,
                                             'last_name': last_name,
                                             'sex': sex,
                                             'date_of_birth': date_of_birth,
                                             'hospital_number': hospital_number,
                                             'phone_number': phone_number,
                                             'email': email,
                                             'is_high_risk': is_high_risk}, follow_redirects=True)


#   Tests if adding a patient adds the patient to the patient collection, a new bloodtest to the bloodtest collection
#   and that the user has been notified that the patient was added.
def test_adding_patient(client, mongo):
    r = add_patient_over_16(client, "Bob", "Frupert")
    assert b'Patient added successfully' in r.data
    result = mongo.db.patients.find_one({'first_name': "Bob"})
    assert result['first_name'] == "Bob"
    assert result['last_name'] == "Frupert"
    assert result['sex'] == "Female"
    assert result['phone_number'] == '123123123'
    assert result['email'] == 'sofie@sofie.com'
    assert result['date_of_birth'] == datetime.strptime('11-03-2000', "%d-%m-%Y")
    assert result['hospital_number'] == '123'


#   Testing if adding a patient without a name will not add the patient to the database and notify the user that they
#   need to fill in required fields
def test_adding_incomplete_patient(client, mongo):
    r = add_patient_over_16(client, "", "Fred")
    assert b'Fill in all of the required fields' in r.data
    assert b'Fred' in r.data

    result = mongo.db.patients.find_one({'last_name': "Fred"})
    assert not result


#   Testing if adding a patient through the client stores the correct information in the patient collection.
def test_adding_underage_patient(client, mongo):
    r = add_patient_under_16(client, "Sofie", "Stuboe", True)
    assert b'Patient added successfully' in r.data

    result = mongo.db.patients.find_one({'first_name': "Sofie"})
    assert result['sex'] == "Female"
    assert result['first_name'] == "Sofie"
    assert result['last_name'] == "Stuboe"
    assert result['sex'] == "Female"
    assert result['date_of_birth'] == datetime.strptime("11-03-2004", "%d-%m-%Y")
    assert result['hospital_number'] == "123"

    carer = result['carer']
    assert carer['name'] == "Erik"
    assert carer['last_name'] == "Stuboe"
    assert carer['phone_number'] == "1231231231"
    assert carer['email'] == "erik@erik.com"


# Test adding an underage patient without their carer info
def test_adding_incomplete_underage_patient(client, mongo):
    r = add_patient_under_16(client, "Gert", "Ruth", False)
    assert b'The patient is under 16 so the details of their carer are required' in r.data
    assert b'Gert' in r.data
    assert b'Ruth' in r.data
    result = mongo.db.patients.find_one({'first_name': "Gert"})
    assert not result


# Test adding a high risk patient
def test_adding_high_risk_patient(client, mongo):
    r = add_patient_over_16(client, "Gert", "Ruth", "11-03-1997", True)
    assert b'<span class="badge badge-danger">R</span>' in r.data
    result = mongo.db.patients.find_one({'first_name': "Gert"})
    assert result['is_high_risk'] == True


# Test deleting a patient
def test_deleting_patient(client, mongo):
    add_patient_over_16(client, "Sofie", "Stuboe")
    patient = mongo.db.patients.find_one({'first_name': "Sofie"})
    patient_id = patient['_id']

    r = client.get(f"/patient/delete/{patient_id}", follow_redirects=True)
    result = mongo.db.patients.find_one({'first_name': "Sofie"})
    assert not result
    assert b'The patient was deleted' in r.data


# Test changing an existing patient
def test_modify_patient_post_method(client, mongo):
    add_patient_over_16(client, "Sofhie", "Prubote")
    patient = mongo.db.patients.find_one({'first_name': "Sofhie"})
    patient_id = patient['_id']
    r = client.post(f"/patient/{patient_id}", data={'first_name': "Sofhie",
                                                    'last_name': "Prubert",
                                                    'sex': "Female",
                                                    'date_of_birth': "11-03-1997",
                                                    'first_blood_test': "12-03-2018",
                                                    'hospital_number': "123",
                                                    'phone_number': "345654333",
                                                    'email': "msws@mded.com"}, follow_redirects=True)
    assert b'Patient updated successfully' in r.data
    assert b'Sofhie' in r.data
    result = mongo.db.patients.find_one({'first_name': "Sofhie"})
    assert result['last_name'] == "Prubert"


# Test retrieving a patient's information when editing an existing patient
def test_modify_patient_get_method(client, mongo):
    add_patient_over_16(client, "Rupert", "Klong")
    patient = mongo.db.patients.find_one({'first_name': "Rupert"})
    patient_id = patient['_id']
    r = client.get(f"/patient/{patient_id}")
    assert b'Rupert' in r.data


# Test retrieving a patient without an id
def test_modify_patient_get_method_no_id(client, mongo):
    client.get("patient/add")


# Test scheduling a new blood test for a patient
def test_get_blood_tests(client, mongo):
    add_patient_over_16(client, "Marta", "Krawzcyk")
    patient = mongo.db.patients.find_one({'first_name': "Marta"})
    patient_id = patient['_id']
    r = client.post(f"/patient/blood_tests/{patient_id}/", data={'next_date': "28-03-2019"},
                    follow_redirects=True)
    assert b'28-03-2019' in r.data


# Test marking a blood test as done with the blood id
def test_mark_done_with_blood_id(client, mongo):
    add_patient_over_16(client, "Marta", "Krawcyk")
    patient = mongo.db.patients.find_one({'first_name': "Marta"})
    patient_id = patient['_id']
    blood = mongo.db.blood_tests.insert_one({"patient_id": ObjectId(patient_id), "due_date": datetime(2019, 3, 30)})
    r = client.post(f"patient/blood-tests/done/{patient_id}/{blood.inserted_id}", data={'done_date': "30-03-2019"},
                    follow_redirects=True)
    assert b'30-03-2019' in r.data


# Test marking a blood test as done without the blood id
def test_mark_done_without_blood_id(client, mongo):
    add_patient_over_16(client, "Marta", "Krawcyk")
    patient = mongo.db.patients.find_one({'first_name': "Marta"})
    patient_id = patient['_id']
    r = client.post(f"patient/blood-tests/done/{patient_id}/", follow_redirects=True)
    assert b'Missing blood test' in r.data


# Test marking a blood test as reviwed with the blood id
def test_mark_reviewed_with_blood_id(client, mongo):
    add_patient_over_16(client, "Marta", "Krawcyk")
    patient = mongo.db.patients.find_one({'first_name': "Marta"})
    patient_id = patient['_id']
    mongo.db.blood_tests.insert_one({"row_id": ObjectId(patient_id), "due_date": datetime(2019, 3, 30), "received_date": datetime(2019, 3, 30)})
    blood = mongo.db.blood_tests.find_one({"row_id": ObjectId(patient_id)})
    blood_id = blood['_id']
    client.post(f"patient/blood-tests/reviewed/{patient_id}/{ObjectId(blood_id)}",
                    follow_redirects=True)
    result = mongo.db.blood_tests.find_one({'_id': blood_id}, {'reviewed': 'True'})
    assert result


# Test marking a blood test as results_received with the blood_id
def test_mark_received_with_blood_id(client, mongo):
    add_patient_over_16(client, "Marta", "Krawcyk")
    patient = mongo.db.patients.find_one({'first_name': "Marta"})
    patient_id = patient['_id']
    blood = mongo.db.blood_tests.insert_one({"patient_id": ObjectId(patient_id), "due_date": datetime(2019, 3, 30)})
    client.post(f"/patient/blood_tests/{patient_id}/", data={'next_date': "28-03-2019"},
                follow_redirects=True)
    r = client.post(f"patient/blood-tests/received/{patient_id}/{blood.inserted_id}",
                    data={'received_date': "01-04-2019"},
                    follow_redirects=True)
    assert b'01' in r.data
    # assert b'04' in r.data
    assert b'2019' in r.data


# Test marking a blood test as results_received without the blood_id
def test_mark_received_without_blood_id(client, mongo):
    add_patient_over_16(client, "Marta", "Krawcyk")
    patient = mongo.db.patients.find_one({'first_name': "Marta"})
    patient_id = patient['_id']
    r = client.post(f"patient/blood-tests/received/{patient_id}/", follow_redirects=True)
    assert b'Missing blood test' in r.data


# Test sorting patients in the table by first name
def test_get_all_sorted_by_first_name_d(client, mongo):
    add_patient_over_16(client, "Sofie", "Stubo", "11-03-1997")
    add_patient_over_16(client, "Karolina", "Szafranek", "03-03-1998")
    add_patient_over_16(client, "Seweryn", "Chlewenicki", "04-07-1998")
    add_patient_over_16(client, "Julia", "Jakuba", "23-08-1998")
    add_patient_over_16(client, "Szymon", "Sudol", "24-12-1998")
    r = client.get('patient/sort/desc/first_name', follow_redirects=True)

    assert r.data.find(b"Julia") < r.data.find(b"Karolina") \
           < r.data.find(b"Seweryn") < r.data.find(b"Sofie") < r.data.find(b"Szymon")


# Test sorting patients in the table by last name
def test_get_all_sorted_by_last_name_desc(client, mongo):
    add_patient_over_16(client, "Marta", "Krawcyk", "13-02-1998")
    add_patient_over_16(client, "Karolina", "Szafranek", "03-03-1998")
    add_patient_over_16(client, "Seweryn", "Chlewenicki", "04-07-1998")
    add_patient_over_16(client, "Julia", "Jakuba", "23-08-1998")
    add_patient_over_16(client, "Szymon", "Sudol", "24-12-1998")
    r = client.get('patient/sort/desc/last_name', follow_redirects=True)

    assert r.data.find(b"Seweryn") < r.data.find(b"Julia") < r.data.find(b"Marta") \
           < r.data.find(b"Szymon") < r.data.find(b"Karolina")


# Test sorting patients in the table by date of birth
def test_get_all_sorted_by_date_of_birth(client, mongo):
    add_patient_over_16(client, "Sofie", "Stubo", "11-03-1997")
    add_patient_over_16(client, "Marta", "Krawcyk", "13-02-1998")
    add_patient_over_16(client, "Karolina", "Szafranek", "03-03-1998")
    add_patient_over_16(client, "Michal", "Juras", "17-05-1998")
    add_patient_over_16(client, "Seweryn", "Chlewenicki", "04-07-1998")
    r = client.get('patient/sort/asc/date_of_birth', follow_redirects=True)

    assert r.data.find(b"Seweryn") < r.data.find(b"Michal") < \
           r.data.find(b"Karolina") < r.data.find(b"Marta") < r.data.find(b"Sofie")


# Test sorting patients in the table by no value
def test_get_all_sorted_with_no_value(client, mongo):
    add_patient_over_16(client, "Sofie", "Stubo", "11-03-1997")
    add_patient_over_16(client, "Marta", "Krawcyk", "13-02-1998")
    add_patient_over_16(client, "Karolina", "Szafranek", "03-03-1998")
    add_patient_over_16(client, "Michal", "Juras", "17-05-1998")
    add_patient_over_16(client, "Seweryn", "Chlewenicki", "04-07-1998")
    r = client.get('patient/sort/asc/test', follow_redirects=True)

    assert r.data.find(b"Sofie") < r.data.find(b"Marta") < r.data.find(b"Karolina") < r.data.find(b"Michal") < \
           r.data.find(b"Seweryn")


# Test using the All filter of the dropdown menu
def test_get_all_search(client, mongo):
    add_patient_over_16(client, "Sofie", "Stubo", "11-03-1997")
    add_patient_over_16(client, "Marta", "Krawcyk", "13-02-1998")
    add_patient_over_16(client, "Karolina", "Szafranek", "03-03-1998")
    add_patient_over_16(client, "Michal", "Juras", "17-05-1998")
    add_patient_over_16(client, "Seweryn", "Chlewenicki", "04-07-1998")
    add_patient_over_16(client, "Julia", "Jakuba", "23-08-1998")
    add_patient_over_16(client, "Szymon", "Sudol", "24-12-1998")
    r = client.get('patient/search', query_string={'search': 'Karolina'}, follow_redirects=True)

    assert b'Karolina' in r.data
    assert b'Sofie' not in r.data
    assert b'Marta' not in r.data
    assert b'Michal' not in r.data
    assert b'Seweryn' not in r.data
    assert b'Julia' not in r.data
    assert b'Szymon' not in r.data


# Test using the 'under 12' filter of the dropdown menu
def test_get_all_under_12(client, mongo):
    add_patient_under_16(client, "Sofie", "Stubo", True, "20-12-2010")
    add_patient_under_16(client, "Marta", "Krawcyk", True, "10-10-2010")
    add_patient_over_16(client, "Karolina", "Szafranek", "03-03-1998")
    add_patient_over_16(client, "Michal", "Juras", "17-05-1998")
    r = client.get('patient/search', query_string={'age': 'under 12'}, follow_redirects=True)

    assert b'Sofie' in r.data
    assert b'Marta' in r.data
    assert b'Karolina' not in r.data
    assert b'Michal' not in r.data


# Test using the 'over 12' filter of the dropdown menu
def test_get_all_over_12(client, mongo):
    add_patient_under_16(client, "Sofie", "Stubo", True, "20-12-2010")
    add_patient_under_16(client, "Marta", "Krawcyk", True, "10-10-2010")
    add_patient_over_16(client, "Karolina", "Szafranek", "03-03-1998")
    add_patient_over_16(client, "Michal", "Juras", "17-05-1998")
    r = client.get('patient/search', query_string={'age': '12 and over'}, follow_redirects=True)

    assert b'Sofie' not in r.data
    assert b'Marta' not in r.data
    assert b'Karolina' in r.data
    assert b'Michal' in r.data


# Test calculating the age of a patient
def test_get_age(client, mongo):
    add_patient_over_16(client, "Sofie", "Stubo", "11-03-1997")
    assert 22 == get_age(datetime.strptime("11-03-1997", "%d-%m-%Y"))

def test_time_to_string(client, mongo):
    add_patient_over_16(client, "Sofie", "Stubo", "11-03-1997")

