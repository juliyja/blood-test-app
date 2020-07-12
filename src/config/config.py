import os

SECRET = os.urandom(24)

SECRET_KEY = os.environ.get('SECRET_KEY', SECRET)
MONGO_URI = os.environ['MONGODB_URI']
MONGO_CONNECT = False
REMEMBER_COOKIE_DURATION=10