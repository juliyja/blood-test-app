import os

SECRET_KEY = 'dev-key'

DEBUG = True
MONGO_URI = os.environ['MONGODB_URI']
MONGO_CONNECT = False
