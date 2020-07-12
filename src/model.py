import flask_login
from bson import ObjectId
from flask_pymongo import PyMongo

mongo = PyMongo()
login_manager = flask_login.LoginManager()


class User(flask_login.UserMixin):

    def __init__(self, id, name, surname, email):
        self.id = id
        self.name = name
        self.surname = surname
        self.email = email

    def get_id(self):
        return self.id


@login_manager.user_loader
def user_loader(id):
    result = mongo.db.users.find_one({'_id': ObjectId(id)})

    if result:
        user = User(str(result['_id']), result['first_name'], result['last_name'], result['email'])
        return user

