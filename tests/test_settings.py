# Test editing the template message to patients
def test_template_edit(auth, mongo):
    mongo.db.settings.insert_one({'name': 'notifications'})
    r = auth['client'].post('/settings/patient', data={'email_editor_patient': 'Test template message',
                                                       'SMS_editor_patient': 'Test template message'},
                            follow_redirects=True)
    assert b'Messages were updated' in r.data
    # check if values were saved correctly
    templates = mongo.db.settings.find_one({'name': 'notifications'})['templates']
    assert templates['patient'].get('email') == 'Test template message'
    assert templates['patient'].get('text') == 'Test template message '


# Test editing the template message to hospitals
def test_template_edit_hospital(auth, mongo):
    mongo.db.settings.insert_one({'name': 'notifications'})
    r = auth['client'].post('/settings/hospital', data={'email_editor_hospital': 'Test template message',
                                                        'SMS_editor_hospital': 'Test template message'},
                            follow_redirects=True)
    assert b'Messages were updated' in r.data
    # check if values were saved correctly
    templates = mongo.db.settings.find_one({'name': 'notifications'})['templates']
    assert templates['hospital'].get('email') == 'Test template message'
    assert templates['hospital'].get('text') == 'Test template message '
