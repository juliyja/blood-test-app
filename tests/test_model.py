from model import *


# Test creating a user in the model
def test_create_user():
    user = User(0, "Sofie", u"Stubø", "robert.cook@kcl.ac.uk")

    assert user.get_id() == 0





