#   Adds a new hospital to the database (used in test methods)
def add_hospital(client, institution_name, number="123", phone="0745728899"):
    location = "Denmark Hill"
    email = "email@kch.uk"
    postcode = "SE1 6HH"

    return client.post('/hospital/add', data={'institution_name': institution_name,
                                              'hospital_number': number,
                                              'phone': phone,
                                              'location': location,
                                              'email': email,
                                              'postcode': postcode}, follow_redirects=True)


#   Tests adding a new hospital to the database
def test_add_hospital(client, mongo):
    r = add_hospital(client, "Kings College Hospital", "1123")
    result = mongo.db.hospitals.find_one({'name': "Kings College Hospital"})
    assert b"Hospital updated successfully" in r.data
    assert result['hospital_number'] == "1123"
    assert result['phone'] == "0745728899"
    assert result['location'] == "Denmark Hill"
    assert result['email'] == 'email@kch.uk'
    assert result['postcode'] == "SE1 6HH"


#   Tests adding and displaying a new hospital
def test_modify_hospital_get_method(client, mongo):
    add_hospital(client, "St. Georges Hospital", "1435")
    hospital = mongo.db.hospitals.find_one({'name': "St. Georges Hospital"})
    hospital_id = hospital['_id']
    r = client.get(f'/hospital/{hospital_id}', follow_redirects=True)
    assert b"St. Georges Hospital" in r.data


#   Tests modify.html with no hospital id sent - it becomes add instead of update
def test_add_hospital_get_method_no_id(client, mongo):
    client.get("hospital/add")


#   Tests if added hospitals are displayed in a table
def test_get_all(client, mongo):
    add_hospital(client, "Greys Anatomy", "911")
    add_hospital(client, "Chelsea Hospital", "523")
    add_hospital(client, "Borough Hospital", "593")
    add_hospital(client, "Southwark Hospital", "503")

    r = client.get('hospital/', follow_redirects=True)

    assert b"Greys Anatomy" in r.data
    assert b"Chelsea Hospital" in r.data
    assert b"Borough Hospital" in r.data
    assert b"Southwark Hospital" in r.data


#   Tests sorting hospitals by name
def test_get_all_sorted_by_name(client, mongo):
    add_hospital(client, "Greys Anatomy", "911")
    add_hospital(client, "Chelsea Hospital", "523")
    add_hospital(client, "Borough Hospital", "593")
    add_hospital(client, "Southwark Hospital", "503")

    r = client.get('hospital/sort/desc/name', follow_redirects=True)
    assert r.data.find(b"Borough Hospital") < r.data.find(b"Chelsea Hospital") < r.data.find(
        b"Greys Anatomy") < r.data.find(b"Southwark Hospital")


#   Tests sorting hospitals by hospital number
def test_get_all_sorted_by_number(client, mongo):
    add_hospital(client, "Greys Anatomy", "911")
    add_hospital(client, "Chelsea Hospital", "523")
    add_hospital(client, "Borough Hospital", "593")
    add_hospital(client, "Southwark Hospital", "503")

    r = client.get('hospital/sort/desc/hospital_number', follow_redirects=True)

    assert r.data.find(b"Southwark Hospital") < r.data.find(b"Chelsea Hospital") < r.data.find(
        b"Borough Hospital") < r.data.find(b"Greys Anatomy")


#   Tests if sorting hospitals by no value changes anything - it shouldn't
def test_get_all_sorted_with_no_value(client, mongo):
    add_hospital(client, "Greys Anatomy", "911")
    add_hospital(client, "Chelsea Hospital", "523")
    add_hospital(client, "Borough Hospital", "593")
    add_hospital(client, "Southwark Hospital", "503")

    r = client.get('hospital/sort/asc/test', follow_redirects=True)

    assert r.data.find(b"Greys Anatomy") < r.data.find(b"Chelsea Hospital") < r.data.find(
        b"Borough Hospital") < r.data.find(b"Southwark Hospital")


#   Tests searching
def test_get_all_search(client, mongo):
    add_hospital(client, "Greys Anatomy", "911")
    add_hospital(client, "Chelsea Hospital", "523")
    add_hospital(client, "Borough Hospital", "593")
    add_hospital(client, "Southwark Hospital", "503")
    r = client.get('hospital/search', query_string={'search': 'Greys Anatomy'}, follow_redirects=True)

    assert b'Greys Anatomy' in r.data
    assert b'Chelsea Hospital' not in r.data
    assert b'Borough Hospital' not in r.data
    assert b'Southwark Hospital' not in r.data


#   Tests deleting a hospital
def test_delete(client, mongo):
    add_hospital(client, "Greys Anatomy", "911")

    hospital = mongo.db.hospitals.find_one({'name': "Greys Anatomy"})
    hospital_id = hospital['_id']

    r = client.get(f'hospital/delete/{hospital_id}', follow_redirects=True)

    assert b"The institution was deleted" in r.data
    result = mongo.db.hospitals.find_one({'name': "Greys Anatomy"})
    assert not result
